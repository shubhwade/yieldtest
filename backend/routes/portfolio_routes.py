"""Portfolio routes — CRUD for user portfolios and holdings."""

import time

from analytics.bond_math import BondCalculator
from analytics.risk_engine import RiskEngine
from database.mongo import get_db
from events.dispatcher import HOLDING_ADDED, PORTFOLIO_UPDATED, dispatcher
from flask import Blueprint, g, jsonify, request
from middleware.auth import optional_auth

portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/api/v1/portfolio")
calc = BondCalculator()
risk = RiskEngine()

DEMO_USER = "demo_user_001"


def _get_user_id():
    return getattr(g, "user_id", None) or DEMO_USER


def _to_oid(id_str):
    """Convert string to ObjectId if valid, otherwise return as-is.
    Handles both seeded string _ids and auto-generated ObjectIds."""
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


def _calculate_holding_value(bond, quantity):
    """Calculate the market value of a holding correctly.
    Standard bonds: (price/100) * face_value * quantity
    ETFs/Money Market: price * quantity (price IS the NAV)
    """
    bond_type = bond.get("type", "")
    price = bond.get("price", 100)
    face_value = bond.get("face_value")

    if (
        bond_type in ("bond_etf", "money_market")
        or face_value is None
        or face_value <= 1
    ):
        # ETFs and money market: price is the NAV per share/unit
        return price * quantity
    else:
        # Standard bonds: price is % of face value
        return (price / 100.0) * face_value * quantity


@portfolio_bp.route("/", methods=["GET"])
@optional_auth
def list_portfolios():
    try:
        db = get_db()
        user_id = _get_user_id()
        portfolios = list(db["portfolios"].find({"user_id": user_id}))
        for p in portfolios:
            p["_id"] = str(p["_id"])
        return jsonify({"success": True, "data": portfolios})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/", methods=["POST"])
