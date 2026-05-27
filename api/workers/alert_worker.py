"""
"""Alert background worker for monitoring price/yield triggers."""

import logging
import time

from celery_app import celery_app
from database.mongo import get_db
from events.dispatcher import ALERT_TRIGGERED, dispatcher

logger = logging.getLogger("yieldlens.workers.alert")


@celery_app.task
def check_alerts():
    """Check user alerts against current market data."""
    db = get_db()
    active_alerts = list(db["alerts"].find({"status": "active"}))
    if not active_alerts:
        return True

    logger.info(f"Checking {len(active_alerts)} active alerts")
    triggered_count = 0

    for alert in active_alerts:
        try:
            target = alert.get("target")
            if not target:
                continue

            # For simplicity, we assume target is a bond_id or cusip
            # In a real system, it could be a macro indicator or sector average
            bond = db["bonds"].find_one({"_id": target})
            if not bond:
                bond = db["bonds"].find_one({"cusip": target})

            if not bond:
                continue

            current_yield = bond.get(
                "coupon_rate", 0
            )  # Approximation using coupon or fetch YTM if stored
            threshold = float(alert.get("threshold", 0))
            condition = alert.get("condition", "above")

            is_triggered = False
            if condition == "above" and current_yield > threshold:
                is_triggered = True
            elif condition == "below" and current_yield < threshold:
                is_triggered = True

            if is_triggered:
                # Mark as triggered
                triggered_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                db["alerts"].update_one(
                    {"_id": alert["_id"]},
                    {"$set": {"status": "triggered", "triggered_at": triggered_time}},
                )

                # Emit event
                dispatcher.emit(
                    ALERT_TRIGGERED,
                    {
                        "alert_id": str(alert["_id"]),
                        "user_id": alert.get("user_id"),
                        "target": target,
                        "value": current_yield,
                        "threshold": threshold,
                        "condition": condition,
                        "timestamp": triggered_time,
                    },
                )
                triggered_count += 1
        except Exception as e:
            logger.error(f"Error checking alert {alert.get('_id')}: {e}")

    if triggered_count > 0:
        logger.info(f"Triggered {triggered_count} alerts")

    return True
