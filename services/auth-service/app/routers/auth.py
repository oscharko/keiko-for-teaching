"""Authentication endpoints with Azure AD B2C integration."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])
security = HTTPBearer()


class TokenRequest(BaseModel):
    """Token request model for Azure AD B2C."""

    code: str = Field(..., description="Authorization code from Azure AD B2C")
    redirect_uri: str = Field(..., description="Redirect URI used in authorization")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


class UserInfo(BaseModel):
    """User information model."""

    sub: str  # Subject (user ID)
    email: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None


class ValidateTokenResponse(BaseModel):
    """Token validation response."""

    valid: bool
    user_info: UserInfo | None = None
    error: str | None = None


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expiration_minutes
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/auth/token", response_model=TokenResponse)
async def exchange_token(
    token_request: TokenRequest, request: Request
) -> TokenResponse:
    """Exchange Azure AD B2C authorization code for access token.
    
    This endpoint exchanges an authorization code from Azure AD B2C for an access token.
    In a real implementation, this would call the Azure AD B2C token endpoint.
    
    Args:
        token_request: Token request with authorization code
        request: FastAPI request object
        
    Returns:
        TokenResponse: Access token and metadata
        
    Raises:
        HTTPException: If token exchange fails
    """
    # TODO: Implement actual Azure AD B2C token exchange
    # This is a placeholder implementation
    
    try:
        # In production, call Azure AD B2C token endpoint:
        # POST https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/oauth2/v2.0/token
        
        # For now, create a mock token
        user_data = {
            "sub": "mock-user-id",
            "email": "user@example.com",
            "name": "Mock User",
        }
        
        access_token = create_access_token(user_data)
        
        # Store session in cache
        cache_client = request.app.state.cache_client
        await cache_client.set(
            f"session:{user_data['sub']}",
            {"user_id": user_data["sub"], "email": user_data["email"]},
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_minutes * 60,
        )
        
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed",
        )


@router.post("/auth/validate", response_model=ValidateTokenResponse)
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> ValidateTokenResponse:
    """Validate a JWT access token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        ValidateTokenResponse: Validation result with user info
    """
    try:
        payload = decode_token(credentials.credentials)

        user_info = UserInfo(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
        )

        return ValidateTokenResponse(valid=True, user_info=user_info)

    except HTTPException as e:
        return ValidateTokenResponse(valid=False, error=e.detail)


@router.post("/auth/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, str]:
    """Logout user and invalidate session.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        dict: Logout confirmation
    """
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")

        if user_id:
            # Remove session from cache
            cache_client = request.app.state.cache_client
            await cache_client.delete(f"session:{user_id}")

        return {"status": "success", "message": "Logged out successfully"}

    except HTTPException:
        # Even if token is invalid, return success
        return {"status": "success", "message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserInfo)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInfo:
    """Get current user information from token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        UserInfo: Current user information

    Raises:
        HTTPException: If token is invalid
    """
    payload = decode_token(credentials.credentials)

    return UserInfo(
        sub=payload.get("sub", ""),
        email=payload.get("email"),
        name=payload.get("name"),
        given_name=payload.get("given_name"),
        family_name=payload.get("family_name"),
    )


