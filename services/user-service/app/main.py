"""User service main application module."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from cache import get_cache_client

from .config import settings
from .routers import health, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize cache client for user data
    app.state.cache_client = get_cache_client(
        redis_url=settings.redis_url,
        default_ttl=86400,  # 24 hours
        key_prefix="keiko:user",
    )
    await app.state.cache_client.connect()

    yield

    # Cleanup
    await app.state.cache_client.disconnect()


app = FastAPI(
    title="Keiko User Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(users.router, prefix="/api")

