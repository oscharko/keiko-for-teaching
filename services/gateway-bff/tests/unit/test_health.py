import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

# Mock shared.cache module before importing app.main
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared"))

# Mocking
cache_mock = MagicMock()
sys.modules["cache"] = cache_mock

# Create an AsyncMock for the cache instance methods that are awaited
mock_cache_instance = MagicMock()
mock_cache_instance.connect = AsyncMock()
mock_cache_instance.disconnect = AsyncMock()
mock_cache_instance.get = AsyncMock()
mock_cache_instance.set = AsyncMock()
mock_cache_instance.delete = AsyncMock()
mock_cache_instance.get.return_value = None # Default return for get

cache_mock.get_cache_client = MagicMock(return_value=mock_cache_instance)

# Now import app
from app.main import app  # noqa: E402

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
