"""Cache utilities for chat responses."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from cache import CacheClient


def generate_cache_key(messages: list[dict[str, str]], **kwargs) -> str:
    """Generate a cache key from messages and parameters.

    Args:
        messages: List of chat messages
        **kwargs: Additional parameters (temperature, etc.)

    Returns:
        str: Cache key
    """
    # Create a deterministic representation
    cache_data = {
        "messages": messages,
        "params": {k: v for k, v in sorted(kwargs.items()) if v is not None},
    }

    # Generate hash
    cache_str = json.dumps(cache_data, sort_keys=True)
    cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()

    return f"chat:response:{cache_hash}"


async def get_cached_response(
    cache_client: CacheClient,
    messages: list[dict[str, str]],
    **kwargs
) -> dict[str, Any] | None:
    """Get cached chat response if available.

    Args:
        cache_client: Cache client instance
        messages: List of chat messages
        **kwargs: Additional parameters

    Returns:
        Optional[dict]: Cached response or None
    """
    cache_key = generate_cache_key(messages, **kwargs)
    return await cache_client.get(cache_key)


async def cache_response(
    cache_client: CacheClient,
    messages: list[dict[str, str]],
    response: dict[str, Any],
    ttl: int = 3600,
    **kwargs
) -> bool:
    """Cache a chat response.

    Args:
        cache_client: Cache client instance
        messages: List of chat messages
        response: Response to cache
        ttl: Time-to-live in seconds (default: 1 hour)
        **kwargs: Additional parameters

    Returns:
        bool: True if cached successfully
    """
    cache_key = generate_cache_key(messages, **kwargs)
    return await cache_client.set(cache_key, response, ttl=ttl)

