"""
Centralized Data Cache using Redis.
Provides low-latency access to market data and shared application state.
"""

import json
import logging

import redis
from config import Config

logger = logging.getLogger("YieldLens.Cache")


class RedisCache:
    def __init__(self):
        self.url = Config.REDIS_URL
        try:
            self.client = redis.from_url(self.url, decode_responses=True)
            self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.client = None

    def get(self, key):
        if not self.client:
            return None
        try:
            val = self.client.get(key)
            return json.loads(val) if val else None
        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key, value, ttl=3600):
        if not self.client:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key):
        if not self.client:
            return
        self.client.delete(key)


cache = RedisCache()
