"""Chat service main application module."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from azure.identity import get_bearer_token_provider
from fastapi import FastAPI
from openai import AsyncAzureOpenAI


from shared.azure_identity import get_azure_credential
from shared.cache import get_cache_client

from .config import settings
from .routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize legacy Azure OpenAI client if needed (for backward compatibility)
    if settings.use_legacy_openai:
        if settings.azure_openai_api_key:
            # Local development with API key
            app.state.openai_client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
        else:
            # Production with Managed Identity
            credential = get_azure_credential(
                managed_identity_client_id=settings.azure_client_id
            )
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            app.state.openai_client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_ad_token_provider=token_provider,
                api_version=settings.azure_openai_api_version,
            )
    else:
        # Microsoft Foundry is the default (no separate client initialization needed)
        # The FoundryClient is initialized in ChatService
        app.state.openai_client = None

    # Initialize cache client
    app.state.cache_client = get_cache_client(
        redis_url=getattr(settings, "redis_url", "redis://localhost:6379"),
        default_ttl=3600,
        key_prefix="keiko:chat",
    )
    await app.state.cache_client.connect()

    # Initialize HTTP client for calling other services (e.g., search service)
    app.state.http_client = httpx.AsyncClient()

    yield

    # Cleanup
    if app.state.openai_client:
        await app.state.openai_client.close()
    await app.state.cache_client.disconnect()
    await app.state.http_client.aclose()


app = FastAPI(
    title="Keiko Chat Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")

