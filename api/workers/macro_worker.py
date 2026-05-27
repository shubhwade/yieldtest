"""
"""Macro background worker for economic indicators."""

import logging

from celery_app import celery_app
from events.dispatcher import dispatcher
from services.fred_service import fred_service

logger = logging.getLogger("yieldlens.workers.macro")


@celery_app.task
def refresh_macro_indicators():
    """Fetch key economic data (CPI, GDP, Unemployment)."""
    indicators = fred_service.get_economic_indicators()

    if indicators:
        dispatcher.emit("MACRO_UPDATED", indicators)
        logger.info("Macro economic indicators updated successfully")

    return True
