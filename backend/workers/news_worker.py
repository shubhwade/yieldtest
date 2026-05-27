"""
News background worker — full ingestion pipeline.
Runs on Celery beat schedule to continuously refresh news.

Pipeline:
  Fetch all sources → Deduplicate → Categorize → Detect entities →
  Rank → Generate AI summaries → Store MongoDB → Emit Socket events
"""

import asyncio
import logging

from celery_app import celery_app
from database.cache import cache
from events.dispatcher import NEWS_BREAKING, NEWS_UPDATED, dispatcher
from ai.service import ai_service
from services.news_service import news_service

logger = logging.getLogger("yieldlens.workers.news")


def _run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def refresh_news(self):
    """
    Full news ingestion pipeline — runs every 60 seconds via Celery beat.
    Fetches from ALL available sources, processes, and broadcasts.
    """
    try:
        # 1. Fetch from all available sources (parallel)
        all_articles = _run_async(news_service.fetch_all_sources())

        if not all_articles:
            # Try failover
            all_articles = _run_async(
                news_service._fetch_with_failover("fixed income bonds")
            )

        if not all_articles:
            logger.warning("[NewsWorker] No articles from any source")
            return 0

        # 2. Full pipeline processing
        articles = news_service._deduplicate(all_articles)
        articles = [news_service._categorize(a) for a in articles]
        articles = news_service._detect_entities(articles)
        articles = news_service._detect_macro_events(articles)
        articles = news_service._rank_articles(articles)

        # 3. Generate AI summary for top articles
        top_articles = articles[:5]
        try:
            summary = ai_service.generate_news_summary(top_articles)
            if summary:
                cache.set("news_ai_summary", summary, ttl=300)
        except Exception as e:
            logger.warning(f"[NewsWorker] AI summary failed: {e}")

        # 4. Store in MongoDB
        news_service._store_articles(articles[:30])

        # 5. Cache the latest set
        cache.set("news_latest", articles[:20], ttl=300)

        # 6. Identify trending/breaking
        breaking = [a for a in articles if "Breaking News" in a.get("categories", [])]
        trending = [a for a in articles if "Market Moving" in a.get("categories", [])]
        cache.set("news_trending", (breaking + trending)[:10], ttl=300)

        # 7. Emit events for real-time push
        dispatcher.emit(
            NEWS_UPDATED,
            {
                "news": articles[:15],
                "count": len(articles),
            },
        )

        if breaking:
            dispatcher.emit(
                NEWS_BREAKING,
                {
                    "articles": breaking[:5],
                    "count": len(breaking),
                },
            )

        logger.info(
            f"[NewsWorker] Pipeline complete: {len(articles)} articles "
            f"({len(breaking)} breaking, {len(trending)} trending)"
        )
        return len(articles)

    except Exception as e:
        logger.error(f"[NewsWorker] Pipeline error: {e}")
        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("[NewsWorker] Max retries exceeded")
        return 0
