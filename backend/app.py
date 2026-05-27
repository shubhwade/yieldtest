"""
YieldLens Backend — Flask Application Entry Point
Bloomberg-style fixed-income intelligence platform.
"""

import eventlet

eventlet.monkey_patch()

import logging
import os
import sys

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yieldlens")

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from config import Config
from database.mongo import get_db, init_db
from database.seed import seed_database
from events.sockets import init_socket_listeners, socketio
from flask import Flask, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Register all route blueprints
    from routes.ai_routes import ai_bp
    from routes.alerts_routes import alerts_bp
    from routes.analytics_routes import analytics_bp
    from routes.auth_routes import auth_bp
    from routes.backtest_routes import backtest_bp
    from routes.bonds_routes import bonds_bp
    from routes.credit_routes import credit_bp
    from routes.fred_routes import fred_bp
    from routes.macro_routes import macro_bp
    from routes.market_routes import market_bp
    from routes.news_routes import news_bp
    from routes.portfolio_routes import portfolio_bp
    from routes.screener_routes import screener_bp
    from routes.search_routes import search_bp
    from routes.telemetry_routes import telemetry_bp
    from routes.watchlist_routes import watchlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(fred_bp)
    app.register_blueprint(bonds_bp)
    app.register_blueprint(screener_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(credit_bp)
    app.register_blueprint(macro_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(search_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    # Health check
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        try:
            db = get_db()
            bond_count = db["bonds"].count_documents({})
            user_count = db["users"].count_documents({})
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "status": "healthy",
                        "service": "YieldLens API",
                        "version": "1.0.0",
                        "bonds_loaded": bond_count,
                        "users": user_count,
                        "fred_api": (
                            "configured" if Config.FRED_API_KEY else "not configured"
                        ),
                        "gemini_api": (
                            "configured"
                            if Config.GEMINI_API_KEY
                            else "not configured (using fallbacks)"
                        ),
                    },
                }
            )
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"Database connection error: {e}"}),
                500,
            )

    # Initialize database and seed on startup
    with app.app_context():
        try:
            init_db()
            db = get_db()
            seed_database(db)
            logger.info("=" * 60)
            logger.info("  YIELDLENS API Server")
            logger.info("=" * 60)
            logger.info(f"  URL:       http://localhost:{Config.FLASK_PORT}")
            logger.info(f"  Bonds:     {db['bonds'].count_documents({})} loaded")
            logger.info(
                f"  FRED API:  {'Configured' if Config.FRED_API_KEY else 'Not set'}"
            )
            logger.info(
                f"  Gemini AI: {'Configured' if Config.GEMINI_API_KEY else 'Using fallbacks'}"
            )
            logger.info(f"  MongoDB:   {Config.MONGODB_URI}")
            logger.info("=" * 60)
        except Exception as e:
            logger.warning(f"Database initialization error: {e}")
            logger.warning("  Make sure MongoDB is running on localhost:27017")
            logger.warning("  Install: https://www.mongodb.com/try/download/community")

    # Initialize System Services

    # Initialize Sockets
    socketio.init_app(app)
    init_socket_listeners()

    # Start a robust lightweight fallback background thread if Redis/Celery isn't running or configured
    import threading
    import time

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
                pass
            try:
                from workers.market_worker import refresh_dashboard

                refresh_dashboard()
            except Exception as e:
                pass
            time.sleep(30)  # Poll/refresh every 30 seconds

    scheduler_thread = threading.Thread(target=fallback_scheduler, daemon=True)
    scheduler_thread.start()

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(
        app,
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
