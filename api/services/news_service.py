"""
News Service — Multi-Source Financial Intelligence Pipeline
Aggregates, deduplicates, categorizes, and enriches news from 4 sources
with automatic failover. Never returns empty results.

Priority stack:
  1. Finnhub  (finance-focused, reliable free tier)
  2. GNews    (breaking headlines, trending stories)
  3. NewsAPI  (general financial coverage)
  4. Yahoo Finance RSS (emergency fallback, no key needed)
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher

import feedparser
import httpx
from config import Config
from database.cache import cache
from database.mongo import get_db

logger = logging.getLogger("YieldLens.News")

# ── Category keyword mapping ─────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Treasury": [
        "treasury",
        "t-bill",
        "t-bond",
        "t-note",
        "government bond",
        "sovereign debt",
        "treasury auction",
        "treasury yield",
    ],
    "Fed": [
        "federal reserve",
        "fed ",
        "fomc",
        "powell",
        "rate decision",
        "monetary policy",
        "central bank",
        "fed meeting",
        "rate hike",
        "rate cut",
        "taper",
        "quantitative",
    ],
    "Inflation": [
        "inflation",
        "cpi",
        "pce",
        "consumer price",
        "deflation",
        "price index",
        "core inflation",
        "cost of living",
    ],
    "Rates": [
        "interest rate",
        "yield",
        "basis points",
        "bps",
        "sofr",
        "libor",
        "prime rate",
        "discount rate",
        "mortgage rate",
    ],
    "Corporate Bonds": [
        "corporate bond",
        "investment grade",
        "ig bond",
        "corporate debt",
        "bond issuance",
        "corporate credit",
        "debenture",
    ],
    "Municipal Bonds": [
        "municipal bond",
        "muni bond",
        "muni ",
        "state bond",
        "local government bond",
        "tax-exempt bond",
        "revenue bond",
        "general obligation",
    ],
    "Macro": [
        "gdp",
        "unemployment",
        "jobs report",
        "nonfarm payroll",
        "economic growth",
        "recession",
        "trade deficit",
        "manufacturing",
        "consumer confidence",
        "retail sales",
        "housing starts",
    ],
    "Corporate Credit": [
        "credit rating",
        "moody",
        "s&p",
        "fitch",
        "downgrade",
        "upgrade",
        "credit risk",
        "default",
        "bankruptcy",
        "restructuring",
        "high yield",
        "junk bond",
        "leveraged",
    ],
    "Market Moving": [
        "market crash",
        "sell-off",
        "rally",
        "surge",
        "plunge",
        "volatility",
        "vix",
        "black swan",
        "circuit breaker",
        "flash crash",
    ],
    "Breaking News": [
        "breaking",
        "urgent",
        "just in",
        "developing",
        "emergency",
        "crisis",
    ],
    "Trending": [
        "trending",
        "viral",
        "most read",
        "top story",
    ],
    "Portfolio Related": [],  # Populated dynamically from user holdings
}

# ── Macro event keywords ─────────────────────────────────────────────────────
MACRO_EVENTS = [
    "fed",
    "fomc",
    "cpi",
    "ppi",
    "gdp",
    "unemployment",
    "nonfarm",
    "payroll",
    "retail sales",
    "housing",
    "consumer confidence",
    "manufacturing",
    "ism",
    "pmi",
    "trade balance",
    "inflation",
    "treasury auction",
    "debt ceiling",
    "fiscal",
    "stimulus",
]


class NewsService:
    """Multi-source financial news aggregation with failover and enrichment."""

    def __init__(self):
        self.finnhub_key = Config.FINNHUB_API_KEY
        self.gnews_key = Config.GNEWS_API_KEY
        self.newsapi_key = Config.NEWS_API_KEY
        self.cache_ttl = Config.NEWS_CACHE_TTL

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════

    async def fetch_news(self, query="fixed income bonds", category=None, limit=20):
        """
        Main entry point.  Returns enriched, deduplicated, categorised articles.
        NEVER returns an empty list — falls back to MongoDB cache.
        """
        cache_key = f"news_{query}_{category}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Fetch from all available sources with failover
        raw_articles = await self._fetch_with_failover(query)

        # 2. If we got nothing from APIs, pull from MongoDB
        if not raw_articles:
            raw_articles = self._get_cached_articles(limit)

        if not raw_articles:
            # Absolute last resort — return a system status article
            raw_articles = self._get_fallback_articles()

        # 3. Full pipeline
        articles = self._deduplicate(raw_articles)
        articles = [self._categorize(a) for a in articles]
        articles = self._detect_entities(articles)
        articles = self._detect_macro_events(articles)
        articles = self._rank_articles(articles)

        # 4. Filter by category if requested
        if category:
            cat_lower = category.lower()
            articles = [
                a
                for a in articles
                if cat_lower in [c.lower() for c in a.get("categories", [])]
            ] or articles  # Fall back to all if filter empties

        articles = articles[:limit]

        # 5. Cache and persist
        cache.set(cache_key, articles, ttl=self.cache_ttl)
        self._store_articles(articles)

        return articles

    async def fetch_all_sources(self, query="fixed income bonds"):
        """Fetch from ALL available sources (for background worker)."""
        results = []
        sources = [
            ("finnhub", self._fetch_finnhub),
            ("gnews", self._fetch_gnews),
            ("newsapi", self._fetch_newsapi),
            ("yahoo_rss", self._fetch_yahoo_rss),
        ]

        for name, fetcher in sources:
            try:
                if name == "yahoo_rss":
                    articles = fetcher()
                else:
                    articles = await fetcher(query)
                if articles:
                    results.extend(articles)
                    logger.info(f"[News] {name}: {len(articles)} articles")
            except Exception as e:
                logger.warning(f"[News] {name} error: {e}")

        return results

    async def get_portfolio_news(self, portfolio_id=None):
        """Get news specifically relevant to user's portfolio holdings."""
        try:
            db = get_db()
            # Get portfolio holdings
            query_filter = {"_id": portfolio_id} if portfolio_id else {}
            portfolios = list(db["portfolios"].find(query_filter).limit(3))

            issuer_names = set()
            sectors = set()
            for pf in portfolios:
                for holding in pf.get("holdings", []):
                    bond_id = holding.get("bond_id")
                    if bond_id:
                        bond = db["bonds"].find_one({"_id": bond_id})
                        if bond:
                            issuer_names.add(bond.get("issuer", ""))
                            sectors.add(bond.get("sector", ""))

            if not issuer_names and not sectors:
                return await self.fetch_news(query="bond market fixed income")

            # Search for news matching issuers
            search_terms = list(issuer_names)[:5]  # Top 5 issuers
            all_articles = []
            for term in search_terms:
                if term:
                    articles = await self.fetch_news(query=term, limit=5)
                    for a in articles:
                        a["portfolio_match"] = True
                        a["matched_issuer"] = term
                    all_articles.extend(articles)

            return (
                self._deduplicate(all_articles)[:20]
                if all_articles
                else await self.fetch_news()
            )
        except Exception as e:
            logger.error(f"[News] Portfolio news error: {e}")
            return await self.fetch_news()

    def get_trending(self, limit=10):
        """Get trending/breaking news from cache or MongoDB."""
        cached = cache.get("news_trending")
        if cached:
            return cached[:limit]

        try:
            db = get_db()
            articles = list(
                db["news_articles"]
                .find(
                    {
                        "categories": {
                            "$in": ["Breaking News", "Market Moving", "Trending"]
                        }
                    }
                )
                .sort("fetched_at", -1)
                .limit(limit)
            )
            for a in articles:
                a["_id"] = str(a["_id"])
            return articles if articles else self._get_fallback_articles()[:limit]
        except Exception:
            return self._get_fallback_articles()[:limit]

    def search_news(self, keyword, limit=20):
        """Search stored news articles by keyword."""
        try:
            db = get_db()
            regex_filter = {"$regex": keyword, "$options": "i"}
            articles = list(
                db["news_articles"]
                .find({"$or": [{"title": regex_filter}, {"summary": regex_filter}]})
                .sort("fetched_at", -1)
                .limit(limit)
            )
            for a in articles:
                a["_id"] = str(a["_id"])
            return articles
        except Exception:
            return []

    def get_by_category(self, category, limit=15):
        """Get news by category from MongoDB."""
        try:
            db = get_db()
            articles = list(
                db["news_articles"]
                .find({"categories": category})
                .sort("fetched_at", -1)
                .limit(limit)
            )
            for a in articles:
                a["_id"] = str(a["_id"])
            return articles if articles else self._get_fallback_articles()
        except Exception:
            return self._get_fallback_articles()

    # ══════════════════════════════════════════════════════════════════════════
    # FAILOVER LOGIC
    # ══════════════════════════════════════════════════════════════════════════

    async def _fetch_with_failover(self, query):
        """Sequential failover: Finnhub → GNews → NewsAPI → Yahoo RSS."""

        # 1. Finnhub (primary)
        articles = await self._fetch_finnhub(query)
        if articles:
            logger.info(f"[News] Finnhub success: {len(articles)} articles")
            return articles

        # 2. GNews (secondary)
        articles = await self._fetch_gnews(query)
        if articles:
            logger.info(f"[News] GNews fallback: {len(articles)} articles")
            return articles

        # 3. NewsAPI (tertiary)
        articles = await self._fetch_newsapi(query)
        if articles:
            logger.info(f"[News] NewsAPI fallback: {len(articles)} articles")
            return articles

        # 4. Yahoo RSS (emergency)
        articles = self._fetch_yahoo_rss()
        if articles:
            logger.info(
                f"[News] Yahoo RSS emergency fallback: {len(articles)} articles"
            )
            return articles

        logger.warning("[News] All sources failed, using cache")
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # SOURCE FETCHERS
    # ══════════════════════════════════════════════════════════════════════════

    async def _fetch_finnhub(self, query=""):
        """Fetch from Finnhub — general + company news."""
        if not self.finnhub_key:
            return None
        try:
            articles = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                # General market news
                res = await client.get(
                    "https://finnhub.io/api/v1/news",
                    params={"category": "general", "token": self.finnhub_key},
                )
                if res.status_code == 200:
                    for a in res.json()[:15]:
                        articles.append(
                            {
                                "title": a.get("headline", ""),
                                "summary": a.get("summary", ""),
                                "source": a.get("source", "Finnhub"),
                                "url": a.get("url", ""),
                                "image": a.get("image", ""),
                                "time": datetime.fromtimestamp(
                                    a.get("datetime", time.time()), tz=timezone.utc
                                ).isoformat(),
                                "categories": [],
                                "origin": "finnhub",
                                "related": a.get("related", ""),
                            }
                        )

                # Also fetch forex/crypto for macro context
                res2 = await client.get(
                    "https://finnhub.io/api/v1/news",
                    params={"category": "forex", "token": self.finnhub_key},
                )
                if res2.status_code == 200:
                    for a in res2.json()[:5]:
                        articles.append(
                            {
                                "title": a.get("headline", ""),
                                "summary": a.get("summary", ""),
                                "source": a.get("source", "Finnhub"),
                                "url": a.get("url", ""),
                                "image": a.get("image", ""),
                                "time": datetime.fromtimestamp(
                                    a.get("datetime", time.time()), tz=timezone.utc
                                ).isoformat(),
                                "categories": ["Macro"],
                                "origin": "finnhub",
                                "related": a.get("related", ""),
                            }
                        )

            return articles if articles else None
        except Exception as e:
            logger.warning(f"[News] Finnhub error: {e}")
            return None

    async def _fetch_gnews(self, query='bonds OR treasury OR "interest rate"'):
        """Fetch from GNews API."""
        if not self.gnews_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://gnews.io/api/v4/search",
                    params={
                        "q": query,
                        "token": self.gnews_key,
                        "max": 15,
                        "lang": "en",
                        "topic": "business",
                    },
                )
                if res.status_code == 200:
                    data = res.json().get("articles", [])
                    articles = []
                    for a in data:
                        articles.append(
                            {
                                "title": a.get("title", ""),
                                "summary": a.get("description", ""),
                                "source": a.get("source", {}).get("name", "GNews"),
                                "url": a.get("url", ""),
                                "image": a.get("image", ""),
                                "time": a.get(
                                    "publishedAt",
                                    datetime.now(timezone.utc).isoformat(),
                                ),
                                "categories": [],
                                "origin": "gnews",
                            }
                        )
                    return articles if articles else None
        except Exception as e:
            logger.warning(f"[News] GNews error: {e}")
        return None

    async def _fetch_newsapi(self, query='bonds OR treasury OR fed OR "fixed income"'):
        """Fetch from NewsAPI."""
        if not self.newsapi_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "apiKey": self.newsapi_key,
                        "pageSize": 15,
                        "language": "en",
                        "sortBy": "publishedAt",
                    },
                )
                if res.status_code == 200:
                    data = res.json().get("articles", [])
                    articles = []
                    for a in data:
                        articles.append(
                            {
                                "title": a.get("title", ""),
                                "summary": a.get("description", ""),
                                "source": a.get("source", {}).get("name", "NewsAPI"),
                                "url": a.get("url", ""),
                                "image": a.get("urlToImage", ""),
                                "time": a.get(
                                    "publishedAt",
                                    datetime.now(timezone.utc).isoformat(),
                                ),
                                "categories": [],
                                "origin": "newsapi",
                            }
                        )
                    return articles if articles else None
        except Exception as e:
            logger.warning(f"[News] NewsAPI error: {e}")
        return None

    def _fetch_yahoo_rss(self):
        """Fetch from Yahoo Finance RSS — no API key needed."""
        feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^TNX&region=US&lang=en-US",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^TYX&region=US&lang=en-US",
        ]
        articles = []
        try:
            for feed_url in feeds:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    articles.append(
                        {
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "source": "Yahoo Finance",
                            "url": entry.get("link", ""),
                            "image": "",
                            "time": (
                                datetime(
                                    *entry.published_parsed[:6], tzinfo=timezone.utc
                                ).isoformat()
                                if hasattr(entry, "published_parsed")
                                and entry.published_parsed
                                else datetime.now(timezone.utc).isoformat()
                            ),
                            "categories": [],
                            "origin": "yahoo_rss",
                        }
                    )
            return articles if articles else None
        except Exception as e:
            logger.warning(f"[News] Yahoo RSS error: {e}")
            return None

    # ══════════════════════════════════════════════════════════════════════════
    # PIPELINE STAGES
    # ══════════════════════════════════════════════════════════════════════════

    def _deduplicate(self, articles):
        """Remove near-duplicate articles using title similarity."""
        if not articles:
            return []

        seen = []
        unique = []
        for article in articles:
            title = article.get("title", "").strip().lower()
            if not title:
                continue
            is_dup = False
            for seen_title in seen:
                if SequenceMatcher(None, title, seen_title).ratio() > 0.75:
                    is_dup = True
                    break
            if not is_dup:
                seen.append(title)
                unique.append(article)
        return unique

    def _categorize(self, article):
        """Assign categories based on keyword matching in title + summary."""
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()
        categories = list(article.get("categories", []))  # Keep existing

        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == "Portfolio Related":
                continue  # Handled separately in entity detection
            for kw in keywords:
                if kw in text:
                    if cat not in categories:
                        categories.append(cat)
                    break  # One match is enough per category

        # Default category if none matched
        if not categories:
            categories.append(
                "Market Moving"
                if any(w in text for w in ["market", "stock", "bond", "yield"])
                else "Macro"
            )

        article["categories"] = categories
        return article

    def _detect_entities(self, articles):
        """Match company/issuer/sector names from the bonds collection."""
        try:
            db = get_db()
            # Get unique issuers and sectors from bonds collection
            issuers = db["bonds"].distinct("issuer")
            sectors = db["bonds"].distinct("sector")

            issuer_lower = {i.lower(): i for i in issuers if i}
            sector_lower = {s.lower(): s for s in sectors if s}

            for article in articles:
                text = (
                    article.get("title", "") + " " + article.get("summary", "")
                ).lower()
                matched_issuers = []
                matched_sectors = []

                for il, original in issuer_lower.items():
                    # Match issuer names (at least 4 chars to avoid false positives)
                    if len(il) >= 4 and il in text:
                        matched_issuers.append(original)

                for sl, original in sector_lower.items():
                    if sl in text:
                        matched_sectors.append(original)

                article["matched_issuers"] = matched_issuers
                article["matched_sectors"] = matched_sectors

                if matched_issuers:
                    if "Portfolio Related" not in article.get("categories", []):
                        article["categories"].append("Portfolio Related")

        except Exception as e:
            logger.warning(f"[News] Entity detection error: {e}")

        return articles

    def _detect_macro_events(self, articles):
        """Flag articles related to macro events."""
        for article in articles:
            text = (article.get("title", "") + " " + article.get("summary", "")).lower()
            events = [ev for ev in MACRO_EVENTS if ev in text]
            article["macro_events"] = events
            article["is_macro"] = len(events) > 0
        return articles

    def _rank_articles(self, articles):
        """Rank articles by relevance score."""
        for article in articles:
            score = 0

            # Finance relevance
            text = (article.get("title", "") + " " + article.get("summary", "")).lower()
            finance_terms = [
                "bond",
                "yield",
                "treasury",
                "rate",
                "fed",
                "credit",
                "spread",
                "fixed income",
                "coupon",
                "maturity",
                "duration",
            ]
            score += sum(2 for term in finance_terms if term in text)

            # Category depth
            score += len(article.get("categories", [])) * 3

            # Entity matches
            score += len(article.get("matched_issuers", [])) * 5
            score += len(article.get("matched_sectors", [])) * 3

            # Macro event relevance
            score += len(article.get("macro_events", [])) * 4

            # Breaking / market-moving boost
            cats = article.get("categories", [])
            if "Breaking News" in cats:
                score += 15
            if "Market Moving" in cats:
                score += 10

            # Recency bonus (within last 6 hours)
            try:
                pub_time = datetime.fromisoformat(
                    article.get("time", "").replace("Z", "+00:00")
                )
                age_hours = (
                    datetime.now(timezone.utc) - pub_time
                ).total_seconds() / 3600
                if age_hours < 1:
                    score += 10
                elif age_hours < 6:
                    score += 5
                elif age_hours < 24:
                    score += 2
            except (ValueError, TypeError):
                pass

            # Source quality bonus
            origin = article.get("origin", "")
            if origin == "finnhub":
                score += 3  # Finance-focused source
            elif origin == "gnews":
                score += 2

            article["relevance_score"] = score

        articles.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)
        return articles

    # ══════════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ══════════════════════════════════════════════════════════════════════════

    def _store_articles(self, articles):
        """Store processed articles in MongoDB for caching and search."""
        if not articles:
            return
        try:
            db = get_db()
            now = datetime.now(timezone.utc).isoformat()
            for article in articles:
                # Use a hash of title + source as unique key
                article_id = hashlib.md5(
                    (article.get("title", "") + article.get("source", "")).encode()
                ).hexdigest()
                article["article_id"] = article_id
                article["fetched_at"] = now

                # Upsert to avoid duplicates
                db["news_articles"].update_one(
                    {"article_id": article_id},
                    {"$set": article},
                    upsert=True,
                )
            logger.info(f"[News] Stored {len(articles)} articles in MongoDB")
        except Exception as e:
            logger.warning(f"[News] MongoDB store error: {e}")

    def _get_cached_articles(self, limit=20):
        """Retrieve recently cached articles from MongoDB."""
        try:
            db = get_db()
            articles = list(
                db["news_articles"].find().sort("fetched_at", -1).limit(limit)
            )
            if articles:
                for a in articles:
                    a["_id"] = str(a["_id"])
                    a["cached"] = True
                logger.info(
                    f"[News] Loaded {len(articles)} cached articles from MongoDB"
                )
                return articles
        except Exception as e:
            logger.warning(f"[News] MongoDB cache read error: {e}")
        return None

    def _get_fallback_articles(self):
        """Absolute last resort — return system-generated status articles."""
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "title": "Treasury Yields: Monitor Live Rates on the Treasury Page",
                "summary": "Track real-time treasury yield movements across the full curve. "
                "Navigate to the Treasury section for live FRED data on all maturities.",
                "source": "YieldLens",
                "url": "",
                "image": "",
                "time": now,
                "categories": ["Treasury", "Rates"],
                "origin": "system",
                "relevance_score": 50,
                "macro_events": [],
                "matched_issuers": [],
                "matched_sectors": [],
                "cached": True,
                "system_note": "Using latest available market data",
            },
            {
                "title": "Federal Reserve Watch: Rate Decision and Policy Analysis",
                "summary": "Stay informed on Federal Reserve policy decisions and their impact "
                "on fixed income markets. Check the Macro section for latest indicators.",
                "source": "YieldLens",
                "url": "",
                "image": "",
                "time": now,
                "categories": ["Fed", "Rates", "Macro"],
                "origin": "system",
                "relevance_score": 45,
                "macro_events": ["fed"],
                "matched_issuers": [],
                "matched_sectors": [],
                "cached": True,
                "system_note": "Using latest available market data",
            },
            {
                "title": "Credit Markets Overview: IG and HY Spread Analysis",
                "summary": "Investment-grade and high-yield credit spreads provide key signals "
                "for bond investors. Review spread trends in the Analytics section.",
                "source": "YieldLens",
                "url": "",
                "image": "",
                "time": now,
                "categories": ["Corporate Credit", "Corporate Bonds"],
                "origin": "system",
                "relevance_score": 40,
                "macro_events": [],
                "matched_issuers": [],
                "matched_sectors": [],
                "cached": True,
                "system_note": "Using latest available market data",
            },
            {
                "title": "Portfolio Risk Monitor: Duration and Sector Exposure",
                "summary": "Analyze your portfolio's duration sensitivity and sector concentration. "
                "Use the Portfolio section for detailed risk analytics.",
                "source": "YieldLens",
                "url": "",
                "image": "",
                "time": now,
                "categories": ["Portfolio Related"],
                "origin": "system",
                "relevance_score": 35,
                "macro_events": [],
                "matched_issuers": [],
                "matched_sectors": [],
                "cached": True,
                "system_note": "Using latest available market data",
            },
        ]


# Singleton
news_service = NewsService()
