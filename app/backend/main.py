#!/usr/bin/env python3
"""
Flask Backend API - Task Management Application
Includes CloudWatch custom metrics for observability
"""

import os
import json
import logging
import time
from datetime import datetime
from functools import wraps

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry
from prometheus_client import start_http_server

# ============================================================================
# Logging Configuration (Structured JSON)
# ============================================================================

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'path': record.pathname,
            'line': record.lineno,
        }
        return json.dumps(log_data)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# ============================================================================
# Flask App Initialization
# ============================================================================

app = Flask(__name__)
CORS(app)

# ============================================================================
# Prometheus Metrics
# ============================================================================

registry = CollectorRegistry()

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    registry=registry
)

# ============================================================================
# Secrets Manager Client
# ============================================================================

class SecretsManager:
    def __init__(self):
        try:
            self.client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            self.enabled = True
            logger.info("AWS Secrets Manager enabled")
        except Exception as e:
            self.enabled = False
            logger.warning(f"Secrets Manager disabled: {str(e)}")

    def get_secret(self, secret_name):
        if not self.enabled:
            return os.getenv(secret_name)

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
                return secret.get(secret_name, os.getenv(secret_name))
            return os.getenv(secret_name)
        except Exception as e:
            logger.warning(f"Failed to get secret {secret_name}, using env var: {str(e)}")
            return os.getenv(secret_name)

secrets_manager = SecretsManager()

# ============================================================================
# CloudWatch Metrics Client
# ============================================================================

class CloudWatchMetrics:
    def __init__(self, namespace='TaskApp'):
        self.namespace = namespace
        try:
            self.client = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            self.enabled = True
            logger.info(f"CloudWatch metrics enabled for namespace: {self.namespace}")
        except Exception as e:
            self.enabled = False
            logger.warning(f"CloudWatch metrics disabled: {str(e)}")

    def put_metric(self, metric_name, value, unit='None', dimensions=None):
        if not self.enabled:
            return

        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }

            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': str(v)} for k, v in dimensions.items()
                ]

            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            logger.error(f"Error putting metric {metric_name}: {str(e)}")

cw_metrics = CloudWatchMetrics()

# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection():
    """Establish database connection with retry logic"""
    max_retries = 3
    retry_delay = 2

    # Get credentials from Secrets Manager (fallback to env vars)
    db_user = secrets_manager.get_secret('db-user') or os.getenv('DB_USER', 'taskuser')
    db_password = secrets_manager.get_secret('db-password') or os.getenv('DB_PASSWORD', 'taskpass')

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'taskdb'),
                user=db_user,
                password=db_password,
                connect_timeout=5
            )
            logger.info("Database connected successfully")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                raise

