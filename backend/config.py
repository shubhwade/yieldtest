"""
YieldLens Configuration Module
Loads environment variables from .env file with sensible defaults.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/yieldlens")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "yieldlens")

    # API Keys
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    GNEWS_API_KEY: str = os.getenv("GNEWS_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "yieldlens-super-secret-key-change-in-production"
    )
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Flask
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    # WARNING: Never enable FLASK_DEBUG in a production environment! It exposes the Werkzeug interactive debugger which allows arbitrary code execution.
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Security & Rate Limiting
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "200 per day")
    RATE_LIMIT_AI_QUERY: str = os.getenv("RATE_LIMIT_AI_QUERY", "50 per hour")

    # Cache TTLs (in seconds)
    FRED_CACHE_TTL: int = int(os.getenv("FRED_CACHE_TTL", "3600"))  # 1 hour
    TREASURY_CACHE_TTL: int = int(os.getenv("TREASURY_CACHE_TTL", "14400"))  # 4 hours
    AI_CACHE_TTL: int = int(os.getenv("AI_CACHE_TTL", "86400"))  # 24 hours
    DEFAULT_CACHE_TTL: int = int(os.getenv("DEFAULT_CACHE_TTL", "3600"))  # 1 hour
    NEWS_CACHE_TTL: int = int(os.getenv("NEWS_CACHE_TTL", "300"))  # 5 minutes
    NEWS_REFRESH_INTERVAL: int = int(
        os.getenv("NEWS_REFRESH_INTERVAL", "60")
    )  # 1 minute

    # OpenRouter model rotation for AI failover
    OPENROUTER_MODELS: list = [
        "google/gemini-flash-1.5",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
    ]
