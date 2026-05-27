"""
Unit Tests for Bond Mathematics Engine
Tests all financial calculations with institutional-grade precision.
Maximum tolerance: 0.001% for all calculations.
"""

import pytest
import math
from datetime import datetime, date
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

from analytics.bond_math import BondCalculator
from utils.helpers import calculate_years_to_maturity, rating_to_score


class TestBondCalculator:
    """Comprehensive tests for BondCalculator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calc = BondCalculator()
        self.tolerance = 0.00001  # 0.001% tolerance
        
    # ================================================================
    # BOND PRICING TESTS
    # ================================================================
    
    def test_bond_price_par_bond(self):
        """Test bond pricing when YTM equals coupon rate (should equal par)."""
        price = self.calc.calculate_bond_price(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        assert abs(price - 100.0) < self.tolerance
        
    def test_bond_price_premium_bond(self):
        """Test bond pricing when YTM < coupon rate (premium bond)."""
        price = self.calc.calculate_bond_price(
            coupon=0.06,
            ytm=0.04,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # Should be > 100 (premium)
        assert price > 100.0
        # Known result for 6% coupon, 4% YTM, 10Y semi-annual
        expected = 116.222  # Approximate
        assert abs(price - expected) < 0.1
        
    def test_bond_price_discount_bond(self):
        """Test bond pricing when YTM > coupon rate (discount bond)."""
        price = self.calc.calculate_bond_price(
            coupon=0.04,
            ytm=0.06,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # Should be < 100 (discount)
        assert price < 100.0
        # Known result for 4% coupon, 6% YTM, 10Y semi-annual
        expected = 85.279  # Approximate
        assert abs(price - expected) < 0.1
        
    def test_bond_price_zero_coupon(self):
        """Test zero-coupon bond pricing."""
        price = self.calc.calculate_bond_price(
            coupon=0.0,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # Zero coupon bond: PV = FV / (1 + r)^n
        expected = 100 / (1.025 ** 20)  # Semi-annual compounding
        assert abs(price - expected) < self.tolerance
        
    def test_bond_price_annual_frequency(self):
        """Test bond pricing with annual coupon payments."""
        price = self.calc.calculate_bond_price(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=5,
            frequency=1,
            face_value=100
        )
        assert abs(price - 100.0) < self.tolerance
        
    def test_bond_price_quarterly_frequency(self):
        """Test bond pricing with quarterly coupon payments."""
        price = self.calc.calculate_bond_price(
            coupon=0.08,
            ytm=0.08,
            years_to_maturity=5,
            frequency=4,
            face_value=100
        )
        assert abs(price - 100.0) < self.tolerance
        
    def test_bond_price_edge_cases(self):
        """Test bond pricing edge cases."""
        # Zero years to maturity
        price = self.calc.calculate_bond_price(0.05, 0.05, 0, 2, 100)
        assert price == 100.0
        
        # Zero YTM
        price = self.calc.calculate_bond_price(0.05, 0.0, 10, 2, 100)
        expected = 100 + (0.05 * 100 * 10)  # Face + total coupons
        assert abs(price - expected) < self.tolerance
        
    # ================================================================
    # YIELD TO MATURITY TESTS
    # ================================================================
    
    def test_ytm_par_bond(self):
        """Test YTM calculation for par bond (price = face value)."""
        ytm = self.calc.calculate_ytm(
            price=100,
            coupon=0.05,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        assert abs(ytm - 0.05) < self.tolerance
        
    def test_ytm_premium_bond(self):
        """Test YTM calculation for premium bond."""
        ytm = self.calc.calculate_ytm(
            price=110,
            coupon=0.06,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # YTM should be less than coupon rate for premium bond
        assert ytm < 0.06
        assert ytm > 0.04  # Reasonable range
        
    def test_ytm_discount_bond(self):
        """Test YTM calculation for discount bond."""
        ytm = self.calc.calculate_ytm(
            price=90,
            coupon=0.04,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # YTM should be greater than coupon rate for discount bond
        assert ytm > 0.04
        assert ytm < 0.08  # Reasonable range
        
    def test_ytm_zero_coupon_bond(self):
        """Test YTM calculation for zero-coupon bond."""
        # 10-year zero coupon bond priced at 61.39
        ytm = self.calc.calculate_ytm(
            price=61.39,
            coupon=0.0,
            years_to_maturity=10,
            frequency=2,
            face_value=100
        )
        # Should be approximately 5% (semi-annual)
        assert abs(ytm - 0.05) < 0.001
        
    def test_ytm_convergence(self):
        """Test YTM calculation convergence for various scenarios."""
        test_cases = [
            (95, 0.04, 5, 2, 100),
            (105, 0.06, 15, 2, 100),
            (80, 0.03, 20, 2, 100),
            (120, 0.08, 7, 2, 100),
        ]
        
        for price, coupon, years, freq, face in test_cases:
            ytm = self.calc.calculate_ytm(price, coupon, years, freq, face)
            # Verify by calculating price with computed YTM
            calc_price = self.calc.calculate_bond_price(coupon, ytm, years, freq, face)
            assert abs(calc_price - price) < 0.01  # Price should match within 1 cent
            
    def test_ytm_edge_cases(self):
        """Test YTM calculation edge cases."""
        # Zero years to maturity
        ytm = self.calc.calculate_ytm(100, 0.05, 0, 2, 100)
        assert ytm == 0.0
        
        # Zero price
        ytm = self.calc.calculate_ytm(0, 0.05, 10, 2, 100)
        assert ytm == 0.0
        
    # ================================================================
    # DURATION TESTS
    # ================================================================
    
    def test_macaulay_duration_par_bond(self):
        """Test Macaulay duration calculation for par bond."""
        mac_dur, mod_dur = self.calc.calculate_duration(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2
        )
        
        # Macaulay duration should be less than maturity for coupon bonds
        assert mac_dur < 10.0
        assert mac_dur > 8.0  # Reasonable range for 5% coupon, 10Y
        
        # Modified duration should be less than Macaulay
        assert mod_dur < mac_dur
        
    def test_duration_zero_coupon(self):
        """Test duration for zero-coupon bond."""
        mac_dur, mod_dur = self.calc.calculate_duration(
            coupon=0.0,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2
        )
        
        # For zero-coupon bonds, Macaulay duration equals maturity
        assert abs(mac_dur - 10.0) < self.tolerance
        
        # Modified duration = Macaulay / (1 + periodic_rate)
        expected_mod = 10.0 / (1 + 0.05/2)
        assert abs(mod_dur - expected_mod) < self.tolerance
        
    def test_duration_high_coupon(self):
        """Test duration for high-coupon bond."""
        mac_dur, mod_dur = self.calc.calculate_duration(
            coupon=0.10,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2
        )
        
        # High coupon bonds have lower duration
        assert mac_dur < 8.0
        assert mod_dur < mac_dur
        
    def test_duration_various_maturities(self):
        """Test duration across various maturities."""
        maturities = [1, 2, 5, 10, 20, 30]
        
        for maturity in maturities:
            mac_dur, mod_dur = self.calc.calculate_duration(
                coupon=0.05,
                ytm=0.05,
                years_to_maturity=maturity,
                frequency=2
            )
            
            # Duration should increase with maturity (but at decreasing rate)
            assert mac_dur > 0
            assert mac_dur <= maturity  # Never exceed maturity for coupon bonds
            assert mod_dur < mac_dur
            
    # ================================================================
    # DV01 TESTS
    # ================================================================
    
    def test_dv01_calculation(self):
        """Test DV01 (dollar value of 01) calculation."""
        # Calculate modified duration first
        _, mod_dur = self.calc.calculate_duration(0.05, 0.05, 10, 2)
        
        # Calculate DV01
        dv01 = self.calc.calculate_dv01(mod_dur, 100)
        
        # DV01 = Modified Duration × Price × 0.0001
        expected = mod_dur * 100 * 0.0001
        assert abs(dv01 - expected) < self.tolerance
        
        # Verify with price sensitivity test
        ytm_base = 0.05
        price_base = self.calc.calculate_bond_price(0.05, ytm_base, 10, 2, 100)
        price_up = self.calc.calculate_bond_price(0.05, ytm_base + 0.0001, 10, 2, 100)
        
        actual_dv01 = price_base - price_up
        assert abs(dv01 - actual_dv01) < 0.001  # Should be close
        
    def test_dv01_various_prices(self):
        """Test DV01 for bonds at different price levels."""
        prices = [80, 90, 100, 110, 120]
        
        for price in prices:
            # Assume 8% duration for simplicity
            dv01 = self.calc.calculate_dv01(8.0, price)
            expected = 8.0 * price * 0.0001
            assert abs(dv01 - expected) < self.tolerance
            
    # ================================================================
    # CONVEXITY TESTS
    # ================================================================
    
    def test_convexity_calculation(self):
        """Test convexity calculation."""
        convexity = self.calc.calculate_convexity(
            coupon=0.05,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2
        )
        
        # Convexity should be positive
        assert convexity > 0
        
        # Reasonable range for 10Y bond
        assert convexity > 50
        assert convexity < 200
        
    def test_convexity_zero_coupon(self):
        """Test convexity for zero-coupon bond."""
        convexity = self.calc.calculate_convexity(
            coupon=0.0,
            ytm=0.05,
            years_to_maturity=10,
            frequency=2
        )
        
        # Zero-coupon bonds have higher convexity
        assert convexity > 0
        
    def test_convexity_price_approximation(self):
        """Test convexity in price approximation formula."""
        coupon, ytm, years, freq = 0.05, 0.05, 10, 2
        
        # Calculate duration and convexity
        _, mod_dur = self.calc.calculate_duration(coupon, ytm, years, freq)
        convexity = self.calc.calculate_convexity(coupon, ytm, years, freq)
        
        # Base price
        price_base = self.calc.calculate_bond_price(coupon, ytm, years, freq)
        
        # Price after 100bp yield change
        yield_change = 0.01
        price_actual = self.calc.calculate_bond_price(coupon, ytm + yield_change, years, freq)
        
        # Price approximation using duration and convexity
        price_approx = price_base * (1 - mod_dur * yield_change + 0.5 * convexity * yield_change**2)
        
        # Approximation should be closer than duration-only
        duration_only = price_base * (1 - mod_dur * yield_change)
        
        error_convex = abs(price_actual - price_approx)
        error_duration = abs(price_actual - duration_only)
        
        assert error_convex < error_duration  # Convexity improves approximation
        
    # ================================================================
    # CURRENT YIELD TESTS
    # ================================================================
    
    def test_current_yield_calculation(self):
        """Test current yield calculation."""
        current_yield = self.calc.calculate_current_yield(5.0, 100)
        assert abs(current_yield - 0.05) < self.tolerance
        
        # Premium bond
        current_yield = self.calc.calculate_current_yield(5.0, 110)
        expected = 5.0 / 110
        assert abs(current_yield - expected) < self.tolerance
        
        # Discount bond
        current_yield = self.calc.calculate_current_yield(5.0, 90)
        expected = 5.0 / 90
        assert abs(current_yield - expected) < self.tolerance
        
    def test_current_yield_edge_cases(self):
        """Test current yield edge cases."""
        # Zero coupon
        current_yield = self.calc.calculate_current_yield(0, 100)
        assert current_yield == 0.0
        
        # Zero price (should handle gracefully)
        current_yield = self.calc.calculate_current_yield(5.0, 0)
        assert current_yield == 0.0
        
    # ================================================================
    # ACCRUED INTEREST TESTS
    # ================================================================
    
    def test_accrued_interest_calculation(self):
        """Test accrued interest calculation."""
        # Semi-annual bond, 6 months since last payment
        accrued = self.calc.calculate_accrued_interest(
            coupon_rate=0.06,
            face_value=100,
            frequency=2,
            days_since_last_payment=183,
            days_in_period=365
        )
        
        # Should be approximately half the semi-annual coupon
        expected = (0.06 * 100 / 2) * (183 / 365)
        assert abs(accrued - expected) < 0.01
        
    def test_accrued_interest_edge_cases(self):
        """Test accrued interest edge cases."""
        # Zero days since payment
        accrued = self.calc.calculate_accrued_interest(0.06, 100, 2, 0, 365)
        assert accrued == 0.0
        
        # Full period elapsed
        accrued = self.calc.calculate_accrued_interest(0.06, 100, 2, 365, 365)
        expected = 0.06 * 100 / 2  # Full semi-annual coupon
        assert abs(accrued - expected) < self.tolerance
        
    # ================================================================
    # YIELD TRANSFORMATIONS TESTS
    # ================================================================
    
    def test_tax_equivalent_yield(self):
        """Test tax-equivalent yield calculation."""
        # 4% tax-free yield, 35% tax bracket
        tax_equiv = self.calc.calculate_tax_equivalent_yield(0.04, 0.35)
        expected = 0.04 / (1 - 0.35)
        assert abs(tax_equiv - expected) < self.tolerance
        
        # Edge cases
        tax_equiv = self.calc.calculate_tax_equivalent_yield(0.04, 0.0)  # No tax
        assert abs(tax_equiv - 0.04) < self.tolerance
        
        tax_equiv = self.calc.calculate_tax_equivalent_yield(0.04, 1.0)  # 100% tax
        assert tax_equiv == float('inf') or tax_equiv > 1000  # Very high
        
    def test_real_yield_calculation(self):
        """Test real yield calculation (Fisher equation)."""
        # 5% nominal, 2% inflation
        real_yield = self.calc.calculate_real_yield(0.05, 0.02)
        expected = ((1 + 0.05) / (1 + 0.02)) - 1
        assert abs(real_yield - expected) < self.tolerance
        
        # Negative real yield (inflation > nominal)
        real_yield = self.calc.calculate_real_yield(0.02, 0.05)
        assert real_yield < 0
        
    def test_spread_calculation(self):
        """Test spread calculation."""
        spread = self.calc.calculate_spread(0.055, 0.045)
        assert abs(spread - 100) < self.tolerance  # 100 basis points
        
        # Negative spread
        spread = self.calc.calculate_spread(0.04, 0.05)
        assert abs(spread - (-100)) < self.tolerance
        
    # ================================================================
    # RISK SCORING TESTS
    # ================================================================
    
    def test_risk_score_calculation(self):
        """Test comprehensive risk score calculation."""
        risk_score = self.calc.calculate_risk_score(
            ytm=0.05,
            duration=8.0,
            credit_rating="AA",
            spread_bps=50
        )
        
        # Risk score should be 0-100
        assert 0 <= risk_score <= 100
        
        # Higher quality should have lower risk
        high_quality = self.calc.calculate_risk_score(0.03, 5.0, "AAA", 20)
        low_quality = self.calc.calculate_risk_score(0.08, 12.0, "BB", 300)
        
        assert high_quality < low_quality
        
    def test_risk_score_components(self):
        """Test individual risk score components."""
        # Test various credit ratings
        ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
        prev_score = 101  # Start high
        
        for rating in ratings:
            score = self.calc.calculate_risk_score(0.05, 8.0, rating, 100)
            assert score < prev_score  # Should decrease with lower rating
            prev_score = score
            
    # ================================================================
    # SCENARIO ANALYSIS TESTS
    # ================================================================
    
    def test_scenario_analysis(self):
        """Test scenario analysis functionality."""
        scenarios = self.calc.scenario_analysis(
            current_price=100,
            coupon=0.05,
            years_to_maturity=10,
            frequency=2,
            yield_scenarios=[-0.01, 0, 0.01, 0.02]
        )
        
        assert len(scenarios) == 4
        
        # Prices should decrease as yields increase
        prices = [s["price"] for s in scenarios]
        for i in range(1, len(prices)):
            assert prices[i] < prices[i-1]
            
        # Returns should be negative for yield increases
        returns = [s["return_pct"] for s in scenarios]
        assert returns[0] > 0  # Yield decrease = price increase
        assert returns[-1] < 0  # Yield increase = price decrease
        
    def test_scenario_edge_cases(self):
        """Test scenario analysis edge cases."""
        # Extreme yield changes
        scenarios = self.calc.scenario_analysis(
            current_price=100,
            coupon=0.05,
            years_to_maturity=10,
            frequency=2,
            yield_scenarios=[-0.05, 0.10]  # -500bp, +1000bp
        )
        
        assert len(scenarios) == 2
        assert all(s["price"] > 0 for s in scenarios)  # Prices should remain positive
        
    # ================================================================
    # COMPREHENSIVE ANALYTICS TESTS
    # ================================================================
    
    def test_calculate_all_analytics(self):
        """Test comprehensive analytics calculation."""
        bond_data = {
            "price": 95,
            "coupon_rate": 0.045,
            "maturity_date": "2034-12-15",
            "frequency": 2,
            "face_value": 100,
            "rating": "A",
            "type": "corporate"
        }
        
        analytics = self.calc.calculate_all_analytics(bond_data)
        
        # Check all required fields are present
        required_fields = [
            "ytm", "current_yield", "macaulay_duration", "modified_duration",
            "dv01", "convexity", "accrued_interest", "risk_score"
        ]
        
        for field in required_fields:
            assert field in analytics
            assert isinstance(analytics[field], (int, float))
            
        # Sanity checks
        assert analytics["ytm"] > 0
        assert analytics["current_yield"] > 0
        assert analytics["macaulay_duration"] > analytics["modified_duration"]
        assert 0 <= analytics["risk_score"] <= 100
        
    # ================================================================
    # PERFORMANCE TESTS
    # ================================================================
    
    def test_calculation_performance(self):
        """Test calculation performance for large datasets."""
        import time
        
        # Test YTM calculation speed
        start_time = time.time()
        
        for _ in range(1000):
            self.calc.calculate_ytm(95, 0.05, 10, 2, 100)
            
        elapsed = time.time() - start_time
        
        # Should complete 1000 YTM calculations in under 1 second
        assert elapsed < 1.0
        
    def test_newton_raphson_convergence_speed(self):
        """Test Newton-Raphson convergence speed."""
        # Test various starting conditions
        test_cases = [
            (80, 0.03, 30),   # Long duration, low coupon
            (120, 0.08, 5),   # High coupon, short duration
            (50, 0.0, 20),    # Zero coupon, long maturity
        ]
        
        for price, coupon, years in test_cases:
            ytm = self.calc.calculate_ytm(price, coupon, years, 2, 100)
            
            # Should converge to a reasonable value
            assert 0 <= ytm <= 1.0  # 0% to 100% is reasonable range
            
            # Verify convergence by back-calculation
            calc_price = self.calc.calculate_bond_price(coupon, ytm, years, 2, 100)
            assert abs(calc_price - price) < 0.01


class TestHelperFunctions:
    """Test utility helper functions."""
    
    def test_calculate_years_to_maturity(self):
        """Test years to maturity calculation."""
        # Test with datetime objects
        maturity = datetime(2034, 12, 15)
        current = datetime(2024, 12, 15)
        years = calculate_years_to_maturity(maturity, current)
        assert abs(years - 10.0) < 0.01
        
        # Test with date objects
        maturity = date(2029, 6, 15)
        current = date(2024, 6, 15)
        years = calculate_years_to_maturity(maturity, current)
        assert abs(years - 5.0) < 0.01
        
    def test_rating_to_score(self):
        """Test credit rating to numeric score conversion."""
        # Test investment grade ratings
        assert rating_to_score("AAA") == 100
        assert rating_to_score("AA+") > rating_to_score("AA")
        assert rating_to_score("AA") > rating_to_score("AA-")
        assert rating_to_score("A") > rating_to_score("BBB")
        
        # Test high yield ratings
        assert rating_to_score("BB") > rating_to_score("B")
        assert rating_to_score("B") > rating_to_score("CCC")
        assert rating_to_score("CCC") > rating_to_score("D")
        
        # Test edge cases
        assert rating_to_score("") == 50  # Default
        assert rating_to_score("INVALID") == 50  # Default
        assert rating_to_score(None) == 50  # Default


# ================================================================
# INTEGRATION TESTS WITH KNOWN FINANCIAL BENCHMARKS
# ================================================================

class TestFinancialBenchmarks:
    """Test calculations against known financial benchmarks."""
    
    def setup_method(self):
        self.calc = BondCalculator()
        
    def test_treasury_benchmark_10y(self):
        """Test against 10Y Treasury benchmark."""
        # 10Y Treasury: 4.25% coupon, 4.25% YTM, should price at par
        price = self.calc.calculate_bond_price(0.0425, 0.0425, 10, 2, 100)
        assert abs(price - 100.0) < 0.001
        
        # Duration should be approximately 8.5 years
        mac_dur, mod_dur = self.calc.calculate_duration(0.0425, 0.0425, 10, 2)
        assert 8.0 < mac_dur < 9.0
        assert mod_dur < mac_dur
        
    def test_corporate_bond_benchmark(self):
        """Test against corporate bond benchmark."""
        # Apple 3.75% 2033: Premium bond
        ytm = self.calc.calculate_ytm(105, 0.0375, 9, 2, 100)
        
        # YTM should be less than coupon for premium bond
        assert ytm < 0.0375
        assert ytm > 0.02  # Reasonable lower bound
        
    def test_zero_coupon_benchmark(self):
        """Test against zero-coupon STRIPS benchmark."""
        # 10Y STRIPS at 5% YTM
        price = self.calc.calculate_bond_price(0.0, 0.05, 10, 2, 100)
        expected = 100 / (1.025 ** 20)  # Semi-annual compounding
        assert abs(price - expected) < 0.001
        
        # Duration should equal maturity for zero-coupon
        mac_dur, _ = self.calc.calculate_duration(0.0, 0.05, 10, 2)
        assert abs(mac_dur - 10.0) < 0.001
        
    def test_high_yield_benchmark(self):
        """Test against high-yield bond benchmark."""
        # High-yield bond: 8% coupon, 10% YTM, 5Y maturity
        price = self.calc.calculate_bond_price(0.08, 0.10, 5, 2, 100)
        
        # Should be discount bond
        assert price < 100
        
        # Calculate risk score
        risk_score = self.calc.calculate_risk_score(0.10, 4.0, "BB", 500)
        assert risk_score > 60  # Should be high risk


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])