def initialize_db():
    """Initialize database schema"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# ============================================================================
# Middleware for Metrics
# ============================================================================

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time

        # Prometheus metrics
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)

        http_requests_total.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()

        # CloudWatch metrics (sample: only track GET requests to reduce API calls)
        if request.method == 'GET':
            cw_metrics.put_metric(
                'APIRequestDuration',
                duration * 1000,  # Convert to milliseconds
                unit='Milliseconds',
                dimensions={'Endpoint': request.endpoint or 'unknown'}
            )

        # Log on errors
        if response.status_code >= 400:
            logger.warning(f"{request.method} {request.path} {response.status_code} ({duration:.3f}s)")
            cw_metrics.put_metric(
                'APIErrors',
                1,
                unit='Count',
                dimensions={
                    'Endpoint': request.endpoint or 'unknown',
                    'Status': str(response.status_code)
                }
            )

    return response

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()

        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        cw_metrics.put_metric('HealthCheckFailures', 1, unit='Count')
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

# ============================================================================
# Metrics Endpoint
# ============================================================================

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(registry), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ============================================================================
# Task API Endpoints
# ============================================================================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        start = time.time()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        tasks = cur.fetchall()

        duration = time.time() - start
        db_query_duration_seconds.labels(query_type='SELECT').observe(duration)

        cur.close()
        conn.close()

        logger.info(f"Retrieved {len(tasks)} tasks ({duration:.3f}s)")
        return jsonify([dict(task) for task in tasks]), 200

    except Exception as e:
        logger.error(f"Get tasks error: {str(e)}")
        cw_metrics.put_metric('GetTasksErrors', 1, unit='Count')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()

        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400

        title = data.get('title')
        description = data.get('description', '')

        start = time.time()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            '''
            INSERT INTO tasks (title, description)
            VALUES (%s, %s)
            RETURNING *
            ''',
            (title, description)
        )

        new_task = cur.fetchone()
        conn.commit()

        duration = time.time() - start
        db_query_duration_seconds.labels(query_type='INSERT').observe(duration)

        cur.close()
        conn.close()

        logger.info(f"Created task: {new_task['id']} ({duration:.3f}s)")
        cw_metrics.put_metric('TasksCreated', 1, unit='Count')

        return jsonify(dict(new_task)), 201

    except Exception as e:
        logger.error(f"Create task error: {str(e)}")
        cw_metrics.put_metric('CreateTaskErrors', 1, unit='Count')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    try:
        start = time.time()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
        task = cur.fetchone()

        duration = time.time() - start
        db_query_duration_seconds.labels(query_type='SELECT').observe(duration)

        cur.close()
        conn.close()

        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(dict(task)), 200

    except Exception as e:
        logger.error(f"Get task error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        data = request.get_json()

        start = time.time()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic update query
        updates = []
        values = []

        if 'title' in data:
            updates.append('title = %s')
            values.append(data['title'])

        if 'description' in data:
            updates.append('description = %s')
            values.append(data['description'])

        if 'completed' in data:
            updates.append('completed = %s')
            values.append(data['completed'])

        if not updates:
            return jsonify({'error': 'No fields to update'}), 400

        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(task_id)

        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s RETURNING *"
        cur.execute(query, values)
        updated_task = cur.fetchone()
        conn.commit()

        duration = time.time() - start
        db_query_duration_seconds.labels(query_type='UPDATE').observe(duration)

        cur.close()
        conn.close()

        if not updated_task:
            return jsonify({'error': 'Task not found'}), 404

        logger.info(f"Updated task: {task_id} ({duration:.3f}s)")
        cw_metrics.put_metric('TasksUpdated', 1, unit='Count')

        return jsonify(dict(updated_task)), 200

    except Exception as e:
        logger.error(f"Update task error: {str(e)}")
        cw_metrics.put_metric('UpdateTaskErrors', 1, unit='Count')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    try:
        start = time.time()
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('DELETE FROM tasks WHERE id = %s RETURNING id', (task_id,))
        deleted = cur.fetchone()
        conn.commit()

        duration = time.time() - start
        db_query_duration_seconds.labels(query_type='DELETE').observe(duration)

        cur.close()
        conn.close()

        if not deleted:
            return jsonify({'error': 'Task not found'}), 404

        logger.info(f"Deleted task: {task_id} ({duration:.3f}s)")
        cw_metrics.put_metric('TasksDeleted', 1, unit='Count')

        return '', 204

    except Exception as e:
        logger.error(f"Delete task error: {str(e)}")
        cw_metrics.put_metric('DeleteTaskErrors', 1, unit='Count')
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error: {str(error)}")
    cw_metrics.put_metric('InternalServerErrors', 1, unit='Count')
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# Application Startup
# ============================================================================

if __name__ == '__main__':
    try:
        environment = os.getenv('ENVIRONMENT', 'dev')
        logger.info(f"Initializing application in {environment} environment...")
        initialize_db()

        # Start Prometheus metrics server on port 8000
        start_http_server(8000, registry=registry)
        logger.info("Prometheus metrics server started on port 8000")

        # Start Flask app
        logger.info("Starting Flask application...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
