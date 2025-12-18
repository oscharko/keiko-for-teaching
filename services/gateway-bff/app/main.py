"""Gateway BFF main application module."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from cache import get_cache_client

from .config import settings
from .middleware import SessionMiddleware
from .routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize cache client
    app.state.cache_client = get_cache_client(
        redis_url=settings.redis_url,
        default_ttl=3600,
        key_prefix="keiko:gateway",
    )
    await app.state.cache_client.connect()

    yield

    # Cleanup
    await app.state.http_client.aclose()
    await app.state.cache_client.disconnect()


app = FastAPI(
    title="Keiko Gateway BFF",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    redis_url=settings.redis_url,
    session_ttl=3600,  # 1 hour
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")

