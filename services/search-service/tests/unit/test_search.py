"""Unit tests for search service endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.routers.search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
    _generate_cache_key,
)


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_generate_cache_key_consistent(self):
        """Test that same request generates same cache key."""
        request1 = SearchRequest(query="test query", top_k=5)
        request2 = SearchRequest(query="test query", top_k=5)

        key1 = _generate_cache_key(request1)
        key2 = _generate_cache_key(request2)

        assert key1 == key2
        assert key1.startswith("search:")

    def test_generate_cache_key_different(self):
        """Test that different requests generate different cache keys."""
        request1 = SearchRequest(query="test query", top_k=5)
        request2 = SearchRequest(query="different query", top_k=5)

        key1 = _generate_cache_key(request1)
        key2 = _generate_cache_key(request2)

        assert key1 != key2

    def test_generate_cache_key_with_vector(self):
        """Test cache key generation with query vector."""
        request = SearchRequest(
            query="test", top_k=5, query_vector=[0.1, 0.2, 0.3]
        )
        key = _generate_cache_key(request)

        assert key.startswith("search:")
        assert len(key) > 10


@pytest.mark.asyncio
class TestSearchEndpoints:
    """Test search endpoints."""

    async def test_search_documents_simple(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test simple text search."""
        # Mock cache miss
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()

        # Mock search results
        mock_result = {
            "id": "doc1",
            "content": "Test content",
            "title": "Test Document",
            "source": "test.pdf",
            "@search.score": 0.95,
        }

        async def mock_search_iter():
            yield mock_result

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 1

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = test_client.post(
            "/api/search",
            json={"query": "test query", "top_k": 5, "use_semantic_ranker": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == "doc1"
        assert data["results"][0]["content"] == "Test content"
        assert data["results"][0]["score"] == 0.95
        assert data["cached"] is False

        # Verify search was called
        mock_search_client.search.assert_called_once()

        # Verify cache was set
        mock_cache_client.set.assert_called_once()

    async def test_search_documents_cached(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test search with cached results."""
        # Mock cache hit
        cached_response = {
            "results": [
                {
                    "id": "doc1",
                    "content": "Cached content",
                    "title": "Cached Doc",
                    "source": "cache.pdf",
                    "score": 0.9,
                    "reranker_score": None,
                    "highlights": None,
                }
            ],
            "total_count": 1,
            "query": "cached query",
            "cached": False,
        }
        mock_cache_client.get = AsyncMock(return_value=cached_response)

        # Make request
        response = test_client.post(
            "/api/search", json={"query": "cached query", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["query"] == "cached query"
        assert len(data["results"]) == 1

        # Verify search was NOT called
        mock_search_client.search.assert_not_called()

    async def test_search_documents_with_semantic_ranker(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test search with semantic ranker."""
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()

        # Mock search results with reranker score
        mock_result = {
            "id": "doc1",
            "content": "Semantic content",
            "@search.score": 0.85,
            "@search.reranker_score": 3.5,
        }

        async def mock_search_iter():
            yield mock_result

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 1

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = test_client.post(
            "/api/search", json={"query": "test", "top_k": 5, "use_semantic_ranker": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["reranker_score"] == 3.5

        # Verify semantic ranker was enabled in search call
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs["query_type"] == "semantic"

    async def test_search_documents_with_vector(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test hybrid search with vector."""
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()

        mock_result = {"id": "doc1", "content": "Vector content", "@search.score": 0.92}

        async def mock_search_iter():
            yield mock_result

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 1

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request with query vector
        response = test_client.post(
            "/api/search",
            json={
                "query": "test",
                "top_k": 5,
                "query_vector": [0.1, 0.2, 0.3],
                "use_semantic_ranker": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

        # Verify vector queries were passed
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert "vector_queries" in call_kwargs
        assert len(call_kwargs["vector_queries"]) == 1

    async def test_search_documents_with_filter(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test search with filter expression."""
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()

        mock_result = {"id": "doc1", "content": "Filtered content", "@search.score": 0.88}

        async def mock_search_iter():
            yield mock_result

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 1

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request with filter
        response = test_client.post(
            "/api/search",
            json={
                "query": "test",
                "top_k": 5,
                "filter_expression": "source eq 'test.pdf'",
                "use_semantic_ranker": False,
            },
        )

        assert response.status_code == 200

        # Verify filter was passed
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs["filter"] == "source eq 'test.pdf'"

    async def test_search_documents_empty_results(
        self, test_client, mock_search_client, mock_cache_client
    ):
        """Test search with no results."""
        mock_cache_client.get = AsyncMock(return_value=None)
        mock_cache_client.set = AsyncMock()

        async def mock_search_iter():
            return
            yield  # Make it a generator

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 0

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        response = test_client.post(
            "/api/search", json={"query": "nonexistent", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0
        assert data["total_count"] == 0

