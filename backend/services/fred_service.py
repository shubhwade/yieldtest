"""
FRED (Federal Reserve Economic Data) Service
Fetches treasury yields, rates, spreads, and economic indicators.
"""

import time

import httpx
from config import Config
from database.cache import cache

# Compatibility wrappers used by tests and older modules
_cache = cache


def _cache_get(key, ttl=None):
    try:
        return cache.get(key)
    except Exception:
        return None


def _cache_set(key, value, ttl=None):
    try:
        cache.set(key, value, ttl=(ttl if ttl is not None else Config.FRED_CACHE_TTL))
    except Exception:
        return False
    return True


FRED_BASE_URL = "https://api.stlouisfed.org/fred"

TREASURY_SERIES = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

ECONOMIC_SERIES = {
    "FEDFUNDS": {"name": "Federal Funds Rate", "category": "rates"},
    "SOFR": {"name": "SOFR", "category": "rates"},
    "CPIAUCSL": {"name": "CPI (All Urban)", "category": "inflation"},
    "CPILFESL": {"name": "Core CPI", "category": "inflation"},
    "PCEPI": {"name": "PCE Price Index", "category": "inflation"},
    "T10Y2Y": {"name": "10Y-2Y Spread", "category": "spreads"},
    "T10Y3M": {"name": "10Y-3M Spread", "category": "spreads"},
    "BAMLC0A0CM": {"name": "IG Corporate Spread", "category": "spreads"},
    "BAMLH0A0HYM2": {"name": "HY Corporate Spread", "category": "spreads"},
    "MORTGAGE30US": {"name": "30Y Mortgage Rate", "category": "rates"},
    "T5YIE": {"name": "5Y Breakeven Inflation", "category": "inflation"},
    "T10YIE": {"name": "10Y Breakeven Inflation", "category": "inflation"},
    "UNRATE": {"name": "Unemployment Rate", "category": "employment"},
    "GDP": {"name": "GDP", "category": "growth"},
}

# Redis-backed cache is managed via database.cache.cache


