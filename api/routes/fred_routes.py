"""FRED routes — yield curve, rates, spreads, economic indicators."""

from flask import Blueprint, jsonify, request
from services.fred_service import fred_service

fred_bp = Blueprint("fred", __name__, url_prefix="/api/v1/fred")


@fred_bp.route("/yield-curve", methods=["GET"])
def yield_curve():
    try:
        data = fred_service.get_yield_curve()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/yield-curve/history", methods=["GET"])
def yield_curve_history():
    try:
        days = request.args.get("days", 30, type=int)
        data = fred_service.get_yield_curve_history(days)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/rates", methods=["GET"])
def rates():
    try:
        indicators = fred_service.get_economic_indicators()
        rates_data = {
            k: v for k, v in indicators.items() if v.get("category") == "rates"
        }
        return jsonify({"success": True, "data": rates_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/spreads", methods=["GET"])
def spreads():
    try:
        data = fred_service.get_spread_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/series/<series_id>", methods=["GET"])
def series(series_id):
    try:
        limit = request.args.get("limit", 365, type=int)
        data = fred_service.get_series(series_id, limit=limit)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/inversion", methods=["GET"])
def inversion():
    try:
        data = fred_service.get_inversion_analysis()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fred_bp.route("/economic", methods=["GET"])
def economic():
    try:
        data = fred_service.get_economic_indicators()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
