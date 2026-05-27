"""
JWT Authentication Middleware
"""

import time
from functools import wraps

import bcrypt
import jwt
from config import Config
from flask import g, jsonify, request


def generate_token(user_id: str, email: str) -> str:
    """Generate a JWT token for a user."""
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + (Config.JWT_EXPIRATION_HOURS * 3600),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def require_auth(f):
    """Decorator to require authentication on a route."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return (
                jsonify({"success": False, "error": "Authorization header required"}),
                401,
            )

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if "error" in payload:
            return jsonify({"success": False, "error": payload["error"]}), 401

        g.user_id = payload.get("user_id")
        g.user_email = payload.get("email")
        return f(*args, **kwargs)

    return decorated


def optional_auth(f):
    """Decorator that optionally extracts user info but doesn't require it."""

    @wraps(f)
    def decorated(*args, **kwargs):
        g.user_id = None
        g.user_email = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if "error" not in payload:
                g.user_id = payload.get("user_id")
                g.user_email = payload.get("email")
        return f(*args, **kwargs)

    return decorated
