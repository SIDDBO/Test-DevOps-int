# Task Management Application - SRE/DevOps Demo

A dev-ready Kubernetes cluster on AWS with full CI/CD automation, demonstrating enterprise DevOps practices.

## My DevOps Architecture

This project showcases my understanding of modern DevOps practices:

```
GitHub Repository (Version Control)
    ↓ Webhook trigger
Jenkins Pipeline (CI/CD Automation)
    ├─ Build Docker images with multi-stage builds
    ├─ Push to Docker Hub with semantic versioning
    └─ Deploy via Helm with automatic rollback
        ↓
AWS Infrastructure (Infrastructure as Code)
    ├─ Terraform manages all AWS resources
    ├─ Free tier optimized (EC2 t3.micro)
    └─ Security groups, IAM, VPC design
        ↓
Kubernetes Cluster (Orchestration)
    ├─ Kubeadm-based cluster on EC2
    ├─ Helm charts for app packaging
    ├─ Auto-scaling based on metrics
    ├─ Health checks and graceful shutdown
    └─ PostgreSQL with persistent storage
        ↓
Observability & Monitoring
    ├─ Prometheus metrics export
    ├─ Structured JSON logging
    ├─ Health endpoints
    └─ Load testing with Locust
```

## DevOps Engineering Demonstrations

### 1. Infrastructure as Code (Terraform)
My approach to managing infrastructure:
- **Modular design**: Separate concerns (VPC, EC2, security, outputs)
- **Free tier optimization**: Cost analysis on every resource decision
- **Reproducibility**: One command to spin up entire environment
- **Security**: IAM least privilege, security group hardening, secrets management
- **Scalability**: Parameterized variables for different environments

### 2. Kubernetes Orchestration (Helm)
How I package and deploy applications:
- **Helm templating**: Separates configuration from infrastructure (values.yaml)
- **Environment management**: Dev/prod configurations with template overrides
- **Namespace segregation**: Frontend, backend, and database in separate namespaces for isolation
- **Network policies**: Zero-trust networking with pod-to-pod communication rules
- **Deployment strategy**: Rolling updates with configurable replicas
- **Health & resilience**: Liveness/readiness probes, Pod Disruption Budgets
- **Auto-scaling**: HPA with CPU/memory thresholds for handling traffic spikes
- **Storage**: PostgreSQL StatefulSet with persistent volumes
- **RBAC & Service Accounts**: Per-namespace service accounts with minimal privileges
- **Resource quotas**: CPU/memory limits per namespace to prevent resource exhaustion

### 3. CI/CD Pipeline (Jenkins)
Automation I've implemented:
- **Pipeline as Code**: Jenkinsfile defines complete workflow
- **Automated builds**: Docker image creation with semantic versioning
- **Registry management**: Pushing to Docker Hub with proper tagging
- **Deployment automation**: Helm upgrade integrated into pipeline
- **Failure handling**: Automatic rollback when deployment fails
- **Load testing**: Performance validation as part of pipeline

### 4. Observability & Monitoring
How I ensure system visibility:
- **Metrics export**: Prometheus-format metrics for monitoring
- **Structured logging**: JSON format for easy parsing and aggregation
- **Health endpoints**: /health and /metrics for K8s probes
- **Performance testing**: Locust-based load simulation
- **Auto-scaling validation**: Demonstrates HPA responding to metrics

### 5. Security & Data Handling
My approach to keeping systems secure:
- **Secrets management**: K8s Secrets for credentials, not hardcoded
- **Network security**: Security groups restricting access appropriately
- **IAM policies**: Least privilege access for AWS resources
- **Container security**: Multi-stage Docker builds, minimal images
- **Database security**: PostgreSQL authentication, isolated pods

## Quick Start

### Prerequisites

- AWS Account (with free tier eligibility)
- Terraform >= 1.0
- Docker & Docker Hub account
- Git
- Jenkins (running locally via Docker)
- kubectl
- Helm

### 1. Setup AWS Infrastructure

```bash
cd terraform

# Copy example tfvars and update with your values
cp terraform.tfvars.example terraform.tfvars

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs (EC2 IP, security group, etc.)
terraform output
```

### 2. Access the Kubernetes Cluster

```bash
# SSH into EC2 instance
ssh -i <your-key>.pem ubuntu@<instance-public-ip>

# Copy kubeconfig
scp -i <your-key>.pem ubuntu@<instance-public-ip>:/home/ubuntu/.kube/config ~/.kube/config

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### 3. Configure Jenkins

```bash
# Configure Docker credentials in Jenkins
# Add Jenkins connection to K8s cluster (kubeconfig)

