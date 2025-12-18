"""Session management middleware using Redis cache."""

import sys
import uuid
from pathlib import Path
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from cache import get_cache_client


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for managing user sessions with Redis cache."""

    def __init__(self, app, redis_url: str, session_ttl: int = 3600):
        """Initialize session middleware.

        Args:
            app: FastAPI application
            redis_url: Redis connection URL
            session_ttl: Session TTL in seconds (default: 1 hour)
        """
        super().__init__(app)
        self.cache_client = get_cache_client(
            redis_url=redis_url,
            default_ttl=session_ttl,
            key_prefix="keiko:session",
        )
        self.session_ttl = session_ttl

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and manage session.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Get or create session ID
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            is_new_session = True
        else:
            is_new_session = False

        # Attach session ID to request state
        request.state.session_id = session_id

        # Get session data from cache
        session_data = await self.cache_client.get(f"data:{session_id}")
        request.state.session = session_data or {}

        # Process request
        response = await call_next(request)

        # Save session data if modified
        if hasattr(request.state, "session_modified") and request.state.session_modified:
            await self.cache_client.set(
                f"data:{session_id}",
                request.state.session,
                ttl=self.session_ttl,
            )

        # Set session cookie for new sessions
        if is_new_session:
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=self.session_ttl,
            )

        return response


async def get_session(request: Request) -> dict:
    """Get session data from request.

    Args:
        request: FastAPI request

    Returns:
        dict: Session data
    """
    return getattr(request.state, "session", {})


async def set_session(request: Request, key: str, value: any) -> None:
    """Set a value in the session.

    Args:
        request: FastAPI request
        key: Session key
        value: Value to store
    """
    if not hasattr(request.state, "session"):
        request.state.session = {}
    
    request.state.session[key] = value
    request.state.session_modified = True


async def clear_session(request: Request) -> None:
    """Clear all session data.

    Args:
        request: FastAPI request
    """
    request.state.session = {}
    request.state.session_modified = True

