"""Search endpoints with hybrid search support."""

import hashlib
import json
import logging
from typing import Any

from azure.core.exceptions import AzureError
from azure.search.documents.models import VectorizedQuery
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(
        default=settings.default_top_k,
        ge=1,
        le=50,
        description="Number of results to return",
    )
    use_semantic_ranker: bool = Field(
        default=True, description="Use semantic ranker for better relevance"
    )
    query_vector: list[float] | None = Field(
        default=None, description="Optional query embedding for vector search"
    )
    filter_expression: str | None = Field(
        default=None, description="Optional OData filter expression"
    )


class SearchResult(BaseModel):
    """Individual search result."""

    id: str
    content: str
    title: str | None = None
    source: str | None = None
    score: float
    reranker_score: float | None = None
    highlights: dict[str, list[str]] | None = None


class SearchResponse(BaseModel):
    """Search response model."""

    results: list[SearchResult]
    total_count: int
    query: str
    cached: bool = False


def _generate_cache_key(request: SearchRequest) -> str:
    """Generate a cache key for the search request.
    
    Args:
        request: Search request
        
    Returns:
        str: Cache key
    """
    # Create a deterministic hash of the request
    request_dict = request.model_dump()
    request_json = json.dumps(request_dict, sort_keys=True)
    hash_digest = hashlib.sha256(request_json.encode()).hexdigest()
    return f"search:{hash_digest}"


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request_body: SearchRequest, request: Request
) -> SearchResponse:
    """Search documents using hybrid search (text + vector).
    
    This endpoint performs hybrid search combining:
    - Full-text search with BM25 ranking
    - Vector similarity search (if query_vector provided)
    - Semantic ranking (if enabled)
    
    Args:
        request_body: Search request parameters
        request: FastAPI request object
        
    Returns:
        SearchResponse: Search results with relevance scores
        
    Raises:
        HTTPException: If search fails
    """
    cache_client = request.app.state.cache_client
    search_client = request.app.state.search_client
    
    # Try to get from cache
    cache_key = _generate_cache_key(request_body)
    cached_result = await cache_client.get(cache_key)
    
    if cached_result:
        logger.info(f"Cache hit for query: {request_body.query}")
        return SearchResponse(**cached_result, cached=True)
    
    try:
        # Prepare search parameters
        search_params: dict[str, Any] = {
            "search_text": request_body.query,
            "top": request_body.top_k,
            "include_total_count": True,
        }
        
        # Add filter if provided
        if request_body.filter_expression:
            search_params["filter"] = request_body.filter_expression
        
        # Add vector search if query vector is provided
        vector_queries = []
        if request_body.query_vector:
            vector_queries.append(
                VectorizedQuery(
                    vector=request_body.query_vector,
                    k_nearest_neighbors=request_body.top_k,
                    fields="content_vector",
                )
            )
            search_params["vector_queries"] = vector_queries
        
        # Add semantic ranker if enabled
        if request_body.use_semantic_ranker:
            search_params["query_type"] = "semantic"
            search_params["semantic_configuration_name"] = (
                settings.default_semantic_configuration
            )
        
        # Perform search
        logger.info(f"Searching for: {request_body.query}")
        search_results = await search_client.search(**search_params)
        
        # Process results
        results = []
        async for result in search_results:
            search_result = SearchResult(
                id=result.get("id", ""),
                content=result.get("content", ""),
                title=result.get("title"),
                source=result.get("source"),
                score=result.get("@search.score", 0.0),
                reranker_score=result.get("@search.reranker_score"),
                highlights=result.get("@search.highlights"),
            )
            results.append(search_result)
        
        # Get total count
        total_count = getattr(search_results, "get_count", lambda: len(results))()
        
        response = SearchResponse(
            results=results,
            total_count=total_count or len(results),
            query=request_body.query,
            cached=False,
        )
        
        # Cache the result
        await cache_client.set(cache_key, response.model_dump())
        
        logger.info(f"Found {len(results)} results for query: {request_body.query}")
        return response
        
    except AzureError as e:
        logger.error(f"Azure Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

