
import base64
import logging
import os
from typing import Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class BetaAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTP Basic Auth based on a Beta Users file.
    """
    def __init__(
        self, 
        app: ASGIApp, 
        auth_file_path: str = "beta_auth_users.txt",
        white_list_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.users: Dict[str, str] = self._load_users(auth_file_path)
        self.white_list_paths = white_list_paths or ["/health", "/docs", "/openapi.json", "/favicon.ico"]

    def _load_users(self, file_path: str) -> Dict[str, str]:
        """Loads users from the beta_auth_users.txt file."""
        users = {}
        # Try finding file in root of workspace if not found relative
        possible_paths = [
            file_path, 
            os.path.join(os.getcwd(), file_path),
            os.path.join(os.path.dirname(__file__), "../../../..", file_path) # Up from services/gateway-bff/app/middleware
        ]
        
        target_path = None
        for path in possible_paths:
            if os.path.exists(path):
                target_path = path
                break
        
        if not target_path:
            logger.warning(f"Beta Auth file not found at {file_path}. Auth will fail for all.")
            return {}

        try:
            with open(target_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("BETA_AUTH_USERS"):
                        continue
                    
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 2:
                            username = parts[0].strip()
                            password = parts[1].strip()
                            users[username] = password
            logger.info(f"Loaded {len(users)} users for Beta Auth.")
        except Exception as e:
            logger.error(f"Failed to load Beta Auth users: {e}")
            
        return users

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check whitelist
        for path in self.white_list_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Check OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return self._request_auth()

        try:
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception:
            return self._request_auth()

        if username in self.users and self.users[username] == password:
            # Populate user state for downstream consumers
            request.state.user = {"id": username, "username": username, "oid": username}
            return await call_next(request)

        return self._request_auth()

    def _request_auth(self) -> Response:
        return JSONResponse(
            status_code=401,
            content={"detail": "Beta Authentication Required"},
            headers={"WWW-Authenticate": "Basic"},
        )
