"""Search proxy router - forwards requests to search service."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    use_semantic_ranker: bool = Field(default=True, description="Use semantic ranker")
    query_vector: list[float] | None = Field(
        default=None, description="Query embedding"
    )
    filter_expression: str | None = Field(default=None, description="OData filter")


@router.post("/search")
async def search_documents(
    search_request: SearchRequest, request: Request
) -> dict[str, Any]:
    """Proxy search request to search service.

    Args:
        search_request: Search parameters
        request: FastAPI request object

    Returns:
        dict: Search results from search service

    Raises:
        HTTPException: If search service request fails
    """
    http_client: httpx.AsyncClient = request.app.state.http_client

    try:
        response = await http_client.post(
            f"{settings.search_service_url}/api/search",
            json=search_request.model_dump(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Search service error: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Search service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Search service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Search service unavailable"
        ) from e

