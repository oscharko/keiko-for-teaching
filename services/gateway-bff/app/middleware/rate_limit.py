"""Rate limiting middleware using Redis."""

import logging
import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to implement rate limiting using Redis."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        excluded_paths: list[str] | None = None,
    ):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per client
            excluded_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.excluded_paths = excluded_paths or ["/health", "/ready"]

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting.
        
        Uses user ID if authenticated, otherwise IP address.
        
        Args:
            request: Incoming request
            
        Returns:
            str: Client identifier
        """
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub")
            if user_id:
                return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and check rate limits.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        cache_client = request.app.state.cache_client

        # Get current minute timestamp
        current_minute = int(time.time() / 60)
        rate_limit_key = f"rate_limit:{client_id}:{current_minute}"

        try:
            # Get current request count
            current_count = await cache_client.get(rate_limit_key)
            
            if current_count is None:
                current_count = 0
            
            # Check if rate limit exceeded
            if current_count >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for {client_id}: {current_count} requests"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": 60,
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            # Increment request count
            new_count = current_count + 1
            await cache_client.set(rate_limit_key, new_count, ttl=60)

            # Continue to next middleware/handler
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.requests_per_minute - new_count)
            )

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request to proceed
            return await call_next(request)

