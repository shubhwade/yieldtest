"""Auth routes — register, login, get current user."""

import re
import time

from database.mongo import get_db
from flask import Blueprint, g, jsonify, request
from middleware.auth import generate_token, hash_password, require_auth, verify_password


def _to_oid(id_str):
    try:
        from bson import ObjectId

        return ObjectId(id_str)
    except Exception:
        return id_str


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "")
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"success": False, "error": "Invalid email format"}), 400
    if len(password) < 6:
        return (
            jsonify(
                {"success": False, "error": "Password must be at least 6 characters"}
            ),
            400,
        )

    db = get_db()
    if db["users"].find_one({"email": email}):
        return jsonify({"success": False, "error": "Email already registered"}), 409

    user = {
        "email": email,
        "name": name or email.split("@")[0],
        "password_hash": hash_password(password),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "settings": {"theme": "dark", "default_currency": "USD", "tax_bracket": 0.32},
    }
    result = db["users"].insert_one(user)
    token = generate_token(str(result.inserted_id), email)
    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "token": token,
                    "user": {
                        "id": str(result.inserted_id),
                        "email": email,
                        "name": user["name"],
                    },
                },
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    db = get_db()
    user = db["users"].find_one({"email": email})
    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    if not verify_password(password, user.get("password_hash", "")):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    token = generate_token(str(user["_id"]), email)
    return jsonify(
        {
            "success": True,
            "data": {
                "token": token,
                "user": {
                    "id": str(user["_id"]),
                    "email": email,
                    "name": user.get("name", ""),
                },
            },
        }
    )


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    db = get_db()
    user = db["users"].find_one({"_id": g.user_id})
    if not user:
        user = db["users"].find_one({"_id": _to_oid(g.user_id)})
    if not user:
        user = db["users"].find_one({"email": g.user_email})
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify(
        {
            "success": True,
            "data": {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "name": user.get("name"),
                "settings": user.get("settings", {}),
            },
        }
    )
