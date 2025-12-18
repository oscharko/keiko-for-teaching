"""Request logging middleware."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses."""

    def __init__(
        self,
        app,
        excluded_paths: list[str] | None = None,
    ):
        """Initialize request logging middleware.
        
        Args:
            app: FastAPI application
            excluded_paths: List of paths to exclude from logging
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/ready"]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Get user info if available
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub", "anonymous")

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_ip} (user: {user_id})"
        )

        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s "
                f"client={client_ip} user={user_id}"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request.headers.get(
                "X-Request-ID", "unknown"
            )
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.3f}s "
                f"client={client_ip} user={user_id}"
            )
            raise

