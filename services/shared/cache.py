"""Redis cache client with async support and TTL management.

This module provides a unified Redis caching interface for all services.
"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheClient:
    """Async Redis cache client with TTL support."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        key_prefix: str = "keiko",
    ):
        """Initialize the cache client.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            key_prefix: Prefix for all cache keys (default: "keiko")
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Successfully connected to Redis")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.aclose()
            logger.info("Disconnected from Redis")

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key.

        Args:
            key: The base key

        Returns:
            str: Prefixed key
        """
        return f"{self.key_prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found
        """
        if not self._client:
            logger.warning("Redis client not connected")
            return None

        try:
            value = await self._client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default_ttl if not specified)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected")
            return False

        try:
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            serialized_value = json.dumps(value)
            await self._client.setex(
                self._make_key(key), ttl_seconds, serialized_value
            )
            return True
        except RedisError as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing value for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            bool: True if key was deleted, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected")
            return False

        try:
            result = await self._client.delete(self._make_key(key))
            return result > 0
        except RedisError as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            bool: True if key exists, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected")
            return False

        try:
            result = await self._client.exists(self._make_key(key))
            return result > 0
        except RedisError as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False

