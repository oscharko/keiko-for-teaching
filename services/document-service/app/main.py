"""Document service main application module."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from azure.storage.blob.aio import BlobServiceClient
from fastapi import FastAPI


from shared.azure_identity import get_azure_credential
from shared.cache import get_cache_client

from .config import settings
from .routers import documents, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    # Initialize Azure Blob Storage client with Managed Identity
    credential = get_azure_credential(
        managed_identity_client_id=settings.azure_client_id
    )
    
    account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
    app.state.blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential=credential,
    )

    # Initialize HTTP client for calling other services
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize cache client
    app.state.cache_client = get_cache_client(
        redis_url=settings.redis_url_computed,
        default_ttl=3600,
        key_prefix="keiko:document",
    )
    await app.state.cache_client.connect()

    yield

    # Cleanup
    await app.state.blob_service_client.close()
    await app.state.http_client.aclose()
    await app.state.cache_client.disconnect()


app = FastAPI(
    title="Keiko Document Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(documents.router, prefix="/api")

