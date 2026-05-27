"""Watchlist routes — CRUD for user watchlists."""

import time

from database.mongo import get_db
from flask import Blueprint, g, jsonify, request
from middleware.auth import optional_auth

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/v1/watchlist")
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


@watchlist_bp.route("/", methods=["GET"])
@optional_auth
def list_watchlists():
    try:
        db = get_db()
        wls = list(db["watchlists"].find({"user_id": _uid()}))
        for w in wls:
            w["_id"] = str(w["_id"])
            enriched = []
            for item in w.get("bonds", []):
                bond_id = item.get("bond_id") if isinstance(item, dict) else item
                bond = _find_by_id(db["bonds"], bond_id)
                if bond:
                    bond["_id"] = str(bond["_id"])
                    enriched.append(
                        {
                            **(item if isinstance(item, dict) else {"bond_id": item}),
                            "bond": bond,
                        }
                    )
            w["enriched_bonds"] = enriched
        return jsonify({"success": True, "data": wls})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/", methods=["POST"])
@optional_auth
def create_watchlist():
    try:
        db = get_db()
        data = request.get_json() or {}
        wl = {
            "user_id": _uid(),
            "name": data.get("name", "My Watchlist"),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bonds": [],
        }
        result = db["watchlists"].insert_one(wl)
        wl["_id"] = str(result.inserted_id)
        return jsonify({"success": True, "data": wl}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/<wl_id>/add", methods=["POST"])
@optional_auth
def add_bond(wl_id):
    try:
        db = get_db()
        data = request.get_json() or {}
        bond_id = data.get("bond_id")
        if not bond_id:
            return jsonify({"success": False, "error": "bond_id required"}), 400

        # Validate bond exists
        bond = _find_by_id(db["bonds"], bond_id)
        if not bond:
            return jsonify({"success": False, "error": "Bond not found in market"}), 404

        # Prevent duplicates
        wl = _find_by_id(db["watchlists"], wl_id)
        if not wl:
            return jsonify({"success": False, "error": "Watchlist not found"}), 404
        existing_ids = [
            b.get("bond_id") if isinstance(b, dict) else b for b in wl.get("bonds", [])
        ]
        if bond_id in existing_ids:
            return (
                jsonify({"success": False, "error": "Bond already in watchlist"}),
                409,
            )

        _update_by_id(
            db["watchlists"],
            wl_id,
            {
                "$push": {
                    "bonds": {
                        "bond_id": bond_id,
                        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                }
            },
        )
        return jsonify({"success": True, "data": {"added": bond_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/<wl_id>/remove/<bond_id>", methods=["DELETE"])
@optional_auth
def remove_bond(wl_id, bond_id):
    try:
        db = get_db()
        _update_by_id(
            db["watchlists"], wl_id, {"$pull": {"bonds": {"bond_id": bond_id}}}
        )
        return jsonify({"success": True, "data": {"removed": bond_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
