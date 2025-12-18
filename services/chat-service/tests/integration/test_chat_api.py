"""Integration tests for chat service API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for integration tests."""
    with patch("app.main.AsyncAzureOpenAI") as mock_class:
        client = MagicMock()
        client.chat.completions.create = AsyncMock()
        # Ensure the instantiated client returns our mock
        mock_class.return_value = client
        
        # Also mock the context manager if used
        # But lifespan calls AsyncAzureOpenAI(...) -> client
        yield client


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for integration tests."""
    with patch("httpx.AsyncClient") as mock:
        client = MagicMock()
        client.post = AsyncMock()
        mock.return_value = client
        yield client


class TestChatEndpoints:
    """Integration tests for chat endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_readiness_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_chat_endpoint_simple(self, client, mock_openai_client):
        """Test simple chat endpoint."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Hello! How can I help you?"))
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Make request
        response = client.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "context": {
                    "overrides": {
                        "use_rag": False
                    }
                },
                "session_state": {"conversation_id": "test-conv"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        data = response.json()
        assert "message" in data
        assert data["message"]["content"] == "Hello! How can I help you?"
        assert "context" in data
        assert "thoughts" in data["context"]
        assert "citations" in data["context"]["data_points"]

    def test_chat_endpoint_with_rag(
        self, client, mock_openai_client, mock_http_client
    ):
        """Test chat endpoint with RAG enabled."""
        # Mock search service response
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "results": [
                {
                    "id": "doc1",
                    "content": "Keiko is a helpful AI assistant.",
                    "title": "About Keiko",
                    "score": 0.95,
                }
            ],
            "total_count": 1,
        }
        mock_http_client.post.return_value = mock_search_response

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="Based on the context, Keiko is an AI assistant."
                )
            )
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Make request
        response = client.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "What is Keiko?"}],
                "context": {
                    "overrides": {
                        "use_rag": True
                    }
                },
                "session_state": {"conversation_id": "test-conv"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "citations" in data["context"]["data_points"]
        assert len(data["context"]["data_points"]["citations"]) > 0

    def test_chat_endpoint_validation_error(self, client):
        """Test chat endpoint with invalid request."""
        response = client.post(
            "/api/chat",
            json={
                # Missing required 'messages' field
                "session_state": {"conversation_id": "test-conv"},
            },
        )

        assert response.status_code == 422  # Validation error

    def test_chat_endpoint_with_history(self, client, mock_openai_client):
        """Test chat endpoint with conversation history."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="I remember our conversation."))
        ]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Make request with history
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "Do you remember what we talked about?"}
                ],
                "context": {
                    "overrides": {
                        "use_rag": False
                    }
                },
                "session_state": {"conversation_id": "test-conv"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify history was passed to OpenAI
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) >= 3  # System + history + current message

