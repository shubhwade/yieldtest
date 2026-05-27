"""Market routes — dashboard, summary, heatmap, movers, sentiment."""

from database.mongo import get_db
from flask import Blueprint, jsonify
from services.market_data_service import market_data_service

market_bp = Blueprint("market", __name__, url_prefix="/api/v1/market")


@market_bp.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        db = get_db()
        data = market_data_service.get_dashboard_data(db)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/summary", methods=["GET"])
def summary():
    try:
        db = get_db()
        data = market_data_service.get_market_summary(db)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/heatmap", methods=["GET"])
def heatmap():
    try:
        data = market_data_service.get_market_heatmap()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/movers", methods=["GET"])
def movers():
    try:
        db = get_db()
        data = market_data_service.get_top_movers(db)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@market_bp.route("/sentiment", methods=["GET"])
def sentiment():
    try:
        from services.fred_service import fred_service

        yield_curve = fred_service.get_yield_curve()
        spreads = fred_service.get_spread_data()
        data = market_data_service.get_market_sentiment(yield_curve, spreads)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
