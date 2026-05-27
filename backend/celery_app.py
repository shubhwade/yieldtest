"""
Celery configuration and background worker initialization.
"""

from celery import Celery
from config import Config


def make_celery(app_name="yieldlens"):
    """Initialize Celery application."""
    celery = Celery(
        app_name,
        broker=Config.REDIS_URL,
        backend=Config.REDIS_URL,
        include=[
            "workers.news_worker",
            "workers.market_worker",
            "workers.treasury_worker",
            "workers.macro_worker",
            "workers.alert_worker",
        ],
    )

    celery.conf.update(
        result_expires=3600,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        beat_schedule={
            "refresh-news-every-minute": {
                "task": "workers.news_worker.refresh_news",
                "schedule": 60.0,
            },
            "refresh-treasury-every-30s": {
                "task": "workers.treasury_worker.refresh_treasury_data",
                "schedule": 30.0,
            },
            "refresh-macro-every-hour": {
                "task": "workers.macro_worker.refresh_macro_indicators",
                "schedule": 3600.0,
            },
            "refresh-dashboard-every-30s": {
                "task": "workers.market_worker.refresh_dashboard",
                "schedule": 30.0,
            },
            "check-alerts-every-60s": {
                "task": "workers.alert_worker.check_alerts",
                "schedule": 60.0,
            },
        },
    )

    return celery


celery_app = make_celery()
