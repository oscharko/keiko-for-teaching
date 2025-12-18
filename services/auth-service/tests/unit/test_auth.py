"""Unit tests for auth service authentication endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from jose import jwt

from app.routers.auth import (
    create_access_token,
    decode_token,
    TokenRequest,
    TokenResponse,
    UserInfo,
    ValidateTokenResponse,
)
from app.config import settings


class TestTokenFunctions:
    """Test token creation and validation functions."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    def test_decode_token_invalid(self):
        """Test decoding an invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_token_expired(self):
        """Test decoding an expired token."""
        # Create token that expired 1 hour ago
        data = {"sub": "user123"}
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        to_encode.update({"exp": expire})

        expired_token = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_exchange_token_success(self, test_client, mock_cache_client):
        """Test successful token exchange."""
        # Mock cache client
        mock_cache_client.set = AsyncMock()

        # Make request
        response = test_client.post(
            "/api/auth/token",
            json={"code": "auth_code_123", "redirect_uri": "http://localhost:3000"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.jwt_expiration_minutes * 60

        # Verify cache was called
        mock_cache_client.set.assert_called_once()

    async def test_validate_token_valid(self, test_client):
        """Test validating a valid token."""
        # Create a valid token
        token = create_access_token(
            {"sub": "user123", "email": "test@example.com", "name": "Test User"}
        )

        response = test_client.post(
            "/api/auth/validate", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_info"]["sub"] == "user123"
        assert data["user_info"]["email"] == "test@example.com"
        assert data["user_info"]["name"] == "Test User"

    async def test_validate_token_invalid(self, test_client):
        """Test validating an invalid token."""
        response = test_client.post(
            "/api/auth/validate", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data

    async def test_get_current_user(self, test_client):
        """Test getting current user info."""
        token = create_access_token(
            {
                "sub": "user123",
                "email": "test@example.com",
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
            }
        )

        response = test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == "user123"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["given_name"] == "Test"
        assert data["family_name"] == "User"

    async def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token."""
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_logout_success(self, test_client, mock_cache_client):
        """Test successful logout."""
        token = create_access_token({"sub": "user123"})
        mock_cache_client.delete = AsyncMock()

        response = test_client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Logged out successfully" in data["message"]

        # Verify cache delete was called
        mock_cache_client.delete.assert_called_once_with("session:user123")

    async def test_logout_invalid_token(self, test_client):
        """Test logout with invalid token still succeeds."""
        response = test_client.post(
            "/api/auth/logout", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

