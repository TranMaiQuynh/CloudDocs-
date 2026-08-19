"""
Locust Performance & Load Testing Script for CloudDocs API
Measures Concurrent Users, Request Throughput (RPS), Latency (P95/P99), Error Rates
Run with: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import uuid

class CloudDocsUser(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        """Simulate user authentication upon session start."""
        email = f"loadtest_{uuid.uuid4().hex[:6]}@example.com"
        password = "LoadTestPassword123!"

        # Register User
        with self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Locust User"
        }, catch_response=True) as reg_res:
            if reg_res.status_code in [200, 201]:
                reg_res.success()
            else:
                reg_res.failure(f"Registration failed with status {reg_res.status_code}")

        # Login User
        with self.client.post("/auth/login", json={
            "email": email,
            "password": password
        }, catch_response=True) as login_res:
            if login_res.status_code == 200:
                self.token = login_res.json().get("access_token")
                login_res.success()
            else:
                login_res.failure(f"Login failed with status {login_res.status_code}")

    @task(4)
    def fetch_workspace_documents(self):
        """Task: View workspace document list (High Frequency)."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            with self.client.get("/documents/search?q=", headers=headers, name="/documents/search", catch_response=True) as res:
                if res.status_code == 200:
                    res.success()
                else:
                    res.failure(f"Failed search with status {res.status_code}")

    @task(3)
    def fetch_storage_quota(self):
        """Task: Check storage quota."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            with self.client.get("/documents/quota", headers=headers, name="/documents/quota", catch_response=True) as res:
                if res.status_code == 200:
                    res.success()
                else:
                    res.failure(f"Failed quota with status {res.status_code}")

    @task(1)
    def fetch_activities_log(self):
        """Task: View system audit log."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            with self.client.get("/activities", headers=headers, name="/activities", catch_response=True) as res:
                if res.status_code == 200:
                    res.success()
                else:
                    res.failure(f"Failed activities with status {res.status_code}")
