import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest
import numpy as np
import pandas as pd
from analytics.yield_engine import YieldEngine
from analytics.portfolio_engine import PortfolioEngine
from analytics.risk_engine import RiskEngine
from analytics.stress_engine import StressEngine
from analytics.allocation_engine import AllocationEngine
from analytics.quant_engine import QuantEngine
from analytics.backtest_engine import BacktestEngine

class TestQuantMathPatch:

    def test_yield_engine_pricing_and_ytm(self):
        # 1. Price at par
        price = YieldEngine.calculate_bond_price(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10.0,
            frequency=2,
            face_value=100.0
        )
        assert abs(price - 100.0) <= 0.001 # 0.001% tolerance check

        # 2. Solver YTM recovery
        target_ytm = 0.045
        price_prem = YieldEngine.calculate_bond_price(0.06, target_ytm, 8.0, 2, 100.0)
        solved_ytm = YieldEngine.calculate_ytm(price_prem, 0.06, 8.0, 2, 100.0)
        
        # Must be strictly under 0.001% error limit
        relative_error = abs(solved_ytm - target_ytm) / target_ytm
        assert relative_error <= 0.00001

    def test_yield_engine_ytc_and_ytw(self):
        # 5% coupon, 10Y maturity, but callable in 5 years at 102
        price = 105.0
        ytm = YieldEngine.calculate_ytm(price, 0.05, 10.0, 2, 100.0)
        ytc = YieldEngine.calculate_ytc(price, 0.05, 5.0, 102.0, 2, 100.0)
        ytw = YieldEngine.calculate_ytw(price, 0.05, 10.0, [{"years": 5.0, "price": 102.0}], 2, 100.0)

        assert ytw == min(ytm, ytc)

    def test_yield_engine_duration_convexity(self):
        # Verify Macaulay and Modified durations
        metrics = YieldEngine.calculate_duration_metrics(
            coupon=0.06,
            ytm=0.04,
            years_to_maturity=10.0,
            frequency=2,
            face_value=100.0
        )
        # Expected Modified Duration ~ 7.425
        assert metrics["modified_duration"] > 0
        assert metrics["convexity"] > 0

    def test_accrued_interest_day_counts(self):
        # ACT/360
        acc_360 = YieldEngine.calculate_accrued_interest(
            coupon_rate=0.06,
            last_coupon_date="2026-01-01",
            settlement_date="2026-03-01", # ~59 days
            frequency=2,
            face_value=100.0,
            day_count="ACT/360"
        )
        assert acc_360 > 0.0

    def test_spot_and_forward_rates_bootstrapping(self):
        maturities = [1.0, 2.0, 3.0]
        yields = [4.0, 4.5, 4.8]
        
        spots = YieldEngine.bootstrap_spot_curve(maturities, yields)
        assert len(spots) == 3
        assert spots[0] == 4.0
        assert spots[1] > spots[0] # upward sloping

        forwards = YieldEngine.calculate_forward_rates(maturities, spots)
        assert len(forwards) == 2
        assert forwards[0]["forward_rate"] > 0

    def test_portfolio_engine_weighted_statistics(self):
        holdings = [
            {"weight": 0.4, "ytm": 0.04, "modified_duration": 4.0, "convexity": 20.0, "years_to_maturity": 5.0},
            {"weight": 0.6, "ytm": 0.06, "modified_duration": 6.0, "convexity": 40.0, "years_to_maturity": 8.0}
        ]
        port_yield = PortfolioEngine.calculate_weighted_average(holdings, "ytm")
        # 0.4 * 0.04 + 0.6 * 0.06 = 0.052
        assert abs(port_yield - 0.052) <= 1e-6

        port_dur = PortfolioEngine.calculate_weighted_average(holdings, "modified_duration")
        # 0.4 * 4.0 + 0.6 * 6.0 = 5.2
        assert abs(port_dur - 5.2) <= 1e-6

    def test_risk_engine_volatility_and_var(self):
        np.random.seed(42)
        returns = pd.DataFrame({
            "asset1": np.random.normal(0.0002, 0.01, 100),
            "asset2": np.random.normal(0.0003, 0.012, 100)
        })
        
        cov = RiskEngine.calculate_covariance_matrix(returns, annualize=True)
        assert cov.shape == (2, 2)
        
        corr = RiskEngine.calculate_correlation_matrix(returns)
        assert corr.shape == (2, 2)
        assert abs(corr.iloc[0, 0] - 1.0) <= 1e-6

        weights = np.array([0.5, 0.5])
        vol = RiskEngine.calculate_portfolio_volatility(weights, cov.values)
        assert vol > 0.0

    def test_allocation_engine_parity(self):
        cov = np.array([
            [0.04, 0.01],
            [0.01, 0.09]
        ])
        weights = AllocationEngine.calculate_risk_parity_weights(cov)
        assert len(weights) == 2
        assert abs(np.sum(weights) - 1.0) <= 1e-5
        # Higher variance asset should have lower weight in risk parity
        assert weights[1] < weights[0]
