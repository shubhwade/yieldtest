"""Macro routes — economic indicators, inflation, employment."""

from flask import Blueprint, jsonify
from services.fred_service import fred_service

macro_bp = Blueprint("macro", __name__, url_prefix="/api/v1/macro")


@macro_bp.route("/indicators", methods=["GET"])
def indicators():
    try:
        data = fred_service.get_economic_indicators()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@macro_bp.route("/inflation", methods=["GET"])
def inflation():
    try:
        indicators = fred_service.get_economic_indicators()
        inflation_data = {
            k: v for k, v in indicators.items() if v.get("category") == "inflation"
        }
        cpi_history = fred_service.get_series("CPIAUCSL", limit=60)
        return jsonify(
            {
                "success": True,
                "data": {"indicators": inflation_data, "cpi_history": cpi_history},
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@macro_bp.route("/employment", methods=["GET"])
def employment():
    try:
        indicators = fred_service.get_economic_indicators()
        unemployment = indicators.get("UNRATE", {})
        unemployment_history = fred_service.get_series("UNRATE", limit=60)
        return jsonify(
            {
                "success": True,
                "data": {"unemployment": unemployment, "history": unemployment_history},
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
