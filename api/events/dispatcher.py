"""
Event Dispatcher System
Enables decoupled cross-module communication for YieldLens ecosystem.
"""

import logging
from typing import Callable, Dict, List

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YieldLens.Events")


class EventDispatcher:
    _instance = None
    _listeners: Dict[str, List[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventDispatcher, cls).__new__(cls)
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable = None):
        """Subscribe a listener to an event type. Can be used as a decorator."""

        def decorator(cb):
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            if cb not in self._listeners[event_type]:
                self._listeners[event_type].append(cb)
                logger.info(f"Listener subscribed to event: {event_type}")
            return cb

        if callback is None:
            return decorator
        return decorator(callback)

    def emit(self, event_type: str, data: dict = None):
        """Emit an event to all subscribed listeners."""
        logger.info(f"Emitting event: {event_type} with data: {data}")
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in listener for {event_type}: {str(e)}")


# Global singleton instance
dispatcher = EventDispatcher()

# Event Constants
BOND_ADDED = "BondAdded"
HOLDING_ADDED = "HoldingAdded"
PORTFOLIO_UPDATED = "PortfolioUpdated"
WATCHLIST_UPDATED = "WatchlistUpdated"
ALERT_TRIGGERED = "AlertTriggered"
TREASURY_UPDATED = "TreasuryUpdated"
MACRO_UPDATED = "MacroUpdated"
AI_ANALYSIS_GENERATED = "AIAnalysisGenerated"
NEWS_UPDATED = "NewsUpdated"
NEWS_BREAKING = "NewsBreaking"
NEWS_PORTFOLIO_MATCH = "NewsPortfolioMatch"
DASHBOARD_UPDATED = "DashboardUpdated"
