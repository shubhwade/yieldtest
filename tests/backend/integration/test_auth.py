import pytest
import json

class TestAuthAPI:
    """
    Integration tests for Authentication API endpoints.
    """

    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"

    def test_user_registration(self, client):
        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password123!"
        }
        response = client.post(
            "/api/v1/auth/register",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert "token" in data["data"]

    def test_user_login(self, client, mock_db):
        # First register a user
        from bcrypt import hashpw, gensalt
        hashed_pw = hashpw("Password123!".encode('utf-8'), gensalt())
        mock_db.users.insert_one({
            "name": "Existing User",
            "email": "existing@example.com",
            "password": hashed_pw.decode('utf-8')
        })

        payload = {
            "email": "existing@example.com",
            "password": "Password123!"
        }
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "token" in data["data"]

    def test_login_invalid_credentials(self, client):
        payload = {
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["success"] is False
