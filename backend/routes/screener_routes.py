"""Screener routes — advanced bond search and filters."""

import re

from analytics.bond_math import BondCalculator
from database.mongo import get_db
from flask import Blueprint, jsonify, request
from ai.service import ai_service

screener_bp = Blueprint("screener", __name__, url_prefix="/api/v1/screener")
calc = BondCalculator()


@screener_bp.route("/search", methods=["POST"])
def search():
    try:
        db = get_db()
        data = request.get_json() or {}
        query = {}

        if data.get("type"):
            query["type"] = (
                data["type"] if isinstance(data["type"], str) else {"$in": data["type"]}
            )
        if data.get("rating"):
            query["rating"] = (
                data["rating"]
                if isinstance(data["rating"], str)
                else {"$in": data["rating"]}
            )
        if data.get("sector"):
            query["sector"] = (
                data["sector"]
                if isinstance(data["sector"], str)
                else {"$in": data["sector"]}
            )
        if data.get("search"):
            escaped = re.escape(data["search"])
            query["$or"] = [
                {"issuer": {"$regex": escaped, "$options": "i"}},
                {"cusip": {"$regex": escaped, "$options": "i"}},
                {"name": {"$regex": escaped, "$options": "i"}},
            ]
        if data.get("minYtm") or data.get("maxYtm"):
            # Note: YTM is often calculated, but if we have it stored or want to filter by price/coupon approx
            pass
        if data.get("state"):
            query["state"] = data["state"]
        if data.get("callable") is not None:
            query["callable"] = data["callable"]
        if data.get("tax_exempt") is not None:
            query["tax_exempt"] = data["tax_exempt"]
        if data.get("min_coupon") is not None or data.get("max_coupon") is not None:
            coupon_q = {}
            if data.get("min_coupon") is not None:
                coupon_q["$gte"] = float(data["min_coupon"])
            if data.get("max_coupon") is not None:
                coupon_q["$lte"] = float(data["max_coupon"])
            query["coupon_rate"] = coupon_q

        page = data.get("page", 1)
        limit = data.get("limit", 50)
        sort_by = data.get("sort_by", "coupon_rate")
        sort_order = -1 if data.get("sort_order", "desc") == "desc" else 1
        skip = (page - 1) * limit

        total = db["bonds"].count_documents(query)
        bonds = list(
            db["bonds"].find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        )

        for b in bonds:
            b["_id"] = str(b["_id"])
            try:
                analytics = calc.calculate_full_bond_analytics(b)
                b["ytm"] = analytics.get("ytm")
                b["duration"] = analytics.get("macaulay_duration")
                b["spread_bps"] = analytics.get("spread_bps")
                b["risk_score"] = analytics.get("risk_score")
            except Exception:
                b["ytm"] = None
                b["duration"] = None

        # Contextual Intelligence: If searching a specific issuer, get related news/AI brief
        intelligence = {}
        if data.get("search") and len(bonds) > 0:
            issuer = bonds[0].get("issuer")
            try:
                intelligence["ai_insight"] = ai_service.answer_query(
                    f"Quick credit outlook for {issuer} and related news themes.", {}
                )
                intelligence["related_issuer"] = issuer
            except Exception:
                # Don't let AI failures block search results
                intelligence["ai_insight"] = None
                intelligence["related_issuer"] = issuer

        return jsonify(
            {
                "success": True,
                "data": {
                    "bonds": bonds,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit,
                    "intelligence": intelligence,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@screener_bp.route("/filters", methods=["GET"])
def filters():
    try:
        db = get_db()
        return jsonify(
            {
                "success": True,
                "data": {
                    "types": db["bonds"].distinct("type"),
                    "ratings": db["bonds"].distinct("rating"),
                    "sectors": db["bonds"].distinct("sector"),
                    "states": [s for s in db["bonds"].distinct("state") if s],
                    "issuers": db["bonds"].distinct("issuer"),
                    "subtypes": db["bonds"].distinct("subtype"),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
