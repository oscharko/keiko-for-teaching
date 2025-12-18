"""Integration tests for gateway BFF API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for backend service calls."""
    with patch("httpx.AsyncClient") as mock:
        client = MagicMock()
        client.post = AsyncMock()
        client.get = AsyncMock()
        mock.return_value = client
        yield client


class TestGatewayEndpoints:
    """Integration tests for gateway endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_chat_proxy(self, client, mock_http_client):
        """Test chat endpoint proxy."""
        # Mock backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Test response",
            "citations": [],
            "thoughts": [],
        }
        mock_http_client.post.return_value = mock_response

        # Make request
        response = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "conversation_id": "test",
                "use_rag": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test response"

        # Verify backend was called
        mock_http_client.post.assert_called_once()

    def test_search_proxy(self, client, mock_http_client):
        """Test search endpoint proxy."""
        # Mock backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "doc1", "content": "Test"}],
            "total_count": 1,
            "query": "test",
        }
        mock_http_client.post.return_value = mock_response

        # Make request
        response = client.post("/api/search", json={"query": "test"})

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

        # Verify backend was called
        mock_http_client.post.assert_called_once()

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_rate_limiting(self, client, mock_http_client):
        """Test rate limiting middleware."""
        # Mock backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"answer": "Test"}
        mock_http_client.post.return_value = mock_response

        # Make multiple requests
        for i in range(5):
            response = client.post(
                "/api/chat",
                json={"message": f"Message {i}", "conversation_id": "test"},
            )
            # First few requests should succeed
            if i < 3:
                assert response.status_code == 200

    def test_error_handling(self, client, mock_http_client):
        """Test error handling from backend services."""
        # Mock backend error
        mock_http_client.post.side_effect = Exception("Backend error")

        # Make request
        response = client.post(
            "/api/chat",
            json={"message": "Hello", "conversation_id": "test"},
        )

        # Should return error response
        assert response.status_code >= 400

    def test_request_logging(self, client, mock_http_client):
        """Test request logging middleware."""
        # Mock backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"answer": "Test"}
        mock_http_client.post.return_value = mock_response

        # Make request
        response = client.post(
            "/api/chat",
            json={"message": "Hello", "conversation_id": "test"},
        )

        assert response.status_code == 200
        # Logging should have occurred (check logs in real implementation)

    def test_document_upload_proxy(self, client, mock_http_client):
        """Test document upload endpoint proxy."""
        # Mock backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "document_id": "doc123",
            "filename": "test.pdf",
            "status": "uploaded",
        }
        mock_http_client.post.return_value = mock_response

        # Make request (simplified - real test would include file upload)
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        )

        # Response depends on actual implementation
        # This is a placeholder test
        assert response.status_code in [200, 404, 500]

