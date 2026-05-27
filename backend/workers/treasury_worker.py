"""
Treasury background worker for yield curve updates.
"""

from celery_app import celery_app
from events.dispatcher import dispatcher
from services.fred_service import fred_service
from services.treasury_service import treasury_service


@celery_app.task
def refresh_treasury_data():
    """Fetch latest treasury yields and auctions."""
    # Force refresh by bypassing cache or letting service update cache
    # The services already update Redis cache on fetch
    curve = fred_service.get_yield_curve()
    auctions = treasury_service.get_auction_data()

    if curve:
        dispatcher.emit("TREASURY_UPDATED", {"curve": curve, "auctions": auctions})
        print(f"[Worker] Refreshed Treasury Yield Curve")

    return True
