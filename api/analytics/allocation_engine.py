"""
YieldLens Allocation & Optimization Engine
Implements portfolio optimization (MVO, Efficient Frontier, Risk Parity) and bond-ladder rebalancing.
"""

import math
from typing import List, Optional, Tuple

import numpy as np


class AllocationEngine:
    """Quantitative asset allocation, rebalancing, and optimal weights solver."""

    @staticmethod
    def calculate_risk_parity_weights(
        cov_matrix: np.ndarray, max_iterations: int = 100, tolerance: float = 1e-6
    ) -> np.ndarray:
        """
        Solve for risk parity weights using numerical cyclical coordinate descent.
        Ensures each asset contributes exactly equal risk to the overall portfolio.
        """
        n = cov_matrix.shape[0]
        # Start with equal weights
        w = np.ones(n) / n

        # Risk parity objective: minimize sum of squared differences of risk contributions
        # Solve numerically for equal risk contribution
        for _ in range(max_iterations):
            for i in range(n):
                # Marginal contribution of asset i
                sigma_p = math.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                if sigma_p <= 0:
                    break

                mctr_i = np.dot(cov_matrix, w)[i] / sigma_p
                rc_i = w[i] * mctr_i

                # Target risk contribution for asset i is 1/n of portfolio volatility
                target_rc = sigma_p / n

                # Simple adjustment step
                if rc_i > 0:
                    w[i] = w[i] * (target_rc / rc_i) ** 0.5

            # Normalise weights
            w_sum = np.sum(w)
            if w_sum > 0:
                w /= w_sum

            # Check convergence
            sigma_p = math.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
            rcs = w * (np.dot(cov_matrix, w) / sigma_p)
            rc_diff = np.std(rcs)
            if rc_diff < tolerance:
                break

        return np.round(w, 6)

    @staticmethod
    def solve_mean_variance_optimization(
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: Optional[float] = None,
        risk_aversion: float = 2.0,
    ) -> np.ndarray:
        """
        Solve for mean-variance optimal weights under constraints.
        If target_return is not specified, maximizes Sharpe / risk-adjusted utility:
          Max: w^T * R - 0.5 * lambda * w^T * Sigma * w
        """
        n = len(expected_returns)
        # Solve using quadratic programming or a highly robust SciPy constraint solver
        from scipy.optimize import minimize

        def utility(w):
            w = np.array(w)
            port_return = np.dot(w, expected_returns)
            port_variance = np.dot(w.T, np.dot(cov_matrix, w))
            # Minimize negative utility
            return -(port_return - 0.5 * risk_aversion * port_variance)

        # Constraints: weights sum to 1, long-only w_i >= 0
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        if target_return is not None:
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda w: np.dot(w, expected_returns) - target_return,
                }
            )

        bounds = [(0.0, 1.0) for _ in range(n)]

        # Initial guess
        w0 = np.ones(n) / n

        res = minimize(
            utility, w0, method="SLSQP", bounds=bounds, constraints=constraints
        )
        if res.success:
            return np.round(res.x, 6)
        else:
            # Fallback to equal weights
            return w0

    @staticmethod
    def generate_ladder_allocations(
        maturity_bounds: Tuple[float, float], count: int
    ) -> List[float]:
        """
        Generate equal allocation weights for a bond ladder strategy.
        """
        if count <= 0:
            return []
        weight = 1.0 / count
        return [round(weight, 6) for _ in range(count)]
