"""
YieldLens Comparison Engine
Compare different fixed-income instrument types across multiple dimensions.
"""

# ──────────────────────────────────────────────────────────────────────
#  Instrument profiles – typical characteristics for each asset class
# ──────────────────────────────────────────────────────────────────────

_PROFILES: dict[str, dict] = {
    "treasury": {
        "name": "U.S. Treasury",
        "typical_yield_range": [3.5, 5.0],
        "risk_level": "Very Low",
        "risk_score": 5,
        "typical_duration": [0.25, 30],
        "credit_quality": "AAA (Risk-Free)",
        "tax_treatment": "Federal taxable, state exempt",
        "liquidity": "Excellent",
        "liquidity_score": 98,
        "inflation_protection": "None (except TIPS)",
        "min_investment": 100,
        "income_frequency": "Semi-annual",
    },
    "corporate": {
        "name": "Corporate Bond",
        "typical_yield_range": [4.0, 7.0],
        "risk_level": "Low to Moderate",
        "risk_score": 30,
        "typical_duration": [1, 30],
        "credit_quality": "BBB to AAA",
        "tax_treatment": "Fully taxable",
        "liquidity": "Good",
        "liquidity_score": 75,
        "inflation_protection": "None",
        "min_investment": 1000,
        "income_frequency": "Semi-annual",
    },
    "municipal": {
        "name": "Municipal Bond",
        "typical_yield_range": [2.5, 5.0],
        "risk_level": "Low",
        "risk_score": 20,
        "typical_duration": [1, 30],
        "credit_quality": "A to AAA",
        "tax_treatment": "Federal tax-exempt, often state exempt",
        "liquidity": "Moderate",
        "liquidity_score": 55,
        "inflation_protection": "None",
        "min_investment": 5000,
        "income_frequency": "Semi-annual",
    },
    "tips": {
        "name": "TIPS (Inflation-Protected)",
        "typical_yield_range": [1.5, 3.0],
        "risk_level": "Very Low",
        "risk_score": 8,
        "typical_duration": [5, 30],
        "credit_quality": "AAA (Risk-Free)",
        "tax_treatment": "Federal taxable (phantom income)",
        "liquidity": "Good",
        "liquidity_score": 85,
        "inflation_protection": "Full CPI adjustment",
        "min_investment": 100,
        "income_frequency": "Semi-annual",
    },
    "bond_etf": {
        "name": "Bond ETF",
        "typical_yield_range": [3.0, 6.0],
        "risk_level": "Low to Moderate",
        "risk_score": 25,
        "typical_duration": [1, 15],
        "credit_quality": "Varies by fund",
        "tax_treatment": "Fully taxable",
        "liquidity": "Excellent",
        "liquidity_score": 95,
        "inflation_protection": "None",
        "min_investment": 1,
        "income_frequency": "Monthly",
    },
    "cd": {
        "name": "Certificate of Deposit",
        "typical_yield_range": [4.0, 5.5],
        "risk_level": "Very Low",
        "risk_score": 3,
        "typical_duration": [0.25, 5],
        "credit_quality": "FDIC Insured",
        "tax_treatment": "Fully taxable",
        "liquidity": "Low (early withdrawal penalty)",
        "liquidity_score": 20,
        "inflation_protection": "None",
        "min_investment": 500,
        "income_frequency": "Monthly or at maturity",
    },
    "money_market": {
        "name": "Money Market Fund",
        "typical_yield_range": [4.0, 5.5],
        "risk_level": "Very Low",
        "risk_score": 2,
        "typical_duration": [0, 0.25],
        "credit_quality": "AAA (stable NAV)",
        "tax_treatment": "Fully taxable",
        "liquidity": "Excellent",
        "liquidity_score": 99,
        "inflation_protection": "Partial (adjusts with rates)",
        "min_investment": 1,
        "income_frequency": "Daily accrual",
    },
    "high_yield": {
        "name": "High-Yield Bond",
        "typical_yield_range": [6.0, 10.0],
        "risk_level": "High",
        "risk_score": 65,
        "typical_duration": [2, 10],
        "credit_quality": "BB and below",
        "tax_treatment": "Fully taxable",
        "liquidity": "Moderate",
        "liquidity_score": 50,
        "inflation_protection": "None",
        "min_investment": 1000,
        "income_frequency": "Semi-annual",
    },
    "preferred": {
        "name": "Preferred Stock",
        "typical_yield_range": [5.0, 8.0],
        "risk_level": "Moderate to High",
        "risk_score": 50,
        "typical_duration": [5, 100],
        "credit_quality": "BBB to BB",
        "tax_treatment": "Qualified dividends (lower rate)",
        "liquidity": "Moderate",
        "liquidity_score": 60,
        "inflation_protection": "None",
        "min_investment": 25,
        "income_frequency": "Quarterly",
    },
    "reit": {
        "name": "REIT",
        "typical_yield_range": [4.0, 9.0],
        "risk_level": "Moderate to High",
        "risk_score": 55,
        "typical_duration": [0, 0],
        "credit_quality": "Varies",
        "tax_treatment": "Ordinary income (mostly)",
        "liquidity": "Good (if publicly traded)",
        "liquidity_score": 70,
        "inflation_protection": "Moderate (real assets)",
        "min_investment": 1,
        "income_frequency": "Quarterly",
    },
    "preferred_stock": {
        "name": "Preferred Stock",
        "typical_yield_range": [5.0, 8.0],
        "risk_level": "Moderate to High",
        "risk_score": 50,
        "typical_duration": [5, 100],
        "credit_quality": "BBB to BB",
        "tax_treatment": "Qualified dividends",
        "liquidity": "Moderate",
        "liquidity_score": 60,
        "inflation_protection": "None",
        "min_investment": 25,
        "income_frequency": "Quarterly",
    },
    "dividend_stock": {
        "name": "Dividend Stock",
        "typical_yield_range": [2.0, 6.0],
        "risk_level": "Moderate",
        "risk_score": 45,
        "typical_duration": [0, 0],
        "credit_quality": "Varies",
        "tax_treatment": "Qualified dividends",
        "liquidity": "Excellent",
        "liquidity_score": 95,
        "inflation_protection": "Moderate (earnings growth)",
        "min_investment": 1,
        "income_frequency": "Quarterly",
    },
    "fixed_deposit": {
        "name": "Fixed Deposit",
        "typical_yield_range": [4.0, 5.5],
        "risk_level": "Very Low",
        "risk_score": 3,
        "typical_duration": [0.25, 5],
        "credit_quality": "FDIC Insured",
        "tax_treatment": "Fully taxable",
        "liquidity": "Low",
        "liquidity_score": 15,
        "inflation_protection": "None",
        "min_investment": 1000,
        "income_frequency": "At maturity",
    },
    "international": {
        "name": "International Bond",
        "typical_yield_range": [1.0, 8.0],
        "risk_level": "Moderate to High",
        "risk_score": 55,
        "typical_duration": [1, 30],
        "credit_quality": "Varies by country",
        "tax_treatment": "Fully taxable + FX risk",
        "liquidity": "Moderate",
        "liquidity_score": 50,
        "inflation_protection": "None",
        "min_investment": 1000,
        "income_frequency": "Varies",
    },
}


