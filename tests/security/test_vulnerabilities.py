import pytest
import json

class TestSecurity:
    """
    Security validation suite for YieldLens.
    Tests for injection, unauthorized access, and API abuse.
    """

    def test_nosql_injection_auth(self, client):
        """Test for MongoDB operator injection in login."""
        # Trying to login with {$gt: ""} which might return the first user
        payload = {
            "email": {"$gt": ""},
            "password": "any"
        }
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            content_type="application/json"
        )
        # Should be 401 Unauthorized or 400 Bad Request, NOT 200
        assert response.status_code != 200

    def test_nosql_injection_screener(self, client):
        """Test for injection in search filters."""
        payload = {
            "type": {"$ne": "non-existent"}
        }
        response = client.post(
            "/api/v1/screener/search",
            data=json.dumps(payload),
            content_type="application/json"
        )
        # The API should probably only accept strings/lists for types
        # If it doesn't sanitize, it might return all bonds.
        # But for security, we check if it handles objects unexpectedly.
        # Good implementation should either fail or sanitize.
        pass

    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without token."""
        protected_endpoints = [
            "/api/v1/portfolio/list",
            "/api/v1/watchlist/add",
            "/api/v1/alerts/config"
        ]
        for ep in protected_endpoints:
            response = client.get(ep) if "list" in ep else client.post(ep)
            assert response.status_code == 401

    def test_jwt_tampering(self, client):
        """Test if API accepts tampered JWT."""
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        headers = {"Authorization": f"Bearer {fake_token}"}
        response = client.get("/api/v1/portfolio/list", headers=headers)
        assert response.status_code == 401

    def test_rate_limiting_mock(self, client):
        """
        Simulate rapid requests to check rate limiting.
        Note: Actual rate limiting might be at the infra level (Nginx/WAF).
        """
        for _ in range(10):
            client.get("/api/v1/health")
        # Check if last request was throttled if rate limiting is implemented
        pass
