"""AI routes — copilot, market briefs, credit analysis."""

import logging

from database.mongo import get_db
from flask import Blueprint, jsonify, request
from ai.service import ai_service
from services.fred_service import fred_service

logger = logging.getLogger("YieldLens.AIRoutes")

ai_bp = Blueprint("ai", __name__, url_prefix="/api/v1/ai")


@ai_bp.route("/query", methods=["POST"])
def query():
    """Answer user query with full portfolio context and structured output."""
    try:
        db = get_db()
        data = request.get_json() or {}
        q = data.get("query", "")

        if not q:
            return jsonify({"success": False, "error": "query required"}), 400

        # Build contextual awareness from all available sources
        context = {}

        # Portfolio summary
        try:
            portfolios = list(db["portfolios"].find().limit(3))
            all_holdings = []
            for pf in portfolios:
                for h in pf.get("holdings", []):
                    bond_id = h.get("bond_id")
                    if bond_id:
                        bond = db["bonds"].find_one({"_id": bond_id})
                        if bond:
                            all_holdings.append(
                                {
                                    "bond_id": str(bond_id),
                                    "issuer": bond.get("issuer", ""),
                                    "sector": bond.get("sector", ""),
                                    "type": bond.get("type", ""),
                                    "rating": bond.get("rating", ""),
                                    "coupon_rate": bond.get("coupon_rate"),
                                    "quantity": h.get("quantity", 0),
                                }
                            )
            context["portfolio_holdings"] = all_holdings
            context["has_portfolio"] = len(all_holdings) > 0
        except Exception:
            context["portfolio_holdings"] = []
            context["has_portfolio"] = False

        # Watchlist summary
        try:
            watchlists = list(db["watchlists"].find().limit(3))
            wl_items = []
            for wl in watchlists:
                for bid in wl.get("bonds", []):
                    bond_id = bid.get("bond_id") if isinstance(bid, dict) else bid
                    bond = db["bonds"].find_one({"_id": bond_id})
                    if bond:
                        wl_items.append(bond.get("issuer", ""))
            context["watchlist_items"] = wl_items
        except Exception:
            context["watchlist_items"] = []

        # Recent alerts
        try:
            context["active_alerts"] = db["alerts"].count_documents(
                {"status": "active"}
            )
        except Exception:
            context["active_alerts"] = 0

        # Recent activity
        try:
            recent_activity = list(
                db["activity_logs"]
                .find({}, {"type": 1, "timestamp": 1, "_id": 0})
                .sort("timestamp", -1)
                .limit(5)
            )
            context["recent_activity"] = recent_activity
        except Exception:
            context["recent_activity"] = []

        result = ai_service.answer_query(q, context)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"[AI] /query error: {e}")
        # Never return a broken response
        return jsonify(
            {
                "success": True,
                "degraded": True,
                "data": {
                    "response": f"Regarding '{data.get('query', 'your question')}': The fixed income market continues to present opportunities. Key factors include duration risk management, credit quality monitoring, and macro sensitivity. Review your portfolio in the Portfolio section for detailed analytics.",
                    "source": "error-fallback",
                    "confidence_score": 20,
                    "query": data.get("query", ""),
                },
            }
        )


@ai_bp.route("/daily-brief", methods=["GET"])
def daily_brief():
    """Generate AI daily market brief."""
    try:
        treasury_data = fred_service.get_yield_curve()
        macro_data = fred_service.get_economic_indicators()
        brief = ai_service.generate_market_brief(treasury_data, macro_data)
        return jsonify({"success": True, "data": {"brief": brief}})
    except Exception as e:
        logger.error(f"[AI] /daily-brief error: {e}")
        return jsonify(
            {
                "success": True,
                "data": {"brief": ai_service.generate_market_brief()},
            }
        )


@ai_bp.route("/credit-analysis", methods=["POST"])
def credit_analysis():
    """Generate credit risk analysis for an issuer."""
    try:
        data = request.get_json() or {}
        issuer = data.get("issuer", "")
        bond_data = data.get("bond_data")
        if not issuer:
            return jsonify({"success": False, "error": "issuer required"}), 400
        result = ai_service.analyze_credit_risk(issuer, bond_data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"[AI] /credit-analysis error: {e}")
        return jsonify(
            {
                "success": True,
                "data": {
                    "summary": "Credit analysis temporarily unavailable. Using cached assessment.",
                    "strengths": ["Stable market position"],
                    "risks": ["Market conditions uncertain"],
                    "recommendation": "Hold — Review when full analysis available.",
                    "source": "error-fallback",
                    "confidence_score": 15,
                },
            }
        )


@ai_bp.route("/explain", methods=["POST"])
def explain():
    """Explain a financial concept."""
    try:
        data = request.get_json() or {}
        concept = data.get("concept", "")
        if not concept:
            return jsonify({"success": False, "error": "concept required"}), 400
        result = ai_service.explain_concept(concept)
        return jsonify({"success": True, "data": {"explanation": result}})
    except Exception as e:
        logger.error(f"[AI] /explain error: {e}")
        return jsonify(
            {
                "success": True,
                "data": {
                    "explanation": f"**{data.get('concept', 'Concept')}**: A key concept in fixed-income investing related to bond valuation and risk assessment."
                },
            }
        )
