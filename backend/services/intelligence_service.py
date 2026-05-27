"""
Product Intelligence Service
Listens to system events and generates insights, recommendations, and activity logs.
Bridges news events to portfolio context for cross-referencing.
"""

import logging

from database.mongo import get_db
from events.dispatcher import (
    AI_ANALYSIS_GENERATED,
    HOLDING_ADDED,
    NEWS_BREAKING,
    NEWS_PORTFOLIO_MATCH,
    NEWS_UPDATED,
    PORTFOLIO_UPDATED,
    TREASURY_UPDATED,
    dispatcher,
)
from ai.service import ai_service

logger = logging.getLogger("YieldLens.Intelligence")


class IntelligenceService:
    def __init__(self):
        # Subscribe to key events
        dispatcher.subscribe(HOLDING_ADDED, self.on_holding_added)
        dispatcher.subscribe(PORTFOLIO_UPDATED, self.on_portfolio_updated)
        dispatcher.subscribe(TREASURY_UPDATED, self.on_treasury_move)
        dispatcher.subscribe(NEWS_UPDATED, self.on_news_updated)
        dispatcher.subscribe(NEWS_BREAKING, self.on_breaking_news)

    def on_holding_added(self, data):
        """React to new holding added."""
        logger.info(f"Intelligence reacting to new holding: {data}")
        db = get_db()
        # 1. Log Activity
        db["activity_logs"].insert_one(
            {
                "type": "HOLDING_ADDED",
                "portfolio_id": data.get("portfolio_id"),
                "bond_id": data.get("holding", {}).get("bond_id"),
                "timestamp": data.get("holding", {}).get("added_at"),
            }
        )

        # 2. Generate Recommendation if needed
        # (Example: check if portfolio is now too concentrated)

    def on_portfolio_updated(self, data):
        """React to general portfolio changes."""
        logger.info(f"Intelligence processing portfolio update: {data}")
        # Recalculate portfolio-level risk scores or cached analytics

    def on_treasury_move(self, data):
        """React to significant treasury market movements."""
        logger.info(f"Intelligence processing treasury move: {data}")
        # Generate new market brief automatically when rates move
        brief = ai_service.generate_market_brief()
        dispatcher.emit(AI_ANALYSIS_GENERATED, {"brief": brief})

    def on_news_updated(self, data):
        """React to news updates — cross-reference against portfolios."""
        logger.info(
            f"Intelligence processing news update: {data.get('count', 0)} articles"
        )
        try:
            articles = data.get("news", [])
            if not articles:
                return

            db = get_db()

            # Get all portfolio issuers
            portfolios = list(db["portfolios"].find().limit(10))
            portfolio_issuers = set()
            for pf in portfolios:
                for h in pf.get("holdings", []):
                    bond_id = h.get("bond_id")
                    if bond_id:
                        bond = db["bonds"].find_one({"_id": bond_id})
                        if bond and bond.get("issuer"):
                            portfolio_issuers.add(bond["issuer"].lower())

            if not portfolio_issuers:
                return

            # Check if any news matches portfolio holdings
            matching_articles = []
            for article in articles:
                matched = article.get("matched_issuers", [])
                for issuer in matched:
                    if issuer.lower() in portfolio_issuers:
                        matching_articles.append(article)
                        break

            if matching_articles:
                logger.info(
                    f"[Intelligence] {len(matching_articles)} articles match portfolio holdings"
                )
                dispatcher.emit(
                    NEWS_PORTFOLIO_MATCH,
                    {
                        "articles": matching_articles[:5],
                        "count": len(matching_articles),
                    },
                )

                # Log activity
                for article in matching_articles[:3]:
                    db["activity_logs"].insert_one(
                        {
                            "type": "NEWS_PORTFOLIO_MATCH",
                            "title": article.get("title", ""),
                            "matched_issuers": article.get("matched_issuers", []),
                            "categories": article.get("categories", []),
                        }
                    )

        except Exception as e:
            logger.error(f"[Intelligence] News cross-reference error: {e}")

    def on_breaking_news(self, data):
        """React to breaking news — trigger AI brief regeneration."""
        logger.info(
            f"Intelligence processing breaking news: {data.get('count', 0)} articles"
        )
        try:
            # Regenerate market brief when breaking news arrives
            brief = ai_service.generate_market_brief()
            dispatcher.emit(AI_ANALYSIS_GENERATED, {"brief": brief})
        except Exception as e:
            logger.error(f"[Intelligence] Breaking news handler error: {e}")


# Initialize global intelligence
intelligence_service = IntelligenceService()
