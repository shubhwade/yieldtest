"""
YieldLens MongoDB Connection Manager
Handles database connection, initialization, and index creation.
"""

import logging

from config import Config
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

logger = logging.getLogger("yieldlens.db")

_client: MongoClient | None = None
_db: Database | None = None


def get_db() -> Database:
    """Return the MongoDB database instance. Initializes connection if needed."""
    global _client, _db
    if _db is None:
        _client = MongoClient(Config.MONGODB_URI)
        _db = _client[Config.MONGODB_DB_NAME]
    return _db


def get_client() -> MongoClient:
    """Return the MongoDB client instance."""
    global _client
    if _client is None:
        get_db()
    return _client  # type: ignore


def init_db() -> None:
    """
    Initialize the database: create collections and indexes.
    Called once on application startup.
    """
    db = get_db()

    # ── Users collection ──
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    db.users.create_index([("email", ASCENDING)], unique=True, background=True)

    # ── Bonds collection (seeded data) ──
    if "bonds" not in db.list_collection_names():
        db.create_collection("bonds")
    db.bonds.create_index([("type", ASCENDING)], background=True)
    db.bonds.create_index([("sector", ASCENDING)], background=True)
    db.bonds.create_index([("issuer", ASCENDING)], background=True)
    db.bonds.create_index([("coupon_rate", ASCENDING)], background=True)
    db.bonds.create_index([("maturity_date", ASCENDING)], background=True)
    db.bonds.create_index([("rating", ASCENDING)], background=True)
    db.bonds.create_index([("state", ASCENDING)], background=True)
    db.bonds.create_index([("callable", ASCENDING)], background=True)
    db.bonds.create_index([("tax_exempt", ASCENDING)], background=True)

    # ── Portfolios collection ──
    if "portfolios" not in db.list_collection_names():
        db.create_collection("portfolios")
    db.portfolios.create_index([("user_id", ASCENDING)], background=True)
    db.portfolios.create_index(
        [("user_id", ASCENDING), ("name", ASCENDING)], background=True
    )

    # ── Watchlists collection ──
    if "watchlists" not in db.list_collection_names():
        db.create_collection("watchlists")
    db.watchlists.create_index([("user_id", ASCENDING)], background=True)

    # ── Alerts collection ──
    if "alerts" not in db.list_collection_names():
        db.create_collection("alerts")
    db.alerts.create_index([("user_id", ASCENDING)], background=True)

    db.alerts.create_index([("triggered", ASCENDING)], background=True)

    # ── Settings collection ──
    if "settings" not in db.list_collection_names():
        db.create_collection("settings")
    db.settings.create_index([("user_id", ASCENDING)], unique=True, background=True)

    logger.info("MongoDB initialized with indexes.")


def close_db() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")