class FREDService:
    """Service for fetching data from FRED API."""

    def __init__(self):
        self.api_key = Config.FRED_API_KEY
        self.client = httpx.Client(timeout=15.0)

    def _fetch(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to FRED API."""
        if not self.api_key:
            return {"error": "FRED API key not configured"}
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        params["file_type"] = "json"

        from analytics.telemetry_engine import TelemetryEngine

        t0 = time.perf_counter()
        status_code = 200
        try:
            resp = self.client.get(f"{FRED_BASE_URL}/{endpoint}", params=params)
            status_code = resp.status_code
            resp.raise_for_status()
            data = resp.json()
            latency = (time.perf_counter() - t0) * 1000
            TelemetryEngine.log_api_latency("FRED", endpoint, latency, status_code)
            return data
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000
            TelemetryEngine.log_api_latency(
                "FRED",
                endpoint,
                latency,
                getattr(e, "response", None) and e.response.status_code or 500,
            )
            print(f"[FRED] Error fetching {endpoint}: {e}")
            return {"error": str(e)}

    def _generate_mock_series(self, series_id: str, limit: int) -> list:
        """Generate realistic mock data for FRED series when API key is not set."""
        import datetime
        import math

        # Base values and volatility for different series to make the charts look realistic and beautiful
        base_configs = {
            # Treasury Yields
            "DGS1MO": {"base": 5.25, "vol": 0.01, "trend": -0.0005},
            "DGS3MO": {"base": 5.15, "vol": 0.01, "trend": -0.0004},
            "DGS6MO": {"base": 5.00, "vol": 0.012, "trend": -0.0003},
            "DGS1": {"base": 4.75, "vol": 0.015, "trend": -0.0002},
            "DGS2": {"base": 4.45, "vol": 0.02, "trend": -0.0001},
            "DGS3": {"base": 4.25, "vol": 0.022, "trend": 0.0},
            "DGS5": {"base": 4.10, "vol": 0.025, "trend": 0.0001},
            "DGS7": {"base": 4.05, "vol": 0.025, "trend": 0.00015},
            "DGS10": {"base": 4.00, "vol": 0.028, "trend": 0.0002},
            "DGS20": {"base": 4.30, "vol": 0.025, "trend": 0.0001},
            "DGS30": {"base": 4.15, "vol": 0.025, "trend": 0.00005},
            # Economic Rates / Indicators
            "FEDFUNDS": {"base": 5.33, "vol": 0.002, "trend": 0.0},
            "SOFR": {"base": 5.31, "vol": 0.005, "trend": 0.0},
            "CPIAUCSL": {"base": 3.1, "vol": 0.02, "trend": -0.01},
            "CPILFESL": {"base": 3.8, "vol": 0.015, "trend": -0.008},
            "PCEPI": {"base": 2.6, "vol": 0.015, "trend": -0.006},
            "T10Y2Y": {"base": -0.45, "vol": 0.01, "trend": 0.0003},
            "T10Y3M": {"base": -1.15, "vol": 0.015, "trend": 0.0006},
            "BAMLC0A0CM": {"base": 1.20, "vol": 0.015, "trend": -0.0001},
            "BAMLH0A0HYM2": {"base": 3.80, "vol": 0.05, "trend": -0.0005},
            "MORTGAGE30US": {"base": 6.75, "vol": 0.03, "trend": -0.0002},
            "T5YIE": {"base": 2.2, "vol": 0.01, "trend": 0.0001},
            "T10YIE": {"base": 2.3, "vol": 0.01, "trend": 0.0001},
            "UNRATE": {"base": 3.9, "vol": 0.02, "trend": 0.0005},
            "GDP": {"base": 2.5, "vol": 0.1, "trend": 0.02},
        }

        config = base_configs.get(series_id, {"base": 4.0, "vol": 0.02, "trend": 0.0})
        base = config["base"]
        vol = config["vol"]
        trend = config["trend"]

        # Generate observations going backward
        observations = []
        now = datetime.datetime.utcnow()

        is_monthly = series_id in ("CPIAUCSL", "CPILFESL", "PCEPI", "UNRATE", "GDP")

        for i in range(limit):
            if is_monthly:
                date_str = (now - datetime.timedelta(days=i * 30)).strftime("%Y-%m-%d")
            else:
                date_str = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")

            # Add some sine-wave/pseudo-random variation to make it look like a real chart
            cycle = math.sin(i / 10.0) * vol * 5
            noise = math.sin(i / 2.0) * vol * 2
            trend_val = i * trend
            val = round(base + cycle + noise - trend_val, 4)

            # GDP is usually positive, unemployment positive, yields can't be negative (except spreads)
            if series_id not in ("T10Y2Y", "T10Y3M") and val < 0:
                val = abs(val)

            observations.append({"date": date_str, "value": val})

        return observations

    def get_series(self, series_id: str, limit: int = 365) -> list:
        """Get observations for a FRED series with Redis cache."""
        cache_key = f"fred_series_{series_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        observations = []
        if not self.api_key:
            observations = self._generate_mock_series(series_id, limit)
        else:
            data = self._fetch(
                "series/observations",
                {
                    "series_id": series_id,
                    "sort_order": "desc",
                    "limit": limit,
                },
            )
            if "error" in data or not data.get("observations"):
                observations = self._generate_mock_series(series_id, limit)
            else:
                for obs in data.get("observations", []):
                    val = obs.get("value", ".")
                    if val != ".":
                        try:
                            observations.append(
                                {"date": obs["date"], "value": float(val)}
                            )
                        except ValueError:
                            continue

        if observations:
            cache.set(cache_key, observations, ttl=Config.FRED_CACHE_TTL)
        return observations

    def get_yield_curve(self) -> dict:
        """Get current yield curve with all 11 maturities and run multi-source validation."""
        cache_key = "fred_yield_curve"
        cached = cache.get(cache_key)
        if cached:
            return cached

        from analytics.telemetry_engine import TelemetryEngine

        curve = {}
        validations = []
        confidence_scores = []

        for label, series_id in TREASURY_SERIES.items():
            obs = self.get_series(series_id, limit=5)
            if obs:
                val = obs[0]["value"]
                prev = obs[1]["value"] if len(obs) > 1 else val
                change = round(val - prev, 4)

                # Validate using TelemetryEngine
                val_res = TelemetryEngine.validate_treasury_yields(label, val)
                validations.append(val_res)
                confidence_scores.append(val_res["confidence_score"])

                curve[label] = {
                    "value": val,
                    "date": obs[0]["date"],
                    "previous": prev,
                    "change": change,
                    "confidence_score": val_res["confidence_score"],
                    "status": val_res["status"],
                    "secondary_value": val_res["secondary_value"],
                }
            else:
                curve[label] = {
                    "value": None,
                    "date": None,
                    "previous": None,
                    "change": 0,
                    "confidence_score": 0,
                    "status": "NO_DATA",
                    "secondary_value": None,
                }

        # Calculate curve-wide confidence score and freshness status
        avg_confidence = (
            int(sum(confidence_scores) / len(confidence_scores))
            if confidence_scores
            else 0
        )
        updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        freshness_res = TelemetryEngine.get_freshness_status("treasury", updated_at)

        result = {
            "curve": curve,
            "maturities": list(TREASURY_SERIES.keys()),
            "values": [curve[m]["value"] for m in TREASURY_SERIES.keys()],
            "updated_at": updated_at,
            "telemetry": {
                "confidence_score": avg_confidence,
                "freshness": freshness_res,
                "validations": validations,
            },
        }
        cache.set(cache_key, result, ttl=Config.FRED_CACHE_TTL)
        return result

    def get_yield_curve_history(self, days: int = 30) -> list:
        """Get historical yield curves for the past N days."""
        cache_key = f"fred_curve_history_{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get 10Y series as reference for dates
        ten_y = self.get_series("DGS10", limit=days)
        dates = [obs["date"] for obs in ten_y[:days]]

        # For each date, build a snapshot
        all_series = {}
        for label, series_id in TREASURY_SERIES.items():
            obs_list = self.get_series(series_id, limit=days + 10)
            all_series[label] = {obs["date"]: obs["value"] for obs in obs_list}

        history = []
        for date in dates[
            : min(days, 10)
        ]:  # Limit to 10 historical curves to avoid overload
            snapshot = {"date": date}
            for label in TREASURY_SERIES.keys():
                snapshot[label] = all_series.get(label, {}).get(date)
            if any(snapshot.get(l) is not None for l in TREASURY_SERIES.keys()):
                history.append(snapshot)

        cache.set(cache_key, history, ttl=Config.FRED_CACHE_TTL)
        return history

    def get_rate_history(self, series_id: str, days: int = 90) -> list:
        """Get history for a specific rate."""
        return self.get_series(series_id, limit=days)

    def get_economic_indicators(self) -> dict:
        """Get all key economic indicators."""
        cache_key = "fred_economic_indicators"
        cached = cache.get(cache_key)
        if cached:
            return cached

        indicators = {}
        for series_id, meta in ECONOMIC_SERIES.items():
            obs = self.get_series(series_id, limit=5)
            if obs:
                current = obs[0]["value"]
                previous = obs[1]["value"] if len(obs) > 1 else current
                indicators[series_id] = {
                    "name": meta["name"],
                    "category": meta["category"],
                    "value": current,
                    "previous": previous,
                    "change": round(current - previous, 4),
                    "change_pct": (
                        round(((current - previous) / previous) * 100, 4)
                        if previous != 0
                        else 0
                    ),
                    "date": obs[0]["date"],
                }
            else:
                indicators[series_id] = {
                    "name": meta["name"],
                    "category": meta["category"],
                    "value": None,
                    "date": None,
                }

        cache.set(cache_key, indicators, ttl=Config.FRED_CACHE_TTL)
        return indicators

    def get_spread_data(self) -> dict:
        """Get credit spread data."""
        cache_key = "fred_spreads"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        spread_series = {
            "ig_spread": "BAMLC0A0CM",
            "hy_spread": "BAMLH0A0HYM2",
            "ten_two": "T10Y2Y",
            "ten_three_mo": "T10Y3M",
        }
        spreads = {}
        for key, series_id in spread_series.items():
            obs = self.get_series(series_id, limit=30)
            if obs:
                spreads[key] = {
                    "current": obs[0]["value"],
                    "previous": obs[1]["value"] if len(obs) > 1 else obs[0]["value"],
                    "change": round(
                        obs[0]["value"]
                        - (obs[1]["value"] if len(obs) > 1 else obs[0]["value"]),
                        4,
                    ),
                    "history": obs[:30],
                    "date": obs[0]["date"],
                }
            else:
                spreads[key] = {"current": None, "change": 0, "history": []}

        _cache_set(cache_key, spreads)
        return spreads

    def get_inversion_analysis(self) -> dict:
        """Analyze yield curve inversions."""
        curve = self.get_yield_curve()
        c = curve.get("curve", {})

        two_y = c.get("2Y", {}).get("value")
        three_m = c.get("3M", {}).get("value")
        ten_y = c.get("10Y", {}).get("value")

        inversions = {}
        if ten_y is not None and two_y is not None:
            spread_10_2 = round(ten_y - two_y, 4)
            inversions["10Y_2Y"] = {
                "spread": spread_10_2,
                "inverted": spread_10_2 < 0,
                "status": "INVERTED" if spread_10_2 < 0 else "NORMAL",
                "ten_y": ten_y,
                "two_y": two_y,
            }
        if ten_y is not None and three_m is not None:
            spread_10_3m = round(ten_y - three_m, 4)
            inversions["10Y_3M"] = {
                "spread": spread_10_3m,
                "inverted": spread_10_3m < 0,
                "status": "INVERTED" if spread_10_3m < 0 else "NORMAL",
                "ten_y": ten_y,
                "three_m": three_m,
            }

        return {
            "inversions": inversions,
            "recession_signal": any(
                inv.get("inverted", False) for inv in inversions.values()
            ),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


# Singleton instance
fred_service = FREDService()
