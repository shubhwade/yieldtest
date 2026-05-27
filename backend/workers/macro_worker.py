"""
Macro background worker for economic indicators.
"""

from celery_app import celery_app
from events.dispatcher import dispatcher
from services.fred_service import fred_service


@celery_app.task
def refresh_macro_indicators():
    """Fetch key economic data (CPI, GDP, Unemployment)."""
    indicators = fred_service.get_economic_indicators()

    if indicators:
        dispatcher.emit("MACRO_UPDATED", indicators)
        print(f"[Worker] Refreshed Macro Indicators")

    return True