@optional_auth
def create_portfolio():
    try:
        db = get_db()
        data = request.get_json() or {}
        portfolio = {
            "user_id": _get_user_id(),
            "name": data.get("name", "My Portfolio"),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "holdings": [],
        }
        result = db["portfolios"].insert_one(portfolio)
        portfolio["_id"] = str(result.inserted_id)
        return jsonify({"success": True, "data": portfolio}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/<portfolio_id>", methods=["GET"])
@optional_auth
def get_portfolio(portfolio_id):
    try:
        db = get_db()
        portfolio = _find_by_id(db["portfolios"], portfolio_id)
        if not portfolio:
            return jsonify({"success": False, "error": "Portfolio not found"}), 404
        portfolio["_id"] = str(portfolio["_id"])

        # Enrich holdings with bond details and analytics
        enriched_holdings = []
        for holding in portfolio.get("holdings", []):
            bond = _find_by_id(db["bonds"], holding["bond_id"])
            if bond:
                bond["_id"] = str(bond["_id"])
                try:
                    analytics = calc.calculate_full_bond_analytics(bond)
                except Exception:
                    analytics = {}

                qty = holding.get("quantity", 0)
                current_value = _calculate_holding_value(bond, qty)
                avg_price = holding.get("avg_price", 100)
                # PnL: difference between current price and purchase price, times quantity
                # For standard bonds, normalize by face_value
                face_value = bond.get("face_value")
                bond_type = bond.get("type", "")
                if (
                    bond_type in ("bond_etf", "money_market")
                    or face_value is None
                    or face_value <= 1
                ):
                    pnl = round((bond.get("price", 100) - avg_price) * qty, 2)
                else:
                    pnl = round(
                        ((bond.get("price", 100) - avg_price) / 100.0)
                        * face_value
                        * qty,
                        2,
                    )

                enriched_holdings.append(
                    {
                        **holding,
                        "bond": bond,
                        "analytics": analytics,
                        "current_value": round(current_value, 2),
                        "pnl": pnl,
                    }
                )
        portfolio["enriched_holdings"] = enriched_holdings

        # Calculate portfolio summary with market-value-weighted averages
        total_value = sum(h.get("current_value", 0) for h in enriched_holdings)

        # Annual income: coupon_rate(%) * face_value * quantity for each holding
        total_income = 0
        weighted_ytm = 0
        weighted_duration = 0
        for h in enriched_holdings:
            bond = h.get("bond", {})
            qty = (
                h.get("quantity", 0)
                if isinstance(h.get("quantity"), (int, float))
                else 0
            )
            coupon_rate = bond.get("coupon_rate", 0) or 0
            face_value = bond.get("face_value")
            bond_type = bond.get("type", "")

            if (
                bond_type in ("bond_etf", "money_market")
                or face_value is None
                or face_value <= 1
            ):
                # ETFs: distribution yield * NAV * shares
                total_income += (coupon_rate / 100.0) * bond.get("price", 0) * qty
            else:
                # Standard bonds: coupon_rate(%) * face_value * quantity
                total_income += (coupon_rate / 100.0) * face_value * qty

            # Market-value-weighted YTM and duration
            holding_value = h.get("current_value", 0)
            ytm = h.get("analytics", {}).get("ytm", 0) or 0
            dur = h.get("analytics", {}).get("macaulay_duration", 0) or 0
            if total_value > 0:
                weight = holding_value / total_value
                weighted_ytm += ytm * weight
                weighted_duration += dur * weight

        portfolio["summary"] = {
            "total_value": round(total_value, 2),
            "total_holdings": len(enriched_holdings),
            "annual_income": round(total_income, 2),
            "avg_ytm": round(weighted_ytm, 4),
            "avg_duration": round(weighted_duration, 4),
        }
        return jsonify({"success": True, "data": portfolio})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/<portfolio_id>/holdings", methods=["POST"])
@optional_auth
def add_holding(portfolio_id):
    try:
        db = get_db()
        data = request.get_json() or {}
        bond_id = data.get("bond_id")
        quantity = data.get("quantity", 1)
        avg_price = data.get("avg_price", 100)
        if not bond_id:
            return jsonify({"success": False, "error": "bond_id required"}), 400

        # Validate bond exists
        bond = _find_by_id(db["bonds"], bond_id)
        if not bond:
            return jsonify({"success": False, "error": "Bond not found in market"}), 404

        # Check for existing holding to prevent duplicates
        portfolio = _find_by_id(db["portfolios"], portfolio_id)
        if not portfolio:
            return jsonify({"success": False, "error": "Portfolio not found"}), 404

        existing = next(
            (h for h in portfolio.get("holdings", []) if h.get("bond_id") == bond_id),
            None,
        )
        if existing:
            # Update existing holding: recalculate avg price and add quantity
            old_qty = existing.get("quantity", 0)
            old_avg = existing.get("avg_price", 100)
            new_qty = old_qty + quantity
            new_avg = (
                round(((old_avg * old_qty) + (avg_price * quantity)) / new_qty, 4)
                if new_qty > 0
                else avg_price
            )

            _update_by_id(
                db["portfolios"],
                portfolio_id,
                {
                    "$set": {
                        "holdings.$[elem].quantity": new_qty,
                        "holdings.$[elem].avg_price": new_avg,
                        "updated_at": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                        ),
                    }
                },
            )
            # Fallback: pymongo array filters require specific syntax
            # Use pull+push approach for compatibility
            actual_pid = portfolio["_id"]
            db["portfolios"].update_one(
                {"_id": actual_pid}, {"$pull": {"holdings": {"bond_id": bond_id}}}
            )
            updated_holding = {
                "bond_id": bond_id,
                "quantity": new_qty,
                "avg_price": new_avg,
                "added_at": existing.get(
                    "added_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                ),
            }
            db["portfolios"].update_one(
                {"_id": actual_pid},
                {
                    "$push": {"holdings": updated_holding},
                    "$set": {
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    },
                },
            )
            holding = updated_holding
        else:
            holding = {
                "bond_id": bond_id,
                "quantity": quantity,
                "avg_price": avg_price,
                "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            _update_by_id(
                db["portfolios"],
                portfolio_id,
                {
                    "$push": {"holdings": holding},
                    "$set": {
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    },
                },
            )

        # Emit events for intelligence system
        dispatcher.emit(
            HOLDING_ADDED, {"portfolio_id": portfolio_id, "holding": holding}
        )
        dispatcher.emit(
            PORTFOLIO_UPDATED, {"portfolio_id": portfolio_id, "action": "add"}
        )

        return jsonify({"success": True, "data": holding}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/<portfolio_id>/holdings/<bond_id>", methods=["DELETE"])
@optional_auth
def remove_holding(portfolio_id, bond_id):
    try:
        db = get_db()
        _update_by_id(
            db["portfolios"],
            portfolio_id,
            {"$pull": {"holdings": {"bond_id": bond_id}}},
        )
        return jsonify({"success": True, "data": {"removed": bond_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/<portfolio_id>/analytics", methods=["GET"])
@optional_auth
def portfolio_analytics(portfolio_id):
    try:
        db = get_db()
        portfolio = _find_by_id(db["portfolios"], portfolio_id)
        if not portfolio:
            return jsonify({"success": False, "error": "Portfolio not found"}), 404
        holdings_data = []
        for h in portfolio.get("holdings", []):
            bond = _find_by_id(db["bonds"], h["bond_id"])
            if bond:
                holdings_data.append({**h, "bond": bond})
        risk_metrics = risk.calculate_portfolio_risk(holdings_data)
        return jsonify({"success": True, "data": risk_metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
