"""
Real-time Socket System
Pushes market updates and ecosystem events to connected clients.
"""

import logging

from flask_socketio import SocketIO

logger = logging.getLogger("YieldLens.Sockets")

# Global SocketIO instance
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def push_event(event_type: str, data: dict):
    """Push a real-time update to all connected clients."""
    logger.info(f"Pushing Socket event: {event_type}")
    socketio.emit(event_type, data)


# Handlers for system events to bridge EDA to Sockets
def init_socket_listeners():
    from events.dispatcher import (
        AI_ANALYSIS_GENERATED,
        DASHBOARD_UPDATED,
        HOLDING_ADDED,
        MACRO_UPDATED,
        NEWS_BREAKING,
        NEWS_PORTFOLIO_MATCH,
        NEWS_UPDATED,
        PORTFOLIO_UPDATED,
        TREASURY_UPDATED,
        dispatcher,
    )

    @dispatcher.subscribe(TREASURY_UPDATED)
    def on_treasury_move(data):
        push_event("market_update", data)

    @dispatcher.subscribe(NEWS_UPDATED)
    def on_news_update(data):
        push_event("news_refresh", data)

    @dispatcher.subscribe(NEWS_BREAKING)
    def on_breaking_news(data):
        push_event("news_breaking", data)

    @dispatcher.subscribe(NEWS_PORTFOLIO_MATCH)
    def on_portfolio_news(data):
        push_event("news_portfolio_match", data)

    @dispatcher.subscribe(DASHBOARD_UPDATED)
    def on_dashboard_update(data):
        push_event("dashboard_refresh", data)

    @dispatcher.subscribe(MACRO_UPDATED)
    def on_macro_update(data):
        push_event("macro_refresh", data)

    @dispatcher.subscribe(HOLDING_ADDED)
    def on_holding(data):
        push_event("portfolio_activity", {"type": "add", "data": data})

    @dispatcher.subscribe(PORTFOLIO_UPDATED)
    def on_portfolio(data):
        push_event("portfolio_refresh", data)

    @dispatcher.subscribe(AI_ANALYSIS_GENERATED)
    def on_ai_update(data):
        push_event("ai_brief_update", data)
