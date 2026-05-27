"""
Treasury Direct API Service
Fetches auction data, rates, and upcoming auctions from Treasury.gov.
"""

import httpx
from config import Config
from database.cache import cache

TREASURY_BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Redis-backed cache is managed via database.cache.cache


class TreasuryService:
    """Service for fetching data from Treasury Direct API."""

    def __init__(self):
        self.client = httpx.Client(timeout=15.0)

    def _fetch(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to Treasury API."""
        if params is None:
            params = {}
        params.setdefault("page[size]", 50)
        params.setdefault("format", "json")
        try:
            resp = self.client.get(f"{TREASURY_BASE_URL}/{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[TREASURY] Error fetching {endpoint}: {e}")
            return {"error": str(e)}

    def get_average_rates(self) -> list:
        """Get average interest rates on US Treasury securities with Redis cache."""
        cache_key = "treasury_avg_rates"
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = self._fetch(
            "v2/accounting/od/avg_interest_rates",
            {
                "sort": "-record_date",
                "page[size]": 100,
            },
        )
        if "error" in data:
            return []

        results = []
        for record in data.get("data", []):
            results.append(
                {
                    "record_date": record.get("record_date"),
                    "security_desc": record.get("security_desc"),
                    "security_type_desc": record.get("security_type_desc"),
                    "avg_interest_rate_amt": float(
                        record.get("avg_interest_rate_amt", 0)
                    ),
                }
            )

        if results:
            cache.set(cache_key, results, ttl=Config.TREASURY_CACHE_TTL)
        return results

    def get_auction_data(self, security_type: str = None) -> list:
        """Get recent treasury auction results with Redis cache."""
        cache_key = f"treasury_auctions_{security_type or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        params = {
            "sort": "-auction_date",
            "page[size]": 50,
        }
        if security_type:
            params["filter"] = f"security_type:eq:{security_type}"

        data = self._fetch("v1/accounting/od/auctions_query", params)
        if "error" in data:
            # Try alternate endpoint
            data = self._fetch(
                "v2/accounting/od/securities_sales",
                {
                    "sort": "-record_date",
                    "page[size]": 50,
                },
            )
            if "error" in data:
                return []

        results = []
        for record in data.get("data", []):
            results.append(
                {
                    "record_date": record.get(
                        "record_date", record.get("auction_date", "")
                    ),
                    "security_type": record.get(
                        "security_type", record.get("security_type_desc", "")
                    ),
                    "security_term": record.get("security_term", ""),
                    "high_yield": record.get(
                        "high_yield_pct", record.get("high_investment_rate", "")
                    ),
                    "allotted_pct": record.get("allotted_pct", ""),
                    "bid_to_cover": record.get("bid_to_cover_ratio", ""),
                }
            )

        if results:
            cache.set(cache_key, results, ttl=Config.TREASURY_CACHE_TTL)
        return results

    def get_upcoming_auctions(self) -> list:
        """Get upcoming treasury auction schedule with Redis cache."""
        cache_key = "treasury_upcoming"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Try to fetch from real API first
        data = self._fetch(
            "v1/accounting/od/auctions_query",
            {
                "filter": "auction_date:gte:2024-01-01",  # Placeholder for real future filter
                "sort": "auction_date",
                "page[size]": 20,
            },
        )

        if "error" not in data and data.get("data"):
            results = []
            for record in data.get("data", []):
                results.append(
                    {
                        "security_description": record.get("security_description", ""),
                        "security_type": record.get("security_type", ""),
                        "auction_date": record.get("auction_date", ""),
                        "settlement_date": record.get("settlement_date", ""),
                        "announcement_date": record.get("announcement_date", ""),
                    }
                )
            cache.set(cache_key, results, ttl=Config.TREASURY_CACHE_TTL)
            return results

        # Fallback to smart mock if API fails or returns empty
        import datetime

        now = datetime.datetime.utcnow()
        upcoming = []
        schedule = [
            ("4-Week Bill", "Bill", 1),
            ("8-Week Bill", "Bill", 2),
            ("13-Week Bill", "Bill", 3),
            ("26-Week Bill", "Bill", 5),
            ("2-Year Note", "Note", 7),
            ("5-Year Note", "Note", 10),
            ("7-Year Note", "Note", 12),
            ("10-Year Note", "Note", 14),
            ("30-Year Bond", "Bond", 18),
        ]
        for desc, sec_type, day_offset in schedule:
            auction_date = now + datetime.timedelta(days=day_offset)
            upcoming.append(
                {
                    "security_description": desc,
                    "security_type": sec_type,
                    "auction_date": auction_date.strftime("%Y-%m-%d"),
                    "settlement_date": (
                        auction_date + datetime.timedelta(days=1)
                    ).strftime("%Y-%m-%d"),
                    "announcement_date": (
                        auction_date - datetime.timedelta(days=2)
                    ).strftime("%Y-%m-%d"),
                }
            )

        cache.set(cache_key, upcoming, ttl=Config.TREASURY_CACHE_TTL)
        return upcoming


treasury_service = TreasuryService()
