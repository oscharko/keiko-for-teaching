"""Search service main application module."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from fastapi import FastAPI


from shared.azure_identity import get_azure_credential
from shared.cache import get_cache_client

from .config import settings
from .routers import health, search


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize Azure AI Search client with Managed Identity
    credential = get_azure_credential(
        managed_identity_client_id=settings.azure_client_id
    )
    
    app.state.search_client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
        api_version=settings.azure_search_api_version,
    )

    # Initialize cache client
    app.state.cache_client = get_cache_client(
        redis_url=settings.redis_url,
        default_ttl=settings.cache_ttl,
        key_prefix="keiko:search",
    )
    await app.state.cache_client.connect()

    yield

    # Cleanup
    await app.state.search_client.close()
    await app.state.cache_client.disconnect()


app = FastAPI(
    title="Keiko Search Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(search.router, prefix="/api")