# Create pipeline job
# Webhook: GitHub → Jenkins
# Pipeline: Jenkinsfile from repo
```

### 4. Deploy Application

```bash
# Via Jenkins: Push to GitHub triggers automatic deployment
git push origin main

# Or manually:
helm upgrade --install task-app-release ./helm-charts/task-app \
  --values helm-charts/task-app/values-dev.yaml
```

### 5. Access the Application

```bash
# Get frontend service address
kubectl get service task-app-release-frontend -n frontend

# Access via LoadBalancer IP or NodePort
# http://<service-ip>:<port>
```

## Kubernetes Architecture: Three-Namespace Segregation

The application is deployed across three isolated Kubernetes namespaces for security, resource management, and operational clarity:

### Namespace Design

```
Frontend Namespace
├─ Deployment: task-app-release-frontend (2-4 replicas)
├─ Service: LoadBalancer on port 80
└─ NetworkPolicy: Allow ingress from any, egress to backend:5000

Backend Namespace
├─ Deployment: task-app-release-backend (2-5 replicas)
├─ Service: ClusterIP on port 5000
├─ ConfigMap: App configuration and secrets
└─ NetworkPolicy: Allow ingress from frontend, egress to database:5432

Database Namespace
├─ StatefulSet: PostgreSQL (1 replica)
├─ Service: ClusterIP on port 5432
└─ NetworkPolicy: Allow ingress from backend only
```

### Network Policies (Zero-Trust Security)

- **Frontend → Backend**: Explicit allow via NetworkPolicy to backend:5000
- **Backend → Database**: Explicit allow via NetworkPolicy to database:5432
- **Default**: All traffic denied (deny-all policy)
- **DNS**: Egress to port 53 (TCP/UDP) for all namespaces
- **Cross-namespace**: Communication uses namespace labels and pod selectors

### Resource Quotas

Each namespace has hard limits to prevent resource exhaustion:

| Namespace | CPU Request | Memory Request |
|-----------|------------|-----------------|
| Frontend  | 100m       | 128Mi          |
| Backend   | 200m       | 256Mi          |
| Database  | 100m       | 512Mi          |

### Service Accounts & RBAC

Each namespace has a dedicated service account for least-privilege access:

```bash
# View service accounts
kubectl get serviceaccounts -n frontend
kubectl get serviceaccounts -n backend
kubectl get serviceaccounts -n database
```

### Viewing Namespace Status

```bash
# Check all namespaces
kubectl get namespaces

# View pods by namespace
kubectl get pods -n frontend
kubectl get pods -n backend
kubectl get pods -n database

# Check network policies
kubectl get networkpolicies -A

# View resource quotas
kubectl describe resourcequota -n frontend
kubectl describe resourcequota -n backend
kubectl describe resourcequota -n database
```

## Directory Structure

```
SG_demo/
├── terraform/                    # Infrastructure as Code
│   ├── main.tf                   # VPC, EC2, Security Groups
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # VPC IP, endpoints
│   ├── user_data.sh              # K8s cluster bootstrap
│   └── terraform.tfvars.example  # Configuration template
│
├── helm-charts/                  # Kubernetes application package
│   └── task-app/
│       ├── Chart.yaml            # Chart metadata
│       ├── values.yaml           # Default configuration
│       └── templates/            # Kubernetes manifests
│
├── jenkins/                      # CI/CD Pipeline
│   └── Jenkinsfile               # Pipeline definition
│
├── app/                          # Application source code
│   ├── backend/                  # Flask API
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/                 # Nginx web UI
│       ├── index.html
│       ├── nginx.conf
│       └── Dockerfile
│
├── load-testing/                 # Performance testing
│   ├── locustfile.py
│   └── requirements.txt
│
└── docs/                         # Documentation
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT_GUIDE.md
    ├── SCALING.md
    └── TROUBLESHOOTING.md
```

## Development Workflow

### Local Development

```bash
# Build Docker images locally
docker-compose -f app/docker-compose-local.yml build

# Run locally
docker-compose -f app/docker-compose-local.yml up

# Access at http://localhost:8080
```

### Testing

```bash
# Run load tests
python -m pip install locust
cd load-testing
locust -f locustfile.py --host=http://localhost:8080
```

## Deployment

### Manual Deployment

```bash
# Export kubeconfig
export KUBECONFIG=~/.kube/config

# Create namespace
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -

# Install with Helm
helm install task-app-release ./helm-charts/task-app \
  --namespace dev \
  --values helm-charts/task-app/values.yaml
```

### CI/CD Deployment

1. Push to GitHub
2. Jenkins webhook triggers
3. Build Docker images
4. Push to Docker Hub
5. Deploy via Helm
6. Verify deployment

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/task-app-release-backend -n dev

# Frontend logs
kubectl logs -f deployment/task-app-release-frontend -n dev

# PostgreSQL logs
kubectl logs -f statefulset/task-app-release-postgresql -n dev
```

### View Metrics

```bash
# Pod resource usage
kubectl top pods -n dev

# Node resource usage
kubectl top nodes

# Deployment status
kubectl describe deployment task-app-release-backend -n dev
```

### Pod Autoscaling Status

```bash
kubectl get hpa -n dev
kubectl describe hpa task-app-release-backend-hpa -n dev
```

## Scaling

### Manual Scaling

```bash
# Scale backend to 3 replicas
kubectl scale deployment task-app-release-backend -n dev --replicas=3

# View scaled deployment
kubectl get pods -n dev
```

### Auto-scaling

Auto-scaling is configured in `values.yaml`:
- Min replicas: 2
- Max replicas: 5
- Target CPU: 70%
- Target memory: 80%

Triggers when metrics exceed thresholds.

## Load Testing

```bash
# Run load test with Locust
python -m pip install locust

cd load-testing
locust -f locustfile.py \
  --host=<frontend-service-ip> \
  --headless \
  --users=50 \
  --spawn-rate=10 \
  --run-time=60s
```

## Cost Optimization

This setup is **completely free within AWS free tier**:

- ✅ EC2 t3.micro: 750 hours/month (free)
- ✅ EBS 30GB: Free tier
- ✅ Data transfer: <1GB (free)
- ✅ Elastic IP: Free (while attached)
- ❌ EKS: NOT used (would cost $0.10/hour)

**Total monthly cost: $0 (within free tier)**

## Troubleshooting

### Pod won't start

```bash
# Check pod status
kubectl describe pod <pod-name> -n dev

# View pod logs
kubectl logs <pod-name> -n dev

# Check events
kubectl get events -n dev
```

### Database connection issues

```bash
# Check PostgreSQL pod
kubectl get pods -n dev | grep postgresql

# Connect to PostgreSQL
kubectl exec -it <postgres-pod> -n dev -- psql -U taskapp -d tasks
```

### Helm deployment failed

```bash
# Check release status
helm status task-app-release -n dev

# Rollback to previous version
helm rollback task-app-release -n dev

# View release history
helm history task-app-release -n dev
```

## What I Learned & What I'd Improve

### During This Exercise

I demonstrated:
- ✅ End-to-end DevOps pipeline setup (Terraform → Kubernetes → Jenkins)
- ✅ Production-grade practices (Helm, HPA, health checks)
- ✅ Cost optimization (free tier focus)
- ✅ Observability from the start (metrics, logging, health endpoints)
- ✅ Security consideration (secrets, IAM, least privilege)
- ✅ Failure handling (auto-scaling, pod restart, rollback)

### Next Steps I'd Implement in Production

- [ ] **TLS/SSL**: Let's Encrypt certificates with cert-manager for HTTPS
- [ ] **Monitoring Dashboard**: Prometheus + Grafana for real-time visibility
- [ ] **Log Aggregation**: ELK stack or CloudWatch for centralized logs
- [ ] **Backup Strategy**: Automated PostgreSQL backups to S3
- [ ] **Network Policies**: K8s NetworkPolicy for pod-to-pod communication control
- [ ] **RBAC**: Role-based access control for K8s resources
- [ ] **CI Testing**: Unit tests, integration tests in Jenkins pipeline
- [ ] **Security Scanning**: Trivy for container image vulnerability scanning
- [ ] **Rate Limiting**: Ingress rate limiting to prevent abuse
- [ ] **Database Migrations**: Automated schema migrations in CD pipeline
- [ ] **Multi-region**: Active-active setup across AWS regions
- [ ] **Disaster Recovery**: Cross-region backup and failover procedures

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture explanation
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [SCALING.md](docs/SCALING.md) - Scaling strategies
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and fixes

## Support

For issues or questions:
1. Check TROUBLESHOOTING.md
2. Review Terraform outputs
3. Check pod logs with kubectl
4. Review Jenkins pipeline logs

## License

This is a demonstration project for learning DevOps practices.