class ComparisonEngine:
    """Compare fixed-income instrument types on multiple dimensions."""

    @staticmethod
    def get_instrument_profile(instrument_type: str) -> dict:
        """
        Return the typical-characteristics profile for an instrument type.

        Args:
            instrument_type: One of the supported type keys.

        Returns:
            Profile dict, or a default generic profile.
        """
        return _PROFILES.get(
            instrument_type,
            {
                "name": instrument_type.replace("_", " ").title(),
                "typical_yield_range": [3.0, 6.0],
                "risk_level": "Unknown",
                "risk_score": 50,
                "typical_duration": [0, 30],
                "credit_quality": "Unknown",
                "tax_treatment": "Fully taxable",
                "liquidity": "Unknown",
                "liquidity_score": 50,
                "inflation_protection": "Unknown",
                "min_investment": 1000,
                "income_frequency": "Varies",
            },
        )

    @classmethod
    def compare_instruments(cls, instruments: list[dict]) -> dict:
        """
        Build a comparison matrix for a list of instrument specifications.

        Each item in *instruments* should have at least:
            - type: str (instrument type key)
            - yield_value: float (optional, current yield in %)
            - duration: float (optional)

        Args:
            instruments: List of instrument dicts.

        Returns:
            Comparison result with per-instrument details and rankings.
        """
        if not instruments:
            return {"instruments": [], "rankings": {}}

        rows: list[dict] = []

        for inst in instruments:
            itype = inst.get("type", "corporate")
            profile = cls.get_instrument_profile(itype)

            # Use provided values or fall back to profile midpoints
            yield_val = inst.get("yield_value")
            if yield_val is None:
                yr = profile["typical_yield_range"]
                yield_val = (yr[0] + yr[1]) / 2

            duration = inst.get("duration")
            if duration is None:
                dr = profile["typical_duration"]
                duration = (dr[0] + dr[1]) / 2

            tax_bracket = inst.get("tax_bracket", 0.37)
            tax_exempt = itype == "municipal"

            if tax_exempt:
                tax_equiv = yield_val / (1 - tax_bracket)
            else:
                tax_equiv = yield_val

            row = {
                "type": itype,
                "name": profile["name"],
                "yield_pct": round(yield_val, 2),
                "tax_equivalent_yield_pct": round(tax_equiv, 2),
                "duration": round(duration, 2),
                "risk_level": profile["risk_level"],
                "risk_score": profile["risk_score"],
                "credit_quality": profile["credit_quality"],
                "liquidity": profile["liquidity"],
                "liquidity_score": profile["liquidity_score"],
                "inflation_protection": profile["inflation_protection"],
                "tax_treatment": profile["tax_treatment"],
                "min_investment": profile["min_investment"],
                "income_frequency": profile["income_frequency"],
            }
            rows.append(row)

        # Rankings
        by_yield = sorted(
            rows, key=lambda r: r["tax_equivalent_yield_pct"], reverse=True
        )
        by_risk = sorted(rows, key=lambda r: r["risk_score"])
        by_liquidity = sorted(rows, key=lambda r: r["liquidity_score"], reverse=True)

        rankings = {
            "best_yield": by_yield[0]["type"] if by_yield else None,
            "lowest_risk": by_risk[0]["type"] if by_risk else None,
            "most_liquid": by_liquidity[0]["type"] if by_liquidity else None,
            "yield_ranking": [r["type"] for r in by_yield],
            "risk_ranking": [r["type"] for r in by_risk],
            "liquidity_ranking": [r["type"] for r in by_liquidity],
        }

        return {
            "instruments": rows,
            "rankings": rankings,
            "count": len(rows),
        }
