"""Alerts routes — CRUD for user alerts."""

import time

from database.mongo import get_db
from flask import Blueprint, g, jsonify, request
from middleware.auth import optional_auth

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")
DEMO_USER = "demo_user_001"


def _uid():
    return getattr(g, "user_id", None) or DEMO_USER


def _to_oid(id_str):
    """Convert string to ObjectId if valid, otherwise return as-is."""
    try:
        from bson import ObjectId

        return ObjectId(id_str)
    except Exception:
        return id_str


def _find_by_id(collection, id_str):
    """Find a document by _id, trying both string and ObjectId formats."""
    doc = collection.find_one({"_id": id_str})
    if doc is None:
        doc = collection.find_one({"_id": _to_oid(id_str)})
    return doc


def _update_by_id(collection, id_str, update):
    """Update a document by _id, trying both string and ObjectId formats."""
    result = collection.update_one({"_id": id_str}, update)
    if result.matched_count == 0:
        result = collection.update_one({"_id": _to_oid(id_str)}, update)
    return result


def _delete_by_id(collection, id_str):
    """Delete a document by _id, trying both string and ObjectId formats."""
    result = collection.delete_one({"_id": id_str})
    if result.deleted_count == 0:
        result = collection.delete_one({"_id": _to_oid(id_str)})
    return result


@alerts_bp.route("/", methods=["GET"])
@optional_auth
def list_alerts():
    try:
        db = get_db()
        alerts = list(
            db["alerts"].find({"user_id": _uid(), "status": {"$ne": "triggered"}})
        )
        for a in alerts:
            a["_id"] = str(a["_id"])
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route("/", methods=["POST"])
@optional_auth
def create_alert():
    try:
        db = get_db()
        data = request.get_json() or {}

        target = data.get("target", "").strip()
        if not target:
            return jsonify({"success": False, "error": "target is required"}), 400

        # Validate threshold is a reasonable number
        try:
            threshold = float(data.get("threshold", 0))
        except (ValueError, TypeError):
            return (
                jsonify(
                    {"success": False, "error": "threshold must be a valid number"}
                ),
                400,
            )

        if threshold < -50 or threshold > 100:
            return (
                jsonify(
                    {"success": False, "error": "threshold must be between -50 and 100"}
                ),
                400,
            )

        condition = data.get("condition", "above")
        if condition not in ("above", "below"):
            return (
                jsonify(
                    {"success": False, "error": "condition must be 'above' or 'below'"}
                ),
                400,
            )

        alert = {
            "user_id": _uid(),
            "type": data.get("type", "yield_change"),
            "target": target,
            "condition": condition,
            "threshold": threshold,
            "status": "active",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "triggered_at": None,
        }
        result = db["alerts"].insert_one(alert)
        alert["_id"] = str(result.inserted_id)
        return jsonify({"success": True, "data": alert}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route("/<alert_id>", methods=["PUT"])
@optional_auth
def update_alert(alert_id):
    try:
        db = get_db()
        data = request.get_json() or {}
        update = {}
        for field in ["type", "target", "condition", "threshold", "status"]:
            if field in data:
                update[field] = data[field]
        if update:
            _update_by_id(db["alerts"], alert_id, {"$set": update})
        return jsonify({"success": True, "data": {"updated": alert_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route("/<alert_id>", methods=["DELETE"])
@optional_auth
def delete_alert(alert_id):
    try:
        db = get_db()
        _delete_by_id(db["alerts"], alert_id)
        return jsonify({"success": True, "data": {"deleted": alert_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route("/triggered", methods=["GET"])
@optional_auth
def triggered_alerts():
    try:
        db = get_db()
        alerts = list(
            db["alerts"]
            .find({"user_id": _uid(), "status": "triggered"})
            .sort("triggered_at", -1)
            .limit(20)
        )
        for a in alerts:
            a["_id"] = str(a["_id"])
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
