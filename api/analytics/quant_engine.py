"""
YieldLens Quant Engine
The primary orchestrator class wrapping all specialized analytical fixed-income solvers.
"""

from typing import List, Optional

import pandas as pd
from analytics.allocation_engine import AllocationEngine
from analytics.portfolio_engine import PortfolioEngine
from analytics.risk_engine import RiskEngine
from analytics.stress_engine import StressEngine
from analytics.yield_engine import YieldEngine


class QuantEngine:
    """The central access point for institutional fixed-income intelligence."""

    def __init__(self):
        self.yield_engine = YieldEngine()
        self.portfolio_engine = PortfolioEngine()
        self.risk_engine = RiskEngine()
        self.stress_engine = StressEngine()
        self.allocation_engine = AllocationEngine()

    def analyze_bond(self, bond: dict) -> dict:
        """
        Run complete quant calculations on a single bond.
        """
        coupon = float(bond.get("coupon_rate", 5.0)) / 100.0
        price = float(bond.get("price", 100.0))
        face_value = float(bond.get("face_value", 100.0))
        years = float(bond.get("years_to_maturity", 10.0))
        frequency = int(bond.get("frequency", 2))

        # Exact math
        ytm = self.yield_engine.calculate_ytm(
            price, coupon, years, frequency, face_value
        )
        current_yield = self.yield_engine.calculate_current_yield = (
            coupon * face_value / price if price > 0 else 0.0
        )

        duration_data = self.yield_engine.calculate_duration_metrics(
            coupon, ytm, years, frequency, face_value
        )
        eff_duration = self.yield_engine.calculate_effective_duration(
            coupon, ytm, years, 10.0, frequency, face_value
        )
        dv01 = self.yield_engine.calculate_dv01(
            duration_data["modified_duration"], price
        )

        # Option-Adjusted Spread (OAS)
        benchmark_ytm = 0.040  # Assume generic 10Y rate is 4.0%
        oas = 0.0
        if bond.get("callable"):
            call_strike = float(bond.get("call_price", 100.0))
            call_start = float(bond.get("call_years", 5.0))
            oas = self.yield_engine.calculate_oas_binomial_tree(
                price,
                coupon,
                years,
                benchmark_ytm,
                0.15,
                frequency,
                face_value,
                call_strike,
                call_start,
            )
        else:
            # For non-callable bond, OAS = nominal spread
            oas = self.yield_engine.calculate_yield_spread(ytm, benchmark_ytm)

        real_yield = self.yield_engine.calculate_real_yield(
            ytm, 0.025
        )  # Assume 2.5% inflation
        tax_equiv = None
        if bond.get("tax_exempt"):
            tax_equiv = self.yield_engine.calculate_tax_equivalent_yield(ytm, 0.37)

        return {
            "ytm": round(ytm * 100.0, 4),
            "current_yield": round(current_yield * 100.0, 4),
            "macaulay_duration": duration_data["macaulay_duration"],
            "modified_duration": duration_data["modified_duration"],
            "effective_duration": eff_duration,
            "convexity": duration_data["convexity"],
            "dv01": dv01,
            "oas_bps": oas,
            "real_yield_pct": round(real_yield * 100.0, 4),
            "tax_equivalent_yield_pct": (
                round(tax_equiv * 100.0, 4) if tax_equiv else None
            ),
        }

    def analyze_portfolio(
        self, holdings: List[dict], daily_returns: Optional[pd.DataFrame] = None
    ) -> dict:
        """
        Run complete quant calculations and risk metrics on a portfolio of holdings.
        """
        # Run portfolio calculations
        port_data = self.portfolio_engine.calculate_full_portfolio_analytics(
            holdings, daily_returns
        )
        # Run risk metrics
        risk_data = self.risk_engine.calculate_portfolio_risk(holdings, daily_returns)
        # Run stress test suite
        stress_data = self.stress_engine.run_stress_suite(holdings)

        # Merge results
        merged_results = {**port_data, **risk_data}
        merged_results["stress_scenarios"] = stress_data

        return merged_results
