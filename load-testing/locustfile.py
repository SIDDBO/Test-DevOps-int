from locust import HttpUser, task, between
import random
import json

class TaskUser(HttpUser):
    """Simulates user behavior on the task app"""
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts"""
        self.task_ids = []
        self.get_tasks()

    @task(3)
    def get_tasks(self):
        """Get all tasks (higher weight)"""
        response = self.client.get(
            "/api/tasks",
            headers={"User-Agent": "Locust/LoadTest"}
        )
        if response.status_code == 200:
            self.task_ids = [t['id'] for t in response.json()]

    @task(1)
    def create_task(self):
        """Create a new task"""
        task_title = f"Task {random.randint(1000, 9999)}"
        response = self.client.post(
            "/api/tasks",
            json={"title": task_title, "description": "Auto-generated task"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 201:
            task_data = response.json()
            self.task_ids.append(task_data['id'])

    @task(1)
    def complete_task(self):
        """Mark a task as complete"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            self.client.put(
                f"/api/tasks/{task_id}",
                json={"completed": True},
                headers={"Content-Type": "application/json"}
            )

    @task(1)
    def delete_task(self):
        """Delete a task"""
        if self.task_ids and len(self.task_ids) > 2:
            task_id = random.choice(self.task_ids)
            response = self.client.delete(f"/api/tasks/{task_id}")
            if response.status_code == 200:
                self.task_ids.remove(task_id)

    @task(2)
    def health_check(self):
        """Check health endpoint"""
        self.client.get("/health")

    @task(1)
    def get_metrics(self):
        """Get Prometheus metrics"""
        self.client.get("/metrics")
