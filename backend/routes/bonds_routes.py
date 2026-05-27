"""Bond routes — list, detail, types, sectors, stats."""

import time

from analytics.bond_math import BondCalculator
from database.mongo import get_db
from flask import Blueprint, jsonify, request


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


bonds_bp = Blueprint("bonds", __name__, url_prefix="/api/v1/bonds")
calc = BondCalculator()


@bonds_bp.route("/", methods=["GET"])
def list_bonds():
    try:
        db = get_db()
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)
        bond_type = request.args.get("type")
        skip = (page - 1) * limit
        query = {}
        if bond_type:
            query["type"] = bond_type
        total = db["bonds"].count_documents(query)
        bonds = list(db["bonds"].find(query).skip(skip).limit(limit))
        for b in bonds:
            b["_id"] = str(b["_id"])
        return jsonify(
            {
                "success": True,
                "data": {
                    "bonds": bonds,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bonds_bp.route("/<bond_id>", methods=["GET"])
def get_bond(bond_id):
    try:
        db = get_db()
        bond = _find_by_id(db["bonds"], bond_id)
        if not bond:
            return jsonify({"success": False, "error": "Bond not found"}), 404
        bond["_id"] = str(bond["_id"])
        # Calculate analytics on-the-fly
        try:
            analytics = calc.calculate_full_bond_analytics(bond)
            bond["analytics"] = analytics
        except Exception:
            bond["analytics"] = {}
        return jsonify({"success": True, "data": bond})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bonds_bp.route("/types", methods=["GET"])
def bond_types():
    try:
        db = get_db()
        types = db["bonds"].distinct("type")
        return jsonify({"success": True, "data": types})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bonds_bp.route("/sectors", methods=["GET"])
def bond_sectors():
    try:
        db = get_db()
        sectors = db["bonds"].distinct("sector")
        return jsonify({"success": True, "data": sectors})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bonds_bp.route("/", methods=["POST"])
def add_bond():
    try:
        db = get_db()
        data = request.get_json() or {}
        required = ["issuer", "cusip", "type", "coupon_rate", "maturity_date"]
        for r in required:
            if r not in data:
                return (
                    jsonify({"success": False, "error": f"Field {r} is required"}),
                    400,
                )

        # Check for CUSIP uniqueness
        existing = db["bonds"].find_one({"cusip": data.get("cusip")})
        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Bond with CUSIP {data.get('cusip')} already exists",
                    }
                ),
                409,
            )

        bond = {
            "issuer": data.get("issuer"),
            "cusip": data.get("cusip"),
            "type": data.get("type"),
            "coupon_rate": float(data.get("coupon_rate")),
            "maturity_date": data.get("maturity_date"),
            "price": float(data.get("price", 100.0)),
            "face_value": float(data.get("face_value", 1000.0)),
            "rating": data.get("rating", "NR"),
            "sector": data.get("sector", "Other"),
            "frequency": int(data.get("frequency", 2)),
            "callable": bool(data.get("callable", False)),
            "tax_exempt": bool(data.get("tax_exempt", False)),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        result = db["bonds"].insert_one(bond)
        bond["_id"] = str(result.inserted_id)
        return jsonify({"success": True, "data": bond}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bonds_bp.route("/stats", methods=["GET"])
def bond_stats():
    try:
        db = get_db()
        pipeline = [
            {
                "$group": {
                    "_id": "$type",
                    "count": {"$sum": 1},
                    "avg_coupon": {"$avg": "$coupon_rate"},
                    "avg_price": {"$avg": "$price"},
                    "min_price": {"$min": "$price"},
                    "max_price": {"$max": "$price"},
                }
            }
        ]
        stats = list(db["bonds"].aggregate(pipeline))
        total = db["bonds"].count_documents({})
        return jsonify({"success": True, "data": {"by_type": stats, "total": total}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
