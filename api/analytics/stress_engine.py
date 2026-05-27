"""
YieldLens Stress Testing Engine
Evaluates portfolio price sensitivity under historical crises and macroeconomic shocks.
"""

from typing import Dict, List

from utils.helpers import safe_float


class StressEngine:
    """Stress testing simulation engine for fixed-income portfolios."""

    CRISIS_SCENARIOS = {
        "2008_credit_crisis": {
            "name": "2008 Credit Crisis",
            "treasury_shift_bps": -150.0,  # Flight to quality
            "corporate_spread_shift_bps": 450.0,  # Credit spread widening
            "muni_spread_shift_bps": 200.0,
            "description": "Replicates the aftermath of Lehman Brothers collapse. High-quality treasuries rallied, while high-yield and investment-grade spreads widened dramatically due to liquidity crunch.",
        },
        "2013_taper_tantrum": {
            "name": "2013 Taper Tantrum",
            "treasury_shift_bps": 140.0,  # Rapid rate spike
            "corporate_spread_shift_bps": 40.0,  # Modest spread rise
            "muni_spread_shift_bps": 80.0,
            "description": "Simulates Fed Chairman Bernanke's tapering announcement. Rates rose rapidly across the curve, hitting munis and long-duration corporate bonds hard.",
        },
        "2020_covid_shock": {
            "name": "2020 COVID Liquidity Crisis",
            "treasury_shift_bps": -80.0,
            "corporate_spread_shift_bps": 280.0,
            "muni_spread_shift_bps": 150.0,
            "description": "Replicates March 2020 market freeze. Massive dash for cash caused absolute yield spike before Fed intervention, combined with major corporate credit spreads widening.",
        },
        "stagflation_shock": {
            "name": "Stagflation Shock",
            "treasury_shift_bps": 200.0,  # Inflation spike rates rise
            "corporate_spread_shift_bps": 120.0,
            "muni_spread_shift_bps": 80.0,
            "description": "Simulates persistent inflation and economic contraction. High interest rates depress fixed coupon bond values, although short-duration TIPS outperform nominal counterparts.",
        },
        "yield_curve_inversion": {
            "name": "Severe Curve Inversion",
            "short_shift_bps": 150.0,  # Short rates rise
            "long_shift_bps": -50.0,  # Long rates fall
            "corporate_spread_shift_bps": 50.0,
            "muni_spread_shift_bps": 30.0,
            "description": "Replicates monetary tightening phase. Short rates rise due to Fed hikes, while long rates depress due to recession expectations, causing an inverted yield curve.",
        },
    }

    @staticmethod
    def calculate_scenario_impact(holdings: List[Dict], scenario_id: str) -> Dict:
        """
        Evaluate portfolio price impact under a specific historical crisis scenario.
        """
        sc = StressEngine.CRISIS_SCENARIOS.get(scenario_id)
        if not sc:
            return {"error": f"Scenario {scenario_id} not found"}

        total_portfolio_value_impact = 0.0
        details = []

        # Scenario parameters
        t_shift = sc.get("treasury_shift_bps", 0.0) / 10000.0
        c_shift = sc.get("corporate_spread_shift_bps", 0.0) / 10000.0
        m_shift = sc.get("muni_spread_shift_bps", 0.0) / 10000.0

        short_shift = sc.get("short_shift_bps", None)
        long_shift = sc.get("long_shift_bps", None)

        for h in holdings:
            w = safe_float(h.get("weight", 0.0))
            md = safe_float(h.get("modified_duration", 0.0))
            cx = safe_float(h.get("convexity", 0.0))
            bond_type = h.get("type", "corporate").lower()
            years = safe_float(h.get("years_to_maturity", 1.0))

            # Determine yield shift
            shift = 0.0
            if short_shift is not None and long_shift is not None:
                # Inversion / non-parallel curve shift
                if years <= 2.0:
                    shift = short_shift / 10000.0
                elif years >= 10.0:
                    shift = long_shift / 10000.0
                else:
                    # linear interpolation
                    frac = (years - 2.0) / 8.0
                    shift = ((1.0 - frac) * short_shift + frac * long_shift) / 10000.0
            else:
                # Parallel rate and spread widening shift
                if bond_type in ("treasury", "tips"):
                    shift = t_shift
                elif bond_type == "municipal":
                    shift = t_shift + m_shift
                else:  # corporate
                    shift = t_shift + c_shift

            # Quadratic price approximation: dP/P ≈ -D_mod * dy + 0.5 * C * dy^2
            duration_effect = -md * shift
            convexity_effect = 0.5 * cx * (shift**2)
            bond_impact = duration_effect + convexity_effect

            portfolio_impact = bond_impact * w
            total_portfolio_value_impact += portfolio_impact

            details.append(
                {
                    "name": h.get("name", h.get("issuer", "Unknown")),
                    "weight": round(w * 100.0, 4),
                    "duration": md,
                    "yield_shift_bps": round(shift * 10000.0, 1),
                    "bond_impact_pct": round(bond_impact * 100.0, 4),
                    "portfolio_impact_contribution_pct": round(
                        portfolio_impact * 100.0, 4
                    ),
                }
            )

        return {
            "scenario_name": sc["name"],
            "description": sc["description"],
            "portfolio_impact_pct": round(total_portfolio_value_impact * 100.0, 4),
            "direction": "loss" if total_portfolio_value_impact < 0 else "gain",
            "bonds": details,
        }

    @staticmethod
    def run_stress_suite(holdings: List[Dict]) -> Dict[str, Dict]:
        """
        Run all stress tests on a portfolio and return a comparison dictionary.
        """
        suite_results = {}
        for sc_id in StressEngine.CRISIS_SCENARIOS:
            suite_results[sc_id] = StressEngine.calculate_scenario_impact(
                holdings, sc_id
            )
        return suite_results
