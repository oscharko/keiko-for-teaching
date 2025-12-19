from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import Settings
from app.services.chat_service import ChatService


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.azure_openai_deployment = "gpt-model"
    settings.default_temperature = 0.7
    settings.default_max_tokens = 500
    settings.search_service_url = "http://search-service"
    settings.use_legacy_openai = True  # Force legacy mode for tests
    return settings

@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client

@pytest.fixture
def mock_http_client():
    client = MagicMock()
    client.post = AsyncMock()
    return client

@pytest.fixture
def chat_service(mock_openai_client, mock_settings, mock_http_client):
    return ChatService(
        settings=mock_settings,
        http_client=mock_http_client,
        legacy_client=mock_openai_client
    )

@pytest.mark.asyncio
async def test_chat_simple(chat_service, mock_openai_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Hello there!"))
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Call chat
    messages = [{"role": "user", "content": "Hello"}]
    result = await chat_service.chat(messages, suggest_followup=False)

    # Check assertions
    assert result["content"] == "Hello there!"
    mock_openai_client.chat.completions.create.assert_called_once()
    assert result["thoughts"] == []
    assert result["citations"] == []

@pytest.mark.asyncio
async def test_chat_with_rag(chat_service, mock_openai_client, mock_http_client):
    # Setup Search Mock
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "results": [
            {"id": "doc1", "content": "Keiko is a dog."},
            {"id": "doc2", "content": "Keiko likes treats."}
        ]
    }
    mock_http_client.post.return_value = mock_search_response

    # Setup OpenAI Mock
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Based on the context..."))
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Call chat
    messages = [{"role": "user", "content": "Who is Keiko?"}]
    result = await chat_service.chat(messages, use_rag=True, suggest_followup=False)

    # Check assertions
    assert result["content"] == "Based on the context..."
    assert len(result["citations"]) == 2
    assert "doc1" in result["citations"]
    mock_http_client.post.assert_called_once()
    mock_openai_client.chat.completions.create.assert_called_once()

    # Check if system prompt contained context (roughly)
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    sent_messages = call_kwargs["messages"]
    system_prompts = [m["content"] for m in sent_messages if m["role"] == "system"]
    assert any("Keiko is a dog" in msg for msg in system_prompts)
