"""
YieldLens Portfolio Engine
Institutional portfolio analytics, weighted average metrics, and exposure attributions.
"""

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from utils.helpers import safe_float


class PortfolioEngine:
    """Rigorous fixed-income portfolio analysis and attribution engine."""

    @staticmethod
    def calculate_weighted_average(holdings: List[Dict], metric_key: str) -> float:
        """
        Calculate the weighted average of a specific metric across holdings.
        """
        total_weight = sum(safe_float(h.get("weight", 0.0)) for h in holdings)
        if total_weight <= 0.0:
            return 0.0

        weighted_sum = sum(
            safe_float(h.get(metric_key, 0.0)) * safe_float(h.get("weight", 0.0))
            for h in holdings
        )
        return round(weighted_sum / total_weight, 6)

    @staticmethod
    def calculate_portfolio_exposures(
        holdings: List[Dict],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate weighted concentration exposures by rating, sector (type), issuer, and geographic location.
        """
        exposures = {"credit": {}, "sector": {}, "issuer": {}, "geographic": {}}

        total_weight = sum(safe_float(h.get("weight", 0.0)) for h in holdings) or 1.0

        for h in holdings:
            weight = safe_float(h.get("weight", 0.0)) / total_weight

            # Rating exposure
            rating = h.get("rating") or "BBB"
            exposures["credit"][rating] = exposures["credit"].get(rating, 0.0) + weight

            # Sector (type) exposure
            sector = h.get("type") or h.get("sector") or "corporate"
            exposures["sector"][sector] = exposures["sector"].get(sector, 0.0) + weight

            # Issuer exposure
            issuer = h.get("issuer") or "Unknown Issuer"
            exposures["issuer"][issuer] = exposures["issuer"].get(issuer, 0.0) + weight

            # Geographic exposure (state or country)
            state = h.get("state") or "US"
            exposures["geographic"][state] = (
                exposures["geographic"].get(state, 0.0) + weight
            )

        # Round allocations
        for cat in exposures:
            for key in exposures[cat]:
                exposures[cat][key] = round(
                    exposures[cat][key] * 100.0, 4
                )  # return in pct

        return exposures

    @staticmethod
    def calculate_portfolio_growth(
        initial_value: float, daily_returns: List[float]
    ) -> List[float]:
        """
        Calculate cumulative asset growth curve.
        """
        growth = [initial_value]
        current = initial_value
        for r in daily_returns:
            current *= 1.0 + r
            growth.append(round(current, 2))
        return growth

    @staticmethod
    def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        """
        if initial_value <= 0.0 or final_value <= 0.0 or years <= 0.0:
            return 0.0
        cagr = (final_value / initial_value) ** (1.0 / years) - 1.0
        return round(cagr, 6)

    @staticmethod
    def calculate_risk_contribution(
        weights: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Calculate exact Marginal Contribution to Risk (MCTR) and Risk Contribution (RC) for each holding.

        Formula:
          MCTR = (Cov * w) / sigma_p
          RC = w * MCTR
        """
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_vol = math.sqrt(portfolio_variance)

        if portfolio_vol <= 0.0:
            return np.zeros(len(weights))

        mctr = np.dot(cov_matrix, weights) / portfolio_vol
        rc = weights * mctr

        # Express relative risk contributions (sum to 1)
        relative_rc = rc / portfolio_vol
        return np.round(relative_rc, 6)

    @staticmethod
    def calculate_full_portfolio_analytics(
        holdings: List[Dict], historical_returns: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Run aggregate portfolio attribution, cash flows, and exposures.
        """
        if not holdings:
            return {
                "portfolio_yield": 0.0,
                "portfolio_duration": 0.0,
                "portfolio_convexity": 0.0,
                "weighted_coupon": 0.0,
                "WAM": 0.0,
                "exposures": {
                    "credit": {},
                    "sector": {},
                    "issuer": {},
                    "geographic": {},
                },
                "risk_contribution": [],
            }

        # 1. Base Weighted Metrics
        port_yield = PortfolioEngine.calculate_weighted_average(holdings, "ytm")
        port_dur = PortfolioEngine.calculate_weighted_average(
            holdings, "modified_duration"
        )
        port_convexity = PortfolioEngine.calculate_weighted_average(
            holdings, "convexity"
        )
        port_coupon = PortfolioEngine.calculate_weighted_average(
            holdings, "coupon_rate"
        )
        port_wam = PortfolioEngine.calculate_weighted_average(
            holdings, "years_to_maturity"
        )

        # 2. Exposures
        exposures = PortfolioEngine.calculate_portfolio_exposures(holdings)

        # 3. Risk Contribution (if historical returns matrix is provided)
        risk_contributions = []
        if historical_returns is not None and len(holdings) > 1:
            try:
                # Align weights to covariance columns
                asset_ids = [
                    h.get("bond_id") or h.get("id") or str(i)
                    for i, h in enumerate(holdings)
                ]
                weights = np.array([safe_float(h.get("weight", 0.0)) for h in holdings])
                weights /= np.sum(weights)  # normalise

                # Covariance matrix from daily returns
                cov_matrix = (
                    historical_returns[asset_ids].cov().values * 252.0
                )  # Annualized
                relative_rc = PortfolioEngine.calculate_risk_contribution(
                    weights, cov_matrix
                )

                for i, h in enumerate(holdings):
                    risk_contributions.append(
                        {
                            "id": asset_ids[i],
                            "name": h.get("name", h.get("issuer", "Unknown")),
                            "weight": round(weights[i] * 100.0, 4),
                            "risk_contribution_pct": round(relative_rc[i] * 100.0, 4),
                        }
                    )
            except Exception as e:
                # Downside fallback to simple duration-weighted risk allocations
                pass

        if not risk_contributions:
            # Fallback to duration-weighted risk allocation
            weights = np.array([safe_float(h.get("weight", 0.0)) for h in holdings])
            weights_sum = np.sum(weights) or 1.0
            weights /= weights_sum
            durations = np.array(
                [safe_float(h.get("modified_duration", 1.0)) for h in holdings]
            )
            dur_weights = weights * durations
            dur_weights_sum = np.sum(dur_weights) or 1.0
            relative_rc = dur_weights / dur_weights_sum
            for i, h in enumerate(holdings):
                risk_contributions.append(
                    {
                        "id": h.get("bond_id") or h.get("id") or str(i),
                        "name": h.get("name", h.get("issuer", "Unknown")),
                        "weight": round(weights[i] * 100.0, 4),
                        "risk_contribution_pct": round(relative_rc[i] * 100.0, 4),
                    }
                )

        return {
            "portfolio_yield": round(port_yield, 4),
            "portfolio_duration": round(port_dur, 4),
            "portfolio_convexity": round(port_convexity, 4),
            "weighted_coupon": round(port_coupon, 4),
            "WAM": round(port_wam, 2),
            "exposures": exposures,
            "risk_contribution": risk_contributions,
        }
