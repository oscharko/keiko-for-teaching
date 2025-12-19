"""Auth service main application module."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI


from shared.cache import get_cache_client

from .config import settings
from .routers import auth, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize cache client for session management
    app.state.cache_client = get_cache_client(
        redis_url=settings.redis_url_computed,
        default_ttl=settings.jwt_expiration_minutes * 60,
        key_prefix="keiko:auth",
    )
    await app.state.cache_client.connect()

    yield

    # Cleanup
    await app.state.cache_client.disconnect()


app = FastAPI(
    title="Keiko Auth Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")

