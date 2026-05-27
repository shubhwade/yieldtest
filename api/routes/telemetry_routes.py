"""
Telemetry & Observability Routes
Exposes system-wide latency logs, resource metrics, validation states, and data confidence indices.
"""

from analytics.telemetry_engine import TelemetryEngine
from flask import Blueprint, jsonify

telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/v1/telemetry")


@telemetry_bp.route("/health", methods=["GET"])
def get_system_telemetry():
    """Retrieve full infrastructure and data quality metrics."""
    try:
        metrics = TelemetryEngine.get_observability_metrics()

        # Gather additional active data quality metrics
        from services.fred_service import fred_service

        curve = fred_service.get_yield_curve()

        metrics["data_quality"] = {
            "treasury_yield_curve": {
                "confidence_score": curve.get("telemetry", {}).get(
                    "confidence_score", 95
                ),
                "freshness_status": curve.get("telemetry", {})
                .get("freshness", {})
                .get("status", "FRESH"),
                "age_seconds": curve.get("telemetry", {})
                .get("freshness", {})
                .get("age_seconds", 0.0),
            }
        }

        return jsonify({"success": True, "data": metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@telemetry_bp.route("/latency", methods=["GET"])
def get_latency_logs():
    """Retrieve recent external API call latencies for dashboards."""
    try:
        logs = TelemetryEngine.get_api_latency_log()
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@telemetry_bp.route("/alerts", methods=["GET"])
def get_telemetry_alerts():
    """Retrieve unresolved multi-source validation discrepancy warnings."""
    try:
        alerts = TelemetryEngine.get_active_telemetry_alerts()
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@telemetry_bp.route("/resolve/<alert_id>", methods=["POST"])
def resolve_alert(alert_id: str):
    """Mark a specific telemetry validation warning as resolved by administrator."""
    try:
        success = TelemetryEngine.resolve_telemetry_alert(alert_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
