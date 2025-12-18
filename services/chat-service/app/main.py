"""Chat service main application module."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from openai import AsyncAzureOpenAI

from .config import settings
from .routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - startup and shutdown."""
    app.state.openai_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    yield
    await app.state.openai_client.close()


app = FastAPI(
    title="Keiko Chat Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")

