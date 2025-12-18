"""Integration tests for search service API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestSearchEndpoints:
    """Integration tests for search endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_readiness_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_search_endpoint_validation(self, client):
        """Test search endpoint request validation."""
        # Missing required 'query' field
        response = client.post("/api/search", json={"top_k": 5})

        assert response.status_code == 422  # Validation error

    def test_search_endpoint_with_defaults(self, client, mock_search_client):
        """Test search endpoint with default parameters."""
        # Mock search results
        mock_result = {
            "id": "doc1",
            "content": "Test content",
            "title": "Test",
            "@search.score": 0.9,
        }

        async def mock_search_iter():
            yield mock_result

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 1

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = client.post("/api/search", json={"query": "test query"})

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_count" in data
        assert "query" in data
        assert data["query"] == "test query"

    def test_search_endpoint_with_top_k(self, client, mock_search_client):
        """Test search endpoint with custom top_k."""
        async def mock_search_iter():
            return
            yield

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 0

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = client.post(
            "/api/search", json={"query": "test", "top_k": 10}
        )

        assert response.status_code == 200

        # Verify top_k was passed to search
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs["top"] == 10

    def test_search_endpoint_with_semantic_ranker(
        self, client, mock_search_client
    ):
        """Test search endpoint with semantic ranker enabled."""
        async def mock_search_iter():
            return
            yield

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 0

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = client.post(
            "/api/search",
            json={"query": "test", "use_semantic_ranker": True},
        )

        assert response.status_code == 200

        # Verify semantic ranker was enabled
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs["query_type"] == "semantic"

    def test_search_endpoint_with_filter(self, client, mock_search_client):
        """Test search endpoint with filter expression."""
        async def mock_search_iter():
            return
            yield

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 0

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = client.post(
            "/api/search",
            json={
                "query": "test",
                "filter_expression": "category eq 'documentation'",
            },
        )

        assert response.status_code == 200

        # Verify filter was passed
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs["filter"] == "category eq 'documentation'"

    def test_search_endpoint_with_vector(self, client, mock_search_client):
        """Test search endpoint with query vector."""
        async def mock_search_iter():
            return
            yield

        mock_search_results = MagicMock()
        mock_search_results.__aiter__ = lambda self: mock_search_iter()
        mock_search_results.get_count = lambda: 0

        mock_search_client.search = AsyncMock(return_value=mock_search_results)

        # Make request
        response = client.post(
            "/api/search",
            json={"query": "test", "query_vector": [0.1, 0.2, 0.3]},
        )

        assert response.status_code == 200

        # Verify vector queries were passed
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert "vector_queries" in call_kwargs

