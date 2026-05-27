"""
Unit Tests for Risk Engine
Tests portfolio-level risk analytics, VaR, stress testing, and concentration risk.
"""

import pytest
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

from analytics.risk_engine import RiskEngine
from utils.helpers import rating_to_score


class TestRiskEngine:
    """Comprehensive tests for RiskEngine class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = RiskEngine()
        self.tolerance = 0.00001
        
        # Sample portfolio holdings
        self.sample_holdings = [
            {
                "weight": 0.3,
                "modified_duration": 8.5,
                "ytm": 0.045,
                "rating": "AA",
                "spread_bps": 50,
                "price": 102,
                "type": "treasury"
            },
            {
                "weight": 0.4,
                "modified_duration": 6.2,
                "ytm": 0.055,
                "rating": "A",
                "spread_bps": 85,
                "price": 98,
                "type": "corporate"
            },
            {
                "weight": 0.3,
                "modified_duration": 4.8,
                "ytm": 0.038,
                "rating": "AAA",
                "spread_bps": 25,
                "price": 105,
                "type": "municipal"
            }
        ]
        
    # ================================================================
    # PORTFOLIO RISK CALCULATION TESTS
    # ================================================================
    
    def test_portfolio_risk_basic(self):
        """Test basic portfolio risk calculation."""
        risk_metrics = self.engine.calculate_portfolio_risk(self.sample_holdings)
        
        # Check all required fields are present
        required_fields = [
            "portfolio_duration", "portfolio_yield", "portfolio_spread",
            "credit_risk_score", "concentration_risk", "duration_risk_1pct",
            "var_95", "risk_rating"
        ]
        
        for field in required_fields:
            assert field in risk_metrics
            
        # Sanity checks
        assert risk_metrics["portfolio_duration"] > 0
        assert risk_metrics["portfolio_yield"] > 0
        assert 0 <= risk_metrics["credit_risk_score"] <= 100
        assert risk_metrics["concentration_risk"] >= 0
        
    def test_portfolio_weighted_averages(self):
        """Test portfolio weighted average calculations."""
        risk_metrics = self.engine.calculate_portfolio_risk(self.sample_holdings)
        
        # Calculate expected weighted duration
        expected_duration = (
            0.3 * 8.5 +  # Treasury
            0.4 * 6.2 +  # Corporate
            0.3 * 4.8    # Municipal
        )
        
        assert abs(risk_metrics["portfolio_duration"] - expected_duration) < self.tolerance
        
        # Calculate expected weighted yield
        expected_yield = (
            0.3 * 0.045 +  # Treasury
            0.4 * 0.055 +  # Corporate
            0.3 * 0.038    # Municipal
        )
        
        assert abs(risk_metrics["portfolio_yield"] - expected_yield) < self.tolerance
        
    def test_empty_portfolio(self):
        """Test risk calculation for empty portfolio."""
        risk_metrics = self.engine.calculate_portfolio_risk([])
        
        assert risk_metrics["portfolio_duration"] == 0.0
        assert risk_metrics["portfolio_yield"] == 0.0
        assert risk_metrics["portfolio_spread"] == 0.0
        assert risk_metrics["credit_risk_score"] == 0.0
        assert risk_metrics["concentration_risk"] == 0.0
        assert risk_metrics["duration_risk_1pct"] == 0.0
        assert risk_metrics["var_95"] == 0.0
        assert risk_metrics["risk_rating"] == "N/A"
        
    def test_single_holding_portfolio(self):
        """Test risk calculation for single holding portfolio."""
        single_holding = [self.sample_holdings[0]]
        risk_metrics = self.engine.calculate_portfolio_risk(single_holding)
        
        # Should match the single holding's characteristics
        assert abs(risk_metrics["portfolio_duration"] - 8.5) < self.tolerance
        assert abs(risk_metrics["portfolio_yield"] - 0.045) < self.tolerance
        assert risk_metrics["concentration_risk"] == 1.0  # Maximum concentration
        
    # ================================================================
    # CREDIT RISK SCORING TESTS
    # ================================================================
    
    def test_credit_risk_score_calculation(self):
        """Test credit risk score calculation."""
        # High quality portfolio
        high_quality_ratings = {"AAA": 0.5, "AA": 0.3, "A": 0.2}
        high_quality_score = self.engine.credit_risk_score(high_quality_ratings)
        
        # Low quality portfolio
        low_quality_ratings = {"BB": 0.4, "B": 0.4, "CCC": 0.2}
        low_quality_score = self.engine.credit_risk_score(low_quality_ratings)
        
        # High quality should have higher score (lower risk)
        assert high_quality_score > low_quality_score
        assert 0 <= high_quality_score <= 100
        assert 0 <= low_quality_score <= 100
        
    def test_credit_risk_score_edge_cases(self):
        """Test credit risk score edge cases."""
        # Empty ratings
        score = self.engine.credit_risk_score({})
        assert score == 0.0
        
        # Single rating
        score = self.engine.credit_risk_score({"AAA": 1.0})
        assert score == 100.0  # Perfect credit
        
        # Invalid ratings (should use default)
        score = self.engine.credit_risk_score({"INVALID": 1.0})
        assert score == 50.0  # Default rating score
        
    # ================================================================
    # CONCENTRATION RISK TESTS
    # ================================================================
    
    def test_concentration_risk_calculation(self):
        """Test concentration risk calculation using HHI."""
        # Equally weighted portfolio (low concentration)
        equal_weights = [0.25, 0.25, 0.25, 0.25]
        equal_conc = self.engine.concentration_risk(equal_weights)
        
        # Concentrated portfolio (high concentration)
        concentrated_weights = [0.8, 0.1, 0.05, 0.05]
        concentrated_conc = self.engine.concentration_risk(concentrated_weights)
        
        # Concentrated portfolio should have higher concentration risk
        assert concentrated_conc > equal_conc
        assert 0 <= equal_conc <= 1
        assert 0 <= concentrated_conc <= 1
        
    def test_concentration_risk_edge_cases(self):
        """Test concentration risk edge cases."""
        # Single holding (maximum concentration)
        single_weight = [1.0]
        conc_risk = self.engine.concentration_risk(single_weight)
        assert conc_risk == 1.0
        
        # Empty weights
        conc_risk = self.engine.concentration_risk([])
        assert conc_risk == 0.0
        
        # Zero weights
        zero_weights = [0.0, 0.0, 0.0]
        conc_risk = self.engine.concentration_risk(zero_weights)
        assert conc_risk == 0.0
        
    def test_concentration_risk_mathematical_properties(self):
        """Test mathematical properties of concentration risk."""
        # Test with known HHI values
        weights = [0.4, 0.3, 0.2, 0.1]
        hhi = sum(w**2 for w in weights)
        expected_conc = (hhi - 1/len(weights)) / (1 - 1/len(weights))
        
        actual_conc = self.engine.concentration_risk(weights)
        assert abs(actual_conc - expected_conc) < self.tolerance
        
    # ================================================================
    # DURATION RISK TESTS
    # ================================================================
    
    def test_duration_risk_calculation(self):
        """Test duration risk calculation."""
        # 1% parallel yield shift
        duration = 8.0
        yield_change = 0.01
        
        duration_risk = self.engine.duration_risk(duration, yield_change)
        expected = duration * yield_change
        
        assert abs(duration_risk - expected) < self.tolerance
        
    def test_duration_risk_various_scenarios(self):
        """Test duration risk for various scenarios."""
        test_cases = [
            (5.0, 0.005),   # 5 years duration, 50bp shift
            (10.0, 0.01),   # 10 years duration, 100bp shift
            (15.0, 0.02),   # 15 years duration, 200bp shift
        ]
        
        for duration, yield_change in test_cases:
            risk = self.engine.duration_risk(duration, yield_change)
            expected = duration * yield_change
            assert abs(risk - expected) < self.tolerance
            
    def test_duration_risk_negative_shifts(self):
        """Test duration risk with negative yield shifts."""
        duration = 8.0
        yield_change = -0.01  # Yields decrease
        
        duration_risk = self.engine.duration_risk(duration, yield_change)
        expected = duration * abs(yield_change)  # Risk is always positive
        
        assert abs(duration_risk - expected) < self.tolerance
        
    # ================================================================
    # VALUE AT RISK (VAR) TESTS
    # ================================================================
    
    def test_var_calculation_basic(self):
        """Test basic VaR calculation."""
        # Sample daily returns (normally distributed)
        returns = np.random.normal(0, 0.01, 1000)  # 1% daily volatility
        
        var_95 = self.engine.calculate_var(returns, confidence_level=0.95)
        var_99 = self.engine.calculate_var(returns, confidence_level=0.99)
        
        # 99% VaR should be higher than 95% VaR
        assert var_99 > var_95
        assert var_95 > 0  # VaR should be positive (loss)
        
    def test_var_calculation_edge_cases(self):
        """Test VaR calculation edge cases."""
        # Empty returns
        var = self.engine.calculate_var([], confidence_level=0.95)
        assert var == 0.0
        
        # Single return
        var = self.engine.calculate_var([0.01], confidence_level=0.95)
        assert var == 0.01
        
        # All positive returns (no risk)
        positive_returns = [0.01, 0.02, 0.015, 0.008]
        var = self.engine.calculate_var(positive_returns, confidence_level=0.95)
        assert var >= 0
        
    def test_var_confidence_levels(self):
        """Test VaR at different confidence levels."""
        # Generate sample returns
        returns = np.random.normal(-0.001, 0.02, 1000)  # Slight negative drift
        
        confidence_levels = [0.90, 0.95, 0.99]
        vars = []
        
        for conf in confidence_levels:
            var = self.engine.calculate_var(returns, confidence_level=conf)
            vars.append(var)
            
        # VaR should increase with confidence level
        for i in range(1, len(vars)):
            assert vars[i] >= vars[i-1]
            
    # ================================================================
    # STRESS TESTING TESTS
    # ================================================================
    
    def test_stress_test_scenarios(self):
        """Test predefined stress test scenarios."""
        portfolio_value = 1000000  # $1M portfolio
        duration = 7.5
        
        stress_results = self.engine.stress_test(portfolio_value, duration)
        
        # Should have 8 predefined scenarios
        assert len(stress_results) == 8
        
        # Check scenario names
        expected_scenarios = [
            "Parallel +50bp", "Parallel -50bp", "Parallel +100bp", "Parallel -100bp",
            "Parallel +200bp", "Parallel -200bp", "Curve Steepener", "Curve Flattener"
        ]
        
        actual_scenarios = [s["scenario"] for s in stress_results]
        for expected in expected_scenarios:
            assert expected in actual_scenarios
            
    def test_stress_test_calculations(self):
        """Test stress test calculation accuracy."""
        portfolio_value = 1000000
        duration = 8.0
        
        stress_results = self.engine.stress_test(portfolio_value, duration)
        
        # Find +100bp parallel shift scenario
        parallel_100bp = next(s for s in stress_results if s["scenario"] == "Parallel +100bp")
        
        # Calculate expected loss: Duration × Yield Change × Portfolio Value
        expected_loss = duration * 0.01 * portfolio_value
        actual_loss = abs(parallel_100bp["pnl"])
        
        # Should be approximately equal (within 1%)
        assert abs(actual_loss - expected_loss) / expected_loss < 0.01
        
    def test_stress_test_edge_cases(self):
        """Test stress test edge cases."""
        # Zero portfolio value
        stress_results = self.engine.stress_test(0, 8.0)
        assert all(s["pnl"] == 0 for s in stress_results)
        
        # Zero duration
        stress_results = self.engine.stress_test(1000000, 0)
        assert all(s["pnl"] == 0 for s in stress_results)
        
    # ================================================================
    # RISK RATING TESTS
    # ================================================================
    
    def test_risk_rating_assignment(self):
        """Test risk rating assignment based on risk score."""
        # Test various risk scores
        test_cases = [
            (95, "Low"),
            (85, "Low"),
            (75, "Medium"),
            (65, "Medium"),
            (55, "High"),
            (45, "High"),
            (25, "Very High"),
            (5, "Very High")
        ]
        
        for risk_score, expected_rating in test_cases:
            rating = self.engine.get_risk_rating(risk_score)
            assert rating == expected_rating
            
    def test_risk_rating_edge_cases(self):
        """Test risk rating edge cases."""
        # Boundary values
        assert self.engine.get_risk_rating(80) == "Low"
        assert self.engine.get_risk_rating(79) == "Medium"
        assert self.engine.get_risk_rating(60) == "Medium"
        assert self.engine.get_risk_rating(59) == "High"
        assert self.engine.get_risk_rating(40) == "High"
        assert self.engine.get_risk_rating(39) == "Very High"
        
        # Out of range values
        assert self.engine.get_risk_rating(150) == "Low"  # Clamped to 100
        assert self.engine.get_risk_rating(-10) == "Very High"  # Clamped to 0
        
    # ================================================================
    # PORTFOLIO ANALYTICS INTEGRATION TESTS
    # ================================================================
    
    def test_portfolio_analytics_integration(self):
        """Test integration of all portfolio analytics."""
        # Create a diversified portfolio
        diversified_holdings = [
            {"weight": 0.2, "modified_duration": 5.0, "ytm": 0.03, "rating": "AAA", "spread_bps": 20, "price": 102, "type": "treasury"},
            {"weight": 0.2, "modified_duration": 7.0, "ytm": 0.045, "rating": "AA", "spread_bps": 40, "price": 100, "type": "treasury"},
            {"weight": 0.2, "modified_duration": 6.0, "ytm": 0.055, "rating": "A", "spread_bps": 80, "price": 98, "type": "corporate"},
            {"weight": 0.2, "modified_duration": 4.0, "ytm": 0.035, "rating": "AA", "spread_bps": 30, "price": 103, "type": "municipal"},
            {"weight": 0.2, "modified_duration": 8.0, "ytm": 0.025, "rating": "AAA", "spread_bps": 15, "price": 105, "type": "tips"}
        ]
        
        risk_metrics = self.engine.calculate_portfolio_risk(diversified_holdings)
        
        # Diversified portfolio should have:
        # - Moderate concentration risk (not 1.0)
        # - Reasonable duration (weighted average)
        # - Good credit quality (high score)
        
        assert risk_metrics["concentration_risk"] < 0.5  # Well diversified
        assert risk_metrics["credit_risk_score"] > 80  # High quality
        assert 4.0 < risk_metrics["portfolio_duration"] < 8.0  # Reasonable duration
        
    def test_concentrated_vs_diversified_portfolio(self):
        """Test risk differences between concentrated and diversified portfolios."""
        # Concentrated portfolio (80% in one holding)
        concentrated_holdings = [
            {"weight": 0.8, "modified_duration": 10.0, "ytm": 0.08, "rating": "BB", "spread_bps": 300, "price": 90, "type": "corporate"},
            {"weight": 0.2, "modified_duration": 5.0, "ytm": 0.04, "rating": "AAA", "spread_bps": 20, "price": 102, "type": "treasury"}
        ]
        
        # Diversified portfolio (equal weights)
        diversified_holdings = [
            {"weight": 0.5, "modified_duration": 10.0, "ytm": 0.08, "rating": "BB", "spread_bps": 300, "price": 90, "type": "corporate"},
            {"weight": 0.5, "modified_duration": 5.0, "ytm": 0.04, "rating": "AAA", "spread_bps": 20, "price": 102, "type": "treasury"}
        ]
        
        concentrated_risk = self.engine.calculate_portfolio_risk(concentrated_holdings)
        diversified_risk = self.engine.calculate_portfolio_risk(diversified_holdings)
        
        # Concentrated portfolio should have higher concentration risk
        assert concentrated_risk["concentration_risk"] > diversified_risk["concentration_risk"]
        
    # ================================================================
    # PERFORMANCE TESTS
    # ================================================================
    
    def test_risk_calculation_performance(self):
        """Test risk calculation performance for large portfolios."""
        import time
        
        # Create large portfolio (1000 holdings)
        large_holdings = []
        for i in range(1000):
            holding = {
                "weight": 0.001,  # Equal weight
                "modified_duration": 5.0 + (i % 10),  # Vary duration
                "ytm": 0.03 + (i % 5) * 0.01,  # Vary yield
                "rating": ["AAA", "AA", "A", "BBB", "BB"][i % 5],  # Vary rating
                "spread_bps": 50 + (i % 10) * 20,  # Vary spread
                "price": 95 + (i % 10),  # Vary price
                "type": "corporate"
            }
            large_holdings.append(holding)
            
        start_time = time.time()
        risk_metrics = self.engine.calculate_portfolio_risk(large_holdings)
        elapsed = time.time() - start_time
        
        # Should complete in under 100ms for 1000 holdings
        assert elapsed < 0.1
        assert risk_metrics["portfolio_duration"] > 0
        
    # ================================================================
    # MATHEMATICAL VALIDATION TESTS
    # ================================================================
    
    def test_hhi_calculation_accuracy(self):
        """Test HHI calculation mathematical accuracy."""
        weights = [0.4, 0.3, 0.2, 0.1]
        
        # Manual HHI calculation
        manual_hhi = sum(w**2 for w in weights)
        
        # Using concentration risk function (which normalizes HHI)
        n = len(weights)
        min_hhi = 1/n
        max_hhi = 1.0
        
        normalized_hhi = (manual_hhi - min_hhi) / (max_hhi - min_hhi)
        calculated_conc = self.engine.concentration_risk(weights)
        
        assert abs(calculated_conc - normalized_hhi) < self.tolerance
        
    def test_weighted_average_accuracy(self):
        """Test weighted average calculation accuracy."""
        holdings = [
            {"weight": 0.25, "modified_duration": 4.0, "ytm": 0.03},
            {"weight": 0.35, "modified_duration": 6.0, "ytm": 0.045},
            {"weight": 0.40, "modified_duration": 8.0, "ytm": 0.055}
        ]
        
        # Manual weighted average calculation
        total_weight = sum(h["weight"] for h in holdings)
        manual_duration = sum(h["modified_duration"] * h["weight"] for h in holdings) / total_weight
        manual_yield = sum(h["ytm"] * h["weight"] for h in holdings) / total_weight
        
        # Add required fields for risk calculation
        for h in holdings:
            h.update({"rating": "A", "spread_bps": 50, "price": 100, "type": "corporate"})
            
        risk_metrics = self.engine.calculate_portfolio_risk(holdings)
        
        assert abs(risk_metrics["portfolio_duration"] - manual_duration) < self.tolerance
        assert abs(risk_metrics["portfolio_yield"] - manual_yield) < self.tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])