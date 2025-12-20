"""Integration tests for Chat API endpoints."""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.routers.chat import ChatRequest, ChatOverrides, ChatContext, Message


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_chat_service():
    """Mock chat service."""
    with patch('app.routers.chat.ChatService') as mock:
        yield mock


class TestChatEndpoint:
    """Test chat endpoint."""

    def test_non_streaming_chat(self, client, mock_chat_service):
        """Test non-streaming chat request."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.chat = AsyncMock(return_value={
            'content': 'Hello! How can I help?',
            'thoughts': [],
            'citations': [],
        })
        mock_chat_service.return_value = mock_instance

        # Create request
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
            ],
            'context': {
                'overrides': {
                    'use_rag': False,
                    'stream': False,
                }
            }
        }

        # Send request
        response = client.post('/api/chat', json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['message']['role'] == 'assistant'
        assert 'Hello' in data['message']['content']

    def test_streaming_chat(self, client, mock_chat_service):
        """Test streaming chat request."""
        # Setup mock
        async def mock_stream(*args, **kwargs):
            yield 'Hello'
            yield ' world'

        mock_instance = MagicMock()
        mock_instance.chat_stream = mock_stream
        mock_chat_service.return_value = mock_instance

        # Create request
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
            ],
            'context': {
                'overrides': {
                    'use_rag': False,
                    'stream': True,
                }
            }
        }

        # Send request
        response = client.post('/api/chat', json=request_data)

        # Verify response is streaming
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/event-stream'

    def test_rag_enabled(self, client, mock_chat_service):
        """Test chat with RAG enabled."""
        mock_instance = MagicMock()
        mock_instance.chat = AsyncMock(return_value={
            'content': 'Based on the documents...',
            'thoughts': [{'title': 'Search', 'description': 'Found 3 docs'}],
            'citations': ['doc1', 'doc2'],
        })
        mock_chat_service.return_value = mock_instance

        request_data = {
            'messages': [
                {'role': 'user', 'content': 'What is RAG?'},
            ],
            'context': {
                'overrides': {
                    'use_rag': True,
                    'stream': False,
                }
            }
        }

        response = client.post('/api/chat', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data['context']['data_points']['citations']) > 0

    def test_error_handling(self, client, mock_chat_service):
        """Test error handling."""
        mock_instance = MagicMock()
        mock_instance.chat = AsyncMock(side_effect=Exception('Service error'))
        mock_chat_service.return_value = mock_instance

        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
            ]
        }

        response = client.post('/api/chat', json=request_data)

        assert response.status_code >= 400

