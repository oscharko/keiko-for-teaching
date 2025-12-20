"""Chat API endpoints - proxies requests to chat service."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)
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


@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest) -> Any:
    """Forward chat request to chat service.

    Supports both standard and streaming responses based on the request context.
    If stream=True in overrides, returns Server-Sent Events stream.
    Otherwise, returns a standard JSON response.
    """
    http_client = request.app.state.http_client

    # Check if streaming is requested
    is_streaming = (
        chat_request.context
        and chat_request.context.overrides
        and chat_request.context.overrides.stream
    )

    try:
        response = await http_client.post(
            f"{settings.chat_service_url}/api/chat",
            json=chat_request.model_dump(exclude_none=True),
        )
        response.raise_for_status()

        # If streaming, return the response as-is (it's already a stream)
        if is_streaming:
            return StreamingResponse(
                response.aiter_bytes(),
                media_type="text/event-stream",
            )

        # Otherwise, return standard JSON response
        return ChatResponse(**response.json())

    except Exception as e:
        logger.error(f"Chat service error: {e}")
        raise HTTPException(status_code=502, detail=f"Chat service error: {e}") from e

