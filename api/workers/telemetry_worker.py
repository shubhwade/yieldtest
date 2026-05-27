"""
YieldLens Telemetry Worker
Handles background data refreshing and telemetry if Celery/Redis is unavailable.
"""

import logging
import threading
import time

logger = logging.getLogger("yieldlens.workers.telemetry")

def start_fallback_scheduler():
    """Start a lightweight fallback background thread for data freshness."""
    def fallback_scheduler():
        time.sleep(10)  # initial delay to let server start up
        logger.info(
            "Telemetry Scheduler: fallback background thread active and monitoring data freshness."
        )
        while True:
            try:
                from workers.news_worker import refresh_news
                refresh_news()
            except Exception as e:
                logger.debug(f"Error in fallback news refresh: {e}")
            
            try:
                from workers.market_worker import refresh_dashboard
                refresh_dashboard()
            except Exception as e:
                logger.debug(f"Error in fallback market refresh: {e}")
            
            time.sleep(30)  # Poll/refresh every 30 seconds

    scheduler_thread = threading.Thread(target=fallback_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread
