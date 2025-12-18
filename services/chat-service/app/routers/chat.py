"""Chat API endpoints."""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..config import settings
from ..services.chat_service import ChatService
from ..utils.cache_utils import cache_response, get_cached_response

router = APIRouter(tags=["Chat"])


class Message(BaseModel):
    """Chat message model."""

    role: str
    content: str


class ChatOverrides(BaseModel):
    """Chat configuration overrides."""

    retrieval_mode: str | None = None
    semantic_ranker: bool | None = None
    semantic_captions: bool | None = None
    top: int | None = None
    temperature: float | None = None
    suggest_followup_questions: bool | None = None


class ChatContext(BaseModel):
    """Chat request context."""

    overrides: ChatOverrides | None = None


class ChatRequest(BaseModel):
    """Chat request model."""

    messages: list[Message]
    context: ChatContext | None = None
    session_state: Any | None = None


class DataPoints(BaseModel):
    """Data points from search results."""

    text: list[str] = []
    images: list[str] = []
    citations: list[str] = []


class ResponseContext(BaseModel):
    """Response context with data points."""

    data_points: DataPoints = DataPoints()
    thoughts: list[dict[str, str]] = []
    followup_questions: list[str] = []


class ChatResponse(BaseModel):
    """Chat response model."""

    message: Message
    context: ResponseContext
    session_state: Any | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """Process chat request and return AI response."""
    openai_client = request.app.state.openai_client
    cache_client = request.app.state.cache_client
    chat_service = ChatService(openai_client, settings)

    overrides = chat_request.context.overrides if chat_request.context else None
    messages = [{"role": m.role, "content": m.content} for m in chat_request.messages]
    temperature = overrides.temperature if overrides else None
    suggest_followup = overrides.suggest_followup_questions if overrides else True

    # Try to get cached response
    cached = await get_cached_response(
        cache_client,
        messages,
        temperature=temperature,
        suggest_followup=suggest_followup,
    )

    if cached:
        # Return cached response
        response = cached
    else:
        # Generate new response
        response = await chat_service.chat(
            messages=messages,
            temperature=temperature,
            suggest_followup=suggest_followup,
        )

        # Cache the response (1 hour TTL)
        await cache_response(
            cache_client,
            messages,
            response,
            ttl=3600,
            temperature=temperature,
            suggest_followup=suggest_followup,
        )

    return ChatResponse(
        message=Message(role="assistant", content=response["content"]),
        context=ResponseContext(
            data_points=DataPoints(),
            thoughts=response.get("thoughts", []),
            followup_questions=response.get("followup_questions", []),
        ),
    )

