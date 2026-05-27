"""News routes — market briefs, categories, search, portfolio news."""

import asyncio
import logging

from flask import Blueprint, jsonify, request
from services.ai_service import ai_service
from services.fred_service import fred_service
from services.news_service import news_service

logger = logging.getLogger("YieldLens.NewsRoutes")

news_bp = Blueprint("news", __name__, url_prefix="/api/v1/news")


def _run_async(coro):
    """Helper to run async code in sync Flask routes."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=30)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@news_bp.route("/latest", methods=["GET"])
def get_latest_news():
    """Get latest news with full pipeline processing."""
    try:
        query = request.args.get("q", "fixed income bonds")
        limit = min(int(request.args.get("limit", "20")), 50)
        news = _run_async(news_service.fetch_news(query=query, limit=limit))
        return jsonify({"success": True, "data": news})
    except Exception as e:
        logger.error(f"[News] /latest error: {e}")
        # Even on error, never return empty
        fallback = (
            news_service._get_cached_articles(20)
            or news_service._get_fallback_articles()
        )
        return jsonify(
            {
                "success": True,
                "data": fallback,
                "notice": "Using latest available market data",
            }
        )


@news_bp.route("/brief", methods=["GET"])
def get_market_brief():
    """Get AI-generated daily market brief."""
    try:
        treasury_data = fred_service.get_yield_curve()
        macro_data = fred_service.get_economic_indicators()
        brief = ai_service.generate_market_brief(treasury_data, macro_data)
        return jsonify({"success": True, "data": {"brief": brief}})
    except Exception as e:
        logger.error(f"[News] /brief error: {e}")
        return jsonify(
            {
                "success": True,
                "data": {"brief": ai_service.generate_market_brief()},
            }
        )


@news_bp.route("/category/<category>", methods=["GET"])
def get_by_category(category):
    """Get news filtered by category."""
    try:
        limit = min(int(request.args.get("limit", "15")), 50)
        articles = news_service.get_by_category(category, limit=limit)
        return jsonify({"success": True, "data": articles})
    except Exception as e:
        logger.error(f"[News] /category error: {e}")
        return jsonify({"success": True, "data": news_service._get_fallback_articles()})


@news_bp.route("/search", methods=["GET"])
def search_news():
    """Search news articles by keyword."""
    try:
        keyword = request.args.get("q", "")
        if not keyword:
            return (
                jsonify({"success": False, "error": "query parameter 'q' required"}),
                400,
            )
        limit = min(int(request.args.get("limit", "20")), 50)
        articles = news_service.search_news(keyword, limit=limit)
        return jsonify({"success": True, "data": articles})
    except Exception as e:
        logger.error(f"[News] /search error: {e}")
        return jsonify({"success": True, "data": []})


@news_bp.route("/portfolio", methods=["GET"])
def get_portfolio_news():
    """Get news relevant to user's portfolio holdings."""
    try:
        articles = _run_async(news_service.get_portfolio_news())
        return jsonify({"success": True, "data": articles})
    except Exception as e:
        logger.error(f"[News] /portfolio error: {e}")
        fallback = (
            news_service._get_cached_articles(20)
            or news_service._get_fallback_articles()
        )
        return jsonify({"success": True, "data": fallback})


@news_bp.route("/trending", methods=["GET"])
def get_trending_news():
    """Get trending and breaking news."""
    try:
        limit = min(int(request.args.get("limit", "10")), 30)
        articles = news_service.get_trending(limit=limit)
        return jsonify({"success": True, "data": articles})
    except Exception as e:
        logger.error(f"[News] /trending error: {e}")
        return jsonify({"success": True, "data": news_service._get_fallback_articles()})
