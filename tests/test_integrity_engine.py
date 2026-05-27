"""
YieldLens Integrity and Uniqueness Validation Tests
Verifies the SequenceMatcher and shingle overlapping duplication detector,
cross-module database consistency auditor, and context-aware filtering layers.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest
from integrity.duplication_detector import DuplicationDetector
from integrity.consistency_validator import ConsistencyValidator
from integrity.context_validator import ContextValidator
from integrity.content_integrity_engine import ContentIntegrityEngine

def test_duplication_detector_similarity():
    """Asserts that identical or heavily copied texts exceed 30% similarity limits."""
    text_a = "Our corporate credit is extremely secure. We maintain fortress capital reserves of $10B."
    text_b = "Our corporate credit is extremely secure. We maintain fortress capital reserves of $10B."
    
    sim = DuplicationDetector.calculate_similarity(text_a, text_b)
    assert sim == 1.0 # Identical

    text_c = "Our corporate credit is extremely secure. We maintain cash reserves of $10B to cover liquidity obligations."
    # Heavily overlapping text
    sim_partial = DuplicationDetector.calculate_similarity(text_a, text_c)
    assert sim_partial > 0.30

    text_d = "Tesla manufactures passenger vehicles, scaling manufacturing capabilities across worldwide gigafactories."
    # Completely different text
    sim_low = DuplicationDetector.calculate_similarity(text_a, text_d)
    assert sim_low <= 0.30

def test_duplication_detector_check_uniqueness():
    """Asserts that checking uniqueness correctly caches and flags duplicates."""
    from database.cache import cache
    cache.delete("integrity_history_test_cat")

    text_apple = "Apple Inc. premium hardware ecosystem, Services recurring revenue growth, and China supply risk."
    text_tesla = "Tesla EV production scaling gigafactory Supercharger vertical network battery pricing pressure."

    # First check should be 100% unique
    res1 = DuplicationDetector.check_uniqueness(text_apple, "test_cat", "AAPL")
    assert res1["success"] is True

    # Second check of a different company should be unique
    res2 = DuplicationDetector.check_uniqueness(text_tesla, "test_cat", "TSLA")
    assert res2["success"] is True

    # Third check repeating Apple text should fail uniqueness test
    text_copied = "Apple Inc. premium hardware ecosystem, Services recurring revenue growth, and China supply risk."
    res3 = DuplicationDetector.check_uniqueness(text_copied, "test_cat", "MSFT")
    assert res3["success"] is False
    assert res3["similarity_score"] > 0.30

def test_context_validator_recommendations():
    """Asserts that recommendations are dynamic, context-aware, and not boilerplate templates."""
    # Test 1: Inverted curve with long-duration portfolio -> Decrease duration
    portfolio_long = {
        "holdings": [{"bond_id": "b1", "rating": "AA"}],
        "wam": 8.5,
        "cash": 5000.0,
        "risk_profile": "CONSERVATIVE"
    }
    curve_inverted = {
        "DGS10": {"value": 4.10},
        "DGS2": {"value": 4.55}  # Inverted by 45 bps
    }

    res_long = ContextValidator.validate_recommendation_context(portfolio_long, curve_inverted)
    assert res_long["success"] is True
    recs_long = res_long["recommendations"]
    assert any(r["action"] == "DECREASE_DURATION" for r in recs_long)

    # Test 2: Aggressive risk profile with no high-yield holdings -> Yield enhancement
    portfolio_safe = {
        "holdings": [{"bond_id": "b2", "rating": "AAA"}],
        "wam": 2.5,
        "cash": 12000.0,
        "risk_profile": "AGGRESSIVE"
    }
    curve_normal = {
        "DGS10": {"value": 4.50},
        "DGS2": {"value": 4.00}  # Normal slope of +50 bps
    }

    res_safe = ContextValidator.validate_recommendation_context(portfolio_safe, curve_normal)
    assert res_safe["success"] is True
    recs_safe = res_safe["recommendations"]
    assert any(r["action"] == "YEILD_ENHANCEMENT" for r in recs_safe)

def test_content_integrity_engine_chart_verification():
    """Asserts that the content integrity engine detects flat placeholder lines and duplicates on charts."""
    # Flat horizontal line -> fails validation
    flat_data = [{"year": "2021", "val": 100}, {"year": "2022", "val": 100}, {"year": "2023", "val": 100}]
    res_flat = ContentIntegrityEngine.verify_chart_data("AAPL", "revenue", flat_data)
    assert res_flat["success"] is False
    assert "Static placeholder" in res_flat["reason"]

    # Unique curve data -> passes validation
    normal_data = [{"year": "2021", "val": 95}, {"year": "2022", "val": 102}, {"year": "2023", "val": 108}]
    res_normal = ContentIntegrityEngine.verify_chart_data("AAPL", "revenue", normal_data)
    assert res_normal["success"] is True
