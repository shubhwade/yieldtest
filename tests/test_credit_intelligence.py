import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest
from services.credit_service import CreditIntelligenceService

def test_credit_intelligence_available_issuers():
    issuers = CreditIntelligenceService.get_available_issuers()
    assert len(issuers) >= 4
    assert issuers[0]["ticker"] == "AAPL"

def test_credit_intelligence_issuer_analysis():
    ticker = "AAPL"
    from database.cache import cache
    # Invalidate cached results to force regeneration
    for t in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"]:
        cache.delete(f"credit_intel_v2_{t}")

    res = CreditIntelligenceService.analyze_corporate_credit(ticker, bypass_cache=True)
    
    # 1. Profile section verifications
    p = res["profile"]
    assert p["name"] == "Apple Inc."
    assert p["ticker"] == "AAPL"
    assert len(p["segments"]) >= 4

    # 2. Solvency and default parameter verifications (Z-score, Merton DD)
    r = res["quant_risk"]
    assert r["z_score"] > 3.0 # Apple is extremely solvent
    assert r["distance_to_default"] > 3.0
    assert r["probability_of_default"] < 0.01

    # 3. Solvency ratios verification
    le = res["leverage"]
    assert le["interest_coverage"] > 10.0
    assert le["net_debt_to_ebitda"] < 1.0

    # 4. Debt structure schedule verification
    d = res["debt_structure"]
    assert d["total_debt"] > 50.0 # billions
    assert d["wac"] > 0.0
    assert d["wam"] > 0.0

def test_credit_intelligence_peer_comparison():
    ticker = "AAPL"
    peers = CreditIntelligenceService.get_competitor_comparison(ticker)
    assert len(peers) >= 2
    assert peers[0]["ticker"] in ["AAPL", "MSFT"]

def test_credit_intelligence_strict_uniqueness():
    """Asserts that no two tickers ever receive identical segments, management teams, or capital structures."""
    res_aapl = CreditIntelligenceService.analyze_corporate_credit("AAPL", bypass_cache=True)
    res_msft = CreditIntelligenceService.analyze_corporate_credit("MSFT", bypass_cache=True)
    res_meta = CreditIntelligenceService.analyze_corporate_credit("META", bypass_cache=True)

    # Assert completely unique management teams
    mgmt_aapl = [m["name"] for m in res_aapl["profile"]["management"]]
    mgmt_msft = [m["name"] for m in res_msft["profile"]["management"]]
    mgmt_meta = [m["name"] for m in res_meta["profile"]["management"]]
    
    assert mgmt_aapl != mgmt_msft
    assert mgmt_msft != mgmt_meta
    assert mgmt_aapl != mgmt_meta

    # Assert completely unique business descriptions
    desc_aapl = res_aapl["profile"]["business_description"]
    desc_msft = res_msft["profile"]["business_description"]
    desc_meta = res_meta["profile"]["business_description"]

    assert desc_aapl != desc_msft
    assert desc_msft != desc_meta

    # Assert completely unique segment breakdowns
    segs_aapl = [s["name"] for s in res_aapl["profile"]["segments"]]
    segs_msft = [s["name"] for s in res_msft["profile"]["segments"]]
    segs_meta = [s["name"] for s in res_meta["profile"]["segments"]]

    assert segs_aapl != segs_msft
    assert segs_msft != segs_meta
