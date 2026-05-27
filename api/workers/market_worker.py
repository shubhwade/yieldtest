"""
"""Market background worker for dashboard aggregation."""

import logging

from celery_app import celery_app
from database.mongo import get_db
from events.dispatcher import dispatcher
from services.market_data_service import market_data_service

logger = logging.getLogger("yieldlens.workers.market")


@celery_app.task
def refresh_dashboard():
    """Update global dashboard state."""
    db = get_db()
    data = market_data_service.get_dashboard_data(db)

    if data:
        dispatcher.emit("DASHBOARD_UPDATED", data)
        logger.info("Global dashboard updated successfully")

    return True
