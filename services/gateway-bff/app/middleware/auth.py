"""Authentication middleware for validating JWT tokens."""

import logging
from typing import Callable

import httpx
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens via auth service."""

    def __init__(
        self,
        app,
        auth_service_url: str,
        excluded_paths: list[str] | None = None,
    ):
        """Initialize authentication middleware.
        
        Args:
            app: FastAPI application
            auth_service_url: URL of the auth service
            excluded_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.auth_service_url = auth_service_url
        self.excluded_paths = excluded_paths or [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/api/auth/token",
        ]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and validate authentication.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response
        """
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]

        # Validate token with auth service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/auth/validate",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                if response.status_code != 200:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid or expired token"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # Add user info to request state
                validation_result = response.json()
                if validation_result.get("valid"):
                    request.state.user = validation_result.get("user_info")
                else:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid token"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        except httpx.RequestError as e:
            logger.error(f"Auth service connection error: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Authentication service unavailable"},
            )

        # Continue to next middleware/handler
        response = await call_next(request)
        return response

