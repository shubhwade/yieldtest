from locust import HttpUser, task, between
import json
import random

class YieldLensUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Executed when a user starts."""
        self.login()

    def login(self):
        """Simulate user login to get a token (if needed)."""
        # For now, we skip auth if the API allows or use a mock token
        pass

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/health")
        self.client.get("/api/v1/market/summary")
        self.client.get("/api/v1/fred/yield-curve")

    @task(2)
    def search_bonds(self):
        payload = {
            "type": random.choice(["corporate", "municipal", "treasury"]),
            "limit": 20
        }
        self.client.post("/api/v1/screener/search", json=payload)

    @task(1)
    def bond_analytics(self):
        # Assuming we have some bond IDs to query
        self.client.get("/api/v1/bonds/US123456789/analytics")

    @task(1)
    def ai_query(self):
        payload = {"prompt": "Why are yields increasing?"}
        self.client.post("/api/v1/ai/query", json=payload)

class LoadTester:
    """
    Instructions for running:
    locust -f tests/performance/locustfile.py --host http://localhost:5000
    """
    pass
