import pytest
import numpy as np
from backend.analytics.bond_math import BondCalculator

class TestBondCalculator:
    """
    Production-grade test suite for YieldLens Bond Mathematics Engine.
    Validates core financial formulas against known theoretical values.
    """

    def test_calculate_bond_price_at_par(self):
        # A bond with coupon = YTM should trade at par (100)
        price = BondCalculator.calculate_bond_price(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        assert pytest.approx(price, rel=1e-5) == 100.0

    def test_calculate_bond_price_premium(self):
        # Coupon > YTM should trade at premium (> 100)
        price = BondCalculator.calculate_bond_price(
            coupon=0.06,
            ytm=0.04,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        assert price > 100.0
        # Theoretical value for 6% coupon, 4% YTM, 10Y semi-annual: ~116.35
        assert pytest.approx(price, rel=1e-4) == 116.3514

    def test_calculate_bond_price_discount(self):
        # Coupon < YTM should trade at discount (< 100)
        price = BondCalculator.calculate_bond_price(
            coupon=0.03,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        assert price < 100.0
        # Theoretical value for 3% coupon, 5% YTM, 10Y semi-annual: ~84.41
        assert pytest.approx(price, rel=1e-4) == 84.4065

    def test_calculate_ytm_newton_raphson(self):
        # If we know the price, can we find the YTM?
        price = 116.3514
        ytm = BondCalculator.calculate_ytm(
            price=price,
            coupon=0.06,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        assert pytest.approx(ytm, rel=1e-4) == 0.04

    def test_calculate_ytm_zero_coupon_approx(self):
        # Price of a zero coupon bond
        price = 60.0
        ytm = BondCalculator.calculate_ytm(
            price=price,
            coupon=0.0,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        # 100 / (1 + r/2)^20 = 60 => (1 + r/2)^20 = 1.666 => 1 + r/2 = 1.0258 => r/2 = 0.0258 => r = 0.0517
        assert pytest.approx(ytm, rel=1e-3) == 0.0517

    def test_calculate_duration(self):
        # 10Y, 5% coupon, 5% YTM
        # Macaulay duration should be less than maturity
        mac, mod = BondCalculator.calculate_duration(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        # Theoretical: Mac ~ 7.98, Mod ~ 7.79
        assert pytest.approx(mac, rel=1e-3) == 7.9894
        assert pytest.approx(mod, rel=1e-3) == 7.7946

    def test_calculate_convexity(self):
        # 10Y, 5% coupon, 5% YTM
        conv = BondCalculator.calculate_convexity(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100.0
        )
        # Theoretical: ~ 74.9
        assert pytest.approx(conv, rel=1e-2) == 74.9

    def test_tax_equivalent_yield(self):
        tey = BondCalculator.calculate_tax_equivalent_yield(0.04, 0.35)
        # 0.04 / (1 - 0.35) = 0.0615
        assert pytest.approx(tey, rel=1e-4) == 0.061538

    def test_real_yield(self):
        real = BondCalculator.calculate_real_yield(0.05, 0.03)
        # (1.05 / 1.03) - 1 = 0.019417
        assert pytest.approx(real, rel=1e-4) == 0.019417

    def test_dv01(self):
        dv01 = BondCalculator.calculate_dv01(mod_duration=7.7946, price=100.0)
        # 7.7946 * 100 * 0.0001 = 0.077946
        assert pytest.approx(dv01, rel=1e-5) == 0.077946

    def test_risk_score_calculation(self):
        # AAA bond, low duration, low spread
        score_safe = BondCalculator.calculate_risk_score(
            ytm=0.02,
            duration=2.0,
            credit_rating="AAA",
            spread=20
        )
        
        # CCC bond, high duration, high spread
        score_risky = BondCalculator.calculate_risk_score(
            ytm=0.15,
            duration=15.0,
            credit_rating="CCC",
            spread=800
        )
        
        assert score_safe < score_risky
        assert 0 <= score_safe <= 100
        assert 0 <= score_risky <= 100

    def test_scenario_analysis(self):
        results = BondCalculator.scenario_analysis(
            coupon=0.05,
            current_ytm=0.05,
            years_to_maturity=10,
            yield_scenarios=[0.04, 0.06]
        )
        
        assert "current_price" in results
        assert results["current_price"] == 100.0
        assert len(results["scenarios"]) == 2
        
        # Scenario 1: Yield drops to 4% (price should rise)
        assert results["scenarios"][0]["price"] > 100.0
        # Scenario 2: Yield rises to 6% (price should fall)
        assert results["scenarios"][1]["price"] < 100.0

    def test_accrued_interest(self):
        # 5% coupon, semi-annual, 91 days since last coupon
        # Accrued = (0.05 * 100 / 2) * (91 / 182.6) approx 2.5 * 0.5 = 1.25
        accrued = BondCalculator.calculate_accrued_interest(
            coupon_rate=0.05,
            last_coupon_date="2024-01-01",
            settlement_date="2024-04-01",
            frequency=2,
            face_value=100.0
        )
        # 91 days / (365.25/2) = 91 / 182.625 = 0.498
        # 2.5 * 0.498 = 1.245
        assert pytest.approx(accrued, rel=1e-2) == 1.245
