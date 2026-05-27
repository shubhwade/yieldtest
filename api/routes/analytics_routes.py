"""Analytics routes — bond calculations, scenario analysis, comparisons."""

from analytics.bond_math import BondCalculator
from analytics.comparison_engine import ComparisonEngine
from analytics.scenario_engine import ScenarioEngine
from flask import Blueprint, jsonify, request
from services.fred_service import fred_service

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")
calc = BondCalculator()
comparison = ComparisonEngine()
scenario = ScenarioEngine()


@analytics_bp.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        price = float(data.get("price", 100))
        coupon = float(data.get("coupon", 5))
        years = float(data.get("years_to_maturity", 10))
        frequency = int(data.get("frequency", 2))
        face_value = float(data.get("face_value", 100))

        ytm = calc.calculate_ytm(price, coupon, years, frequency, face_value)
        current_yield = calc.calculate_current_yield(coupon, price)
        mac_dur, mod_dur = calc.calculate_duration(coupon, ytm, years, frequency)
        dv01 = calc.calculate_dv01(mod_dur, price)
        convexity = calc.calculate_convexity(coupon, ytm, years, frequency)
        bond_price = calc.calculate_bond_price(
            coupon, ytm, years, frequency, face_value
        )

        result = {
            "ytm": round(ytm, 6),
            "current_yield": round(current_yield, 6),
            "macaulay_duration": round(mac_dur, 4),
            "modified_duration": round(mod_dur, 4),
            "dv01": round(dv01, 6),
            "convexity": round(convexity, 4),
            "theoretical_price": round(bond_price, 4),
            "accrued_interest": 0,
        }
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/scenario", methods=["POST"])
def scenario_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        coupon = float(data.get("coupon", 5))
        current_ytm = float(data.get("current_ytm", 4.5))
        years = float(data.get("years_to_maturity", 10))
        scenarios = data.get("yield_scenarios", [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2])

        result = calc.scenario_analysis(coupon, current_ytm, years, scenarios)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        instruments = data.get("instruments", [])
        if not instruments:
            return (
                jsonify({"success": False, "error": "instruments list required"}),
                400,
            )
        result = comparison.compare_instruments(instruments)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/stress-test", methods=["POST"])
def stress_test():
    try:
        data = request.get_json() or {}
        from database.mongo import get_db

        db = get_db()
        bonds = list(
            db["bonds"].find({"type": {"$in": ["treasury", "corporate"]}}).limit(50)
        )
        for b in bonds:
            b["_id"] = str(b["_id"])
        results = scenario.run_all_scenarios(bonds)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/forward-rates", methods=["GET"])
def forward_rates():
    try:
        curve = fred_service.get_yield_curve()
        values = curve.get("curve", {})
        forward_rates = []
        maturities = [
            ("1Y", 1),
            ("2Y", 2),
            ("3Y", 3),
            ("5Y", 5),
            ("7Y", 7),
            ("10Y", 10),
        ]
        for i in range(len(maturities) - 1):
            label1, t1 = maturities[i]
            label2, t2 = maturities[i + 1]
            y1 = values.get(label1, {}).get("value")
            y2 = values.get(label2, {}).get("value")
            if y1 is not None and y2 is not None:
                forward = ((1 + y2 / 100) ** t2 / (1 + y1 / 100) ** t1) ** (
                    1 / (t2 - t1)
                ) - 1
                forward_rates.append(
                    {
                        "period": f"{label1}-{label2}",
                        "forward_rate": round(forward * 100, 4),
                        "spot_start": y1,
                        "spot_end": y2,
                    }
                )
        return jsonify({"success": True, "data": forward_rates})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
