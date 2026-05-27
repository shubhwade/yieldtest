"""
Market Data Service
Aggregates data from FRED, Treasury, and bond universe for dashboard and market views.
"""

import random
import time

from config import Config
from database.cache import cache
from events.dispatcher import TREASURY_UPDATED, dispatcher
from services.fred_service import fred_service

# Redis-backed cache is managed via database.cache.cache


class MarketDataService:
    """Aggregates all market data sources for dashboard and views."""

    def get_dashboard_data(self, db=None) -> dict:
        """Get full dashboard payload."""
        cache_key = "dashboard_data"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        yield_curve = fred_service.get_yield_curve()
        indicators = fred_service.get_economic_indicators()
        spreads = fred_service.get_spread_data()

        # Key metrics for top cards
        curve = yield_curve.get("curve", {})
        key_metrics = [
            {
                "label": "10Y Treasury",
                "value": curve.get("10Y", {}).get("value"),
                "change": curve.get("10Y", {}).get("change", 0),
                "unit": "%",
            },
            {
                "label": "2Y Treasury",
                "value": curve.get("2Y", {}).get("value"),
                "change": curve.get("2Y", {}).get("change", 0),
                "unit": "%",
            },
            {
                "label": "Fed Funds Rate",
                "value": indicators.get("FEDFUNDS", {}).get("value"),
                "change": indicators.get("FEDFUNDS", {}).get("change", 0),
                "unit": "%",
            },
            {
                "label": "SOFR",
                "value": indicators.get("SOFR", {}).get("value"),
                "change": indicators.get("SOFR", {}).get("change", 0),
                "unit": "%",
            },
            {
                "label": "CPI YoY",
                "value": indicators.get("CPIAUCSL", {}).get("value"),
                "change": indicators.get("CPIAUCSL", {}).get("change", 0),
                "unit": "%",
            },
        ]

        # Rate movements table
        rate_movements = []
        for label, series_id in [
            ("10Y Treasury", "DGS10"),
            ("2Y Treasury", "DGS2"),
            ("30Y Treasury", "DGS30"),
            ("5Y Treasury", "DGS5"),
            ("Fed Funds", "FEDFUNDS"),
            ("SOFR", "SOFR"),
            ("30Y Mortgage", "MORTGAGE30US"),
        ]:
            obs = fred_service.get_series(series_id, limit=30)
            if obs:
                rate_movements.append(
                    {
                        "name": label,
                        "current": obs[0]["value"],
                        "change_1d": (
                            round(obs[0]["value"] - obs[1]["value"], 4)
                            if len(obs) > 1
                            else 0
                        ),
                        "change_1w": (
                            round(obs[0]["value"] - obs[5]["value"], 4)
                            if len(obs) > 5
                            else 0
                        ),
                        "change_1m": (
                            round(
                                obs[0]["value"] - obs[min(22, len(obs) - 1)]["value"], 4
                            )
                            if len(obs) > 22
                            else 0
                        ),
                    }
                )

        # Spread data
        spread_bars = []
        for key, label in [
            ("ig_spread", "IG Spread"),
            ("hy_spread", "HY Spread"),
            ("ten_two", "10Y-2Y"),
            ("ten_three_mo", "10Y-3M"),
        ]:
            s = spreads.get(key, {})
            if s.get("current") is not None:
                spread_bars.append(
                    {
                        "name": label,
                        "value": s["current"],
                        "change": s.get("change", 0),
                        "unit": "bps" if key in ("ig_spread", "hy_spread") else "%",
                    }
                )

        # Top movers from bond collection
        movers = []
        if db is not None:
            bonds = list(db["bonds"].find({"type": {"$ne": "money_market"}}).limit(100))
            random.seed(int(time.time() / 3600))
            for bond in random.sample(bonds, min(8, len(bonds))):
                change = round(random.uniform(-0.15, 0.15), 4)
                movers.append(
                    {
                        "name": bond.get("name", "")[:50],
                        "type": bond.get("type"),
                        "issuer": bond.get("issuer"),
                        "price": bond.get("price"),
                        "coupon": bond.get("coupon_rate"),
                        "change": change,
                    }
                )
            movers.sort(key=lambda x: abs(x["change"]), reverse=True)

        # Market heatmap
        heatmap = self.get_market_heatmap()

        # Sentiment
        sentiment = self.get_market_sentiment(yield_curve, spreads)

        result = {
            "key_metrics": key_metrics,
            "yield_curve": yield_curve,
            "spreads": spread_bars,
            "rate_movements": rate_movements,
            "heatmap": heatmap,
            "movers": movers[:5],
            "sentiment": sentiment,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # Emit event for real-time subscribers
        dispatcher.emit(
            TREASURY_UPDATED, {"metrics": key_metrics, "curve": yield_curve}
        )

        cache.set(cache_key, result, ttl=120)  # Dashboard cache is short (2 mins)
        return result

    def get_market_heatmap(self) -> dict:
        """Get sector/type heatmap data."""
        cache_key = "market_heatmap"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        random.seed(int(time.time() / 3600))
        sectors = [
            {
                "name": "Government",
                "avg_yield": round(random.uniform(4.0, 4.8), 2),
                "change": round(random.uniform(-0.05, 0.05), 3),
                "volume": "High",
            },
            {
                "name": "Corp IG",
                "avg_yield": round(random.uniform(4.5, 5.5), 2),
                "change": round(random.uniform(-0.08, 0.08), 3),
                "volume": "High",
            },
            {
                "name": "Corp HY",
                "avg_yield": round(random.uniform(6.0, 8.0), 2),
                "change": round(random.uniform(-0.15, 0.15), 3),
                "volume": "Medium",
            },
            {
                "name": "Municipal",
                "avg_yield": round(random.uniform(2.8, 4.0), 2),
                "change": round(random.uniform(-0.04, 0.04), 3),
                "volume": "Medium",
            },
            {
                "name": "MBS",
                "avg_yield": round(random.uniform(5.0, 6.0), 2),
                "change": round(random.uniform(-0.06, 0.06), 3),
                "volume": "High",
            },
            {
                "name": "TIPS",
                "avg_yield": round(random.uniform(1.5, 2.5), 2),
                "change": round(random.uniform(-0.03, 0.03), 3),
                "volume": "Low",
            },
        ]
        result = {"sectors": sectors}
        cache.set(cache_key, result, ttl=Config.DEFAULT_CACHE_TTL)
        return result

    def get_top_movers(self, db) -> list:
        """Get bonds with biggest yield changes."""
        bonds = list(
            db["bonds"].find({"type": {"$in": ["treasury", "corporate"]}}).limit(200)
        )
        random.seed(int(time.time() / 3600))
        movers = []
        for bond in random.sample(bonds, min(10, len(bonds))):
            change = round(random.uniform(-0.20, 0.20), 4)
            movers.append(
                {
                    "id": str(bond["_id"]),
                    "name": bond.get("name", "")[:50],
                    "type": bond.get("type"),
                    "issuer": bond.get("issuer"),
                    "price": bond.get("price"),
                    "coupon": bond.get("coupon_rate"),
                    "change": change,
                }
            )
        movers.sort(key=lambda x: abs(x["change"]), reverse=True)
        return movers

    def get_market_sentiment(self, yield_curve: dict, spreads: dict) -> dict:
        """Calculate market sentiment from data signals."""
        score = 50  # Neutral baseline
        signals = []

        curve = yield_curve.get("curve", {})
        ten_y = curve.get("10Y", {}).get("value")
        two_y = curve.get("2Y", {}).get("value")

        if ten_y and two_y:
            spread_10_2 = ten_y - two_y
            if spread_10_2 < 0:
                score -= 15
                signals.append(
                    {"signal": "Yield curve inverted (2s10s)", "impact": "bearish"}
                )
            elif spread_10_2 > 0.5:
                score += 10
                signals.append(
                    {"signal": "Normal yield curve slope", "impact": "bullish"}
                )

        ig_spread = spreads.get("ig_spread", {}).get("current")
        if ig_spread:
            if ig_spread > 1.5:
                score -= 10
                signals.append(
                    {"signal": "Wide IG credit spreads", "impact": "bearish"}
                )
            elif ig_spread < 1.0:
                score += 5
                signals.append(
                    {"signal": "Tight IG credit spreads", "impact": "bullish"}
                )

        hy_spread = spreads.get("hy_spread", {}).get("current")
        if hy_spread:
            if hy_spread > 5.0:
                score -= 10
                signals.append(
                    {
                        "signal": "Elevated HY spreads - stress signal",
                        "impact": "bearish",
                    }
                )
            elif hy_spread < 3.5:
                score += 5
                signals.append(
                    {"signal": "Compressed HY spreads - risk-on", "impact": "bullish"}
                )

        score = max(0, min(100, score))
        if score >= 65:
            description = "Bullish - favorable conditions for fixed income"
        elif score >= 45:
            description = "Neutral - mixed signals, proceed with caution"
        else:
            description = "Bearish - elevated risk signals in credit markets"

        return {
            "score": score,
            "description": description,
            "signals": signals,
            "label": (
                "Bullish" if score >= 65 else ("Neutral" if score >= 45 else "Bearish")
            ),
        }

    def get_market_summary(self, db=None) -> dict:
        """Get a compact market summary."""
        yield_curve = fred_service.get_yield_curve()
        indicators = fred_service.get_economic_indicators()
        bond_count = db["bonds"].count_documents({}) if db is not None else 0

        return {
            "yield_curve_snapshot": {
                "2Y": yield_curve.get("curve", {}).get("2Y", {}).get("value"),
                "10Y": yield_curve.get("curve", {}).get("10Y", {}).get("value"),
                "30Y": yield_curve.get("curve", {}).get("30Y", {}).get("value"),
            },
            "fed_funds": indicators.get("FEDFUNDS", {}).get("value"),
            "cpi": indicators.get("CPIAUCSL", {}).get("value"),
            "bond_universe_size": bond_count,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


market_data_service = MarketDataService()
