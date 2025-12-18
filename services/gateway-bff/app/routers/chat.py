"""Chat API endpoints - proxies requests to chat service."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..config import settings

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


class ChatResponse(BaseModel):
    """Chat response model."""

    message: Message
    context: dict[str, Any]
    session_state: Any | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """Forward chat request to chat service."""
    http_client = request.app.state.http_client

    try:
        response = await http_client.post(
            f"{settings.chat_service_url}/api/chat",
            json=chat_request.model_dump(exclude_none=True),
        )
        response.raise_for_status()
        return ChatResponse(**response.json())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Chat service error: {e}") from e

