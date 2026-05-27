"""
YieldLens Risk Engine
Institutional portfolio risk modeling: Volatility, Covariance, Correlation, advanced VaR/CVaR,
Sharpe/Sortino/Treynor/Information ratios, and market regressions (Alpha/Beta).
"""

import math
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from utils.helpers import rating_to_score, safe_float


class RiskEngine:
    """Rigorous risk and volatility modeling engine for fixed-income assets and portfolios."""

    # ------------------------------------------------------------------ #
    #  Basic Volatility and Matrices
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_covariance_matrix(
        returns: pd.DataFrame, annualize: bool = True
    ) -> pd.DataFrame:
        """
        Calculate annualized covariance matrix of daily asset returns.
        """
        cov = returns.cov()
        if annualize:
            cov = cov * 252.0
        return cov.round(6)

    @staticmethod
    def calculate_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix of daily asset returns.
        """
        return returns.corr().round(6)

    @staticmethod
    def calculate_portfolio_volatility(
        weights: np.ndarray, cov_matrix: np.ndarray
    ) -> float:
        """
        Calculate portfolio volatility using modern portfolio theory:
          sigma_p = sqrt(w^T * Sigma * w)
        """
        variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        return round(math.sqrt(max(variance, 0.0)), 6)

    # ------------------------------------------------------------------ #
    #  Value at Risk (VaR) & Conditional VaR (CVaR)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_historical_var_cvar(
        returns: np.ndarray, confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate Historical Value at Risk (VaR) and Conditional VaR (CVaR).
        Returns both as positive decimals.
        """
        if len(returns) < 5:
            return 0.0, 0.0

        sorted_returns = np.sort(returns)
        idx = int(math.floor((1 - confidence) * len(sorted_returns)))
        idx = max(min(idx, len(sorted_returns) - 1), 0)

        var = -sorted_returns[idx]
        cvar = -np.mean(sorted_returns[: idx + 1])

        return round(max(var, 0.0), 6), round(max(cvar, 0.0), 6)

    @staticmethod
    def calculate_parametric_var_cvar(
        mean: float, std: float, confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate Parametric (Variance-Covariance) VaR and CVaR assuming a normal distribution.
        Returns both as positive decimals.
        """
        from scipy.stats import norm

        alpha = 1.0 - confidence
        z_score = norm.ppf(confidence)

        var = -(mean - z_score * std)

        # CVaR = -mean + std * (pdf(z_score) / alpha)
        pdf_z = norm.pdf(z_score)
        cvar = -(mean - std * (pdf_z / alpha))

        return round(max(var, 0.0), 6), round(max(cvar, 0.0), 6)

    @staticmethod
    def calculate_monte_carlo_var_cvar(
        mean: float, std: float, confidence: float = 0.95, simulations: int = 10000
    ) -> Tuple[float, float]:
        """
        Calculate Monte Carlo simulated Value at Risk (VaR) and Conditional VaR (CVaR).
        """
        np.random.seed(42)  # deterministic seed
        sim_returns = np.random.normal(mean, std, simulations)
        return RiskEngine.calculate_historical_var_cvar(sim_returns, confidence)

    # ------------------------------------------------------------------ #
    #  Advanced Ratios & Regressions
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_sharpe_ratio(
        return_rate: float, risk_free_rate: float, volatility: float
    ) -> float:
        """
        Calculate the Sharpe Ratio.
        """
        if volatility <= 0.0:
            return 0.0
        return round((return_rate - risk_free_rate) / volatility, 6)

    @staticmethod
    def calculate_sortino_ratio(
        returns: np.ndarray, return_rate: float, risk_free_rate: float
    ) -> float:
        """
        Calculate the Sortino Ratio using downside semi-deviation.
        """
        excess_returns = returns - (risk_free_rate / 252.0)  # daily excess
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) < 2:
            return 0.0

        downside_deviation = math.sqrt(np.mean(downside_returns**2)) * math.sqrt(252.0)
        if downside_deviation <= 0.0:
            return 0.0

        return round((return_rate - risk_free_rate) / downside_deviation, 6)

    @staticmethod
    def calculate_treynor_ratio(
        return_rate: float, risk_free_rate: float, beta: float
    ) -> float:
        """
        Calculate Treynor Ratio.
        """
        if beta == 0.0:
            return 0.0
        return round((return_rate - risk_free_rate) / beta, 6)

    @staticmethod
    def calculate_information_ratio(
        portfolio_returns: np.ndarray, benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate Information Ratio (Excess Return divided by Tracking Error).
        """
        if (
            len(portfolio_returns) != len(benchmark_returns)
            or len(portfolio_returns) < 5
        ):
            return 0.0

        active_returns = portfolio_returns - benchmark_returns
        tracking_error = np.std(active_returns, ddof=1) * math.sqrt(252.0)

        if tracking_error <= 0.0:
            return 0.0

        ann_active_return = np.mean(active_returns) * 252.0
        return round(ann_active_return / tracking_error, 6)

    @staticmethod
    def calculate_alpha_beta(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        risk_free_rate: float = 0.04,
    ) -> Tuple[float, float]:
        """
        Calculate Alpha (Jensen's Alpha) and Beta via OLS regression.
        """
        import statsmodels.api as sm

        if (
            len(portfolio_returns) != len(benchmark_returns)
            or len(portfolio_returns) < 5
        ):
            return 0.0, 1.0

        # Annualized arithmetic conversions
        y = portfolio_returns - (risk_free_rate / 252.0)
        x = benchmark_returns - (risk_free_rate / 252.0)

        # OLS regression
        x_const = sm.add_constant(x)
        model = sm.OLS(y, x_const).fit()

        alpha_daily = model.params[0]
        beta = model.params[1]

        # Annualize alpha
        alpha = alpha_daily * 252.0
        return round(alpha, 6), round(beta, 6)

    @staticmethod
    def calculate_maximum_drawdown(returns: np.ndarray) -> float:
        """
        Calculate the absolute Maximum Drawdown. Returns positive number (percentage).
        """
        if len(returns) == 0:
            return 0.0

        cumulative = np.insert(np.cumprod(1.0 + returns), 0, 1.0)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (running_max - cumulative) / running_max
        return round(float(np.max(drawdowns)) * 100.0, 4)

    # ------------------------------------------------------------------ #
    #  Main Aggregate Wrapper
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_portfolio_risk(
        holdings: list[dict], daily_returns: Optional[pd.DataFrame] = None
    ) -> dict:
        """
        Compute full set of portfolio-level mathematical risk and volatility indicators.
        """
        total_weight = sum(safe_float(h.get("weight", 0)) for h in holdings) or 1.0

        # Weighted duration/yield
        port_duration = (
            sum(
                safe_float(h.get("modified_duration", 0))
                * safe_float(h.get("weight", 0))
                for h in holdings
            )
            / total_weight
        )

        port_yield = (
            sum(
                safe_float(h.get("ytm", 0)) * safe_float(h.get("weight", 0))
                for h in holdings
            )
            / total_weight
        )

        port_spread = (
            sum(
                safe_float(h.get("spread_bps", 0)) * safe_float(h.get("weight", 0))
                for h in holdings
            )
            / total_weight
        )

        # Default credit and concentration metrics
        ratings = {
            h.get("rating", "BBB"): safe_float(h.get("weight", 0)) for h in holdings
        }
        credit_score = RiskEngine.credit_risk_score(ratings)

        weights = [safe_float(h.get("weight", 0)) for h in holdings]
        conc_risk = RiskEngine.concentration_risk(weights)

        # Advanced stats: VaR, Volatility
        var_95 = 0.0
        cvar_95 = 0.0
        portfolio_vol = 0.0

        if daily_returns is not None and len(holdings) > 1:
            try:
                # Weights alignment
                asset_ids = [
                    h.get("bond_id") or h.get("id") or str(i)
                    for i, h in enumerate(holdings)
                ]
                w = np.array([safe_float(h.get("weight", 0.0)) for h in holdings])
                w /= np.sum(w)  # normalise

                # Portfolio returns vector
                sub_returns = daily_returns[asset_ids]
                port_daily_returns = np.dot(sub_returns.values, w)

                # Volatility
                cov = RiskEngine.calculate_covariance_matrix(
                    sub_returns, annualize=True
                )
                portfolio_vol = RiskEngine.calculate_portfolio_volatility(w, cov.values)

                # VaR / CVaR
                var_95, cvar_95 = RiskEngine.calculate_historical_var_cvar(
                    port_daily_returns, 0.95
                )
                # Express as pct
                var_95 *= 100.0
                cvar_95 *= 100.0
            except Exception:
                pass

        if portfolio_vol == 0.0:
            # Fallback to duration-based estimates
            portfolio_vol = (
                port_duration * 0.015
            )  # approximation (1.5% volatility scaling)
            var_95 = port_duration * 0.0005 * 1.645 * 100
            cvar_95 = var_95 * 1.25

        # Overall rating
        raw_risk = (
            credit_score * 0.3
            + conc_risk * 100 * 0.2
            + min(port_duration * 5, 50) * 0.3
            + min(port_spread / 10, 30) * 0.2
        )
        if raw_risk < 20:
            risk_rating = "Low"
        elif raw_risk < 45:
            risk_rating = "Moderate"
        elif raw_risk < 70:
            risk_rating = "High"
        else:
            risk_rating = "Very High"

        return {
            "portfolio_duration": round(port_duration, 4),
            "portfolio_yield": round(port_yield * 100, 4),
            "portfolio_spread_bps": round(port_spread, 2),
            "credit_risk_score": round(credit_score, 2),
            "concentration_risk": round(conc_risk, 4),
            "duration_risk_1pct": round(
                -port_duration * 0.01 * 100, 4
            ),  # Parallel 1% shift loss
            "volatility_pct": round(portfolio_vol * 100.0, 4),
            "var_95_pct": round(var_95, 4),
            "cvar_95_pct": round(cvar_95, 4),
            "risk_rating": risk_rating,
            "holding_count": len(holdings),
        }

    @staticmethod
    def credit_risk_score(ratings_distribution: dict[str, float]) -> float:
        """
        Compute weighted credit risk score (0-100).
        """
        if not ratings_distribution:
            return 50.0
        total_weight = sum(ratings_distribution.values()) or 1.0
        weighted_quality = (
            sum(
                rating_to_score(rating) * weight
                for rating, weight in ratings_distribution.items()
            )
            / total_weight
        )
        return round(100.0 - weighted_quality, 2)

    @staticmethod
    def concentration_risk(weights: list[float]) -> float:
        """
        Compute Herfindahl-Hirschman Index concentration (0-1).
        """
        if not weights:
            return 0.0
        total = sum(weights) or 1.0
        normalised = [w / total for w in weights]
        return round(sum(w**2 for w in normalised), 4)
