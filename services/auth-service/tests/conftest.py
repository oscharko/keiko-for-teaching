"""Pytest configuration and fixtures for auth service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def mock_cache_client():
    """Mock cache client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def test_client(mock_cache_client):
    """Create test client with mocked dependencies."""
    # Override app state with mocks
    app.state.cache_client = mock_cache_client

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_settings():
    """Mock settings."""
    return settings

