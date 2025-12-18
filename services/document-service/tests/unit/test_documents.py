"""Unit tests for document service endpoints."""

import pytest
import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile

from app.routers.documents import (
    DocumentMetadata,
    DocumentListResponse,
    UploadResponse,
    _validate_file,
)


class TestFileValidation:
    """Test file validation."""

    def test_validate_file_allowed_extension(self):
        """Test validation with allowed file extension."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"

        # Should not raise exception
        _validate_file(mock_file)

    def test_validate_file_disallowed_extension(self):
        """Test validation with disallowed file extension."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.exe"

        with pytest.raises(HTTPException) as exc_info:
            _validate_file(mock_file)

        assert exc_info.value.status_code == 400
        assert "File type not allowed" in exc_info.value.detail

    def test_validate_file_no_extension(self):
        """Test validation with file without extension."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "testfile"

        # Should raise exception for unknown extension
        with pytest.raises(HTTPException):
            _validate_file(mock_file)


@pytest.mark.asyncio
class TestDocumentEndpoints:
    """Test document endpoints."""

    async def test_upload_document_success(
        self, test_client, mock_blob_service_client, mock_cache_client
    ):
        """Test successful document upload."""
        # Mock blob client
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://storage.blob.core.windows.net/container/doc/test.pdf"

        mock_container_client.create_container = AsyncMock()
        mock_container_client.get_blob_client = MagicMock(return_value=mock_blob_client)

        mock_blob_service_client.get_container_client = MagicMock(
            return_value=mock_container_client
        )

        # Mock cache
        mock_cache_client.set = AsyncMock()

        # Create test file
        file_content = b"Test PDF content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

        # Make request
        response = test_client.post("/api/documents/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.pdf"
        assert data["size"] == len(file_content)
        assert data["status"] == "uploaded"

        # Verify blob upload was called
        mock_blob_client.upload_blob.assert_called_once()

        # Verify cache was set
        mock_cache_client.set.assert_called_once()

    async def test_upload_document_invalid_type(self, test_client):
        """Test upload with invalid file type."""
        file_content = b"Executable content"
        files = {"file": ("malware.exe", io.BytesIO(file_content), "application/x-msdownload")}

        response = test_client.post("/api/documents/upload", files=files)

        assert response.status_code == 400
        assert "File type not allowed" in response.json()["detail"]

    async def test_upload_document_too_large(
        self, test_client, mock_blob_service_client, mock_cache_client
    ):
        """Test upload with file too large."""
        # Mock blob client
        mock_container_client = MagicMock()
        mock_container_client.create_container = AsyncMock()

        mock_blob_service_client.get_container_client = MagicMock(
            return_value=mock_container_client
        )

        # Create large file (> max_file_size)
        # Assuming max_file_size is 10MB in settings
        file_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        files = {"file": ("large.pdf", io.BytesIO(file_content), "application/pdf")}

        response = test_client.post("/api/documents/upload", files=files)

        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    async def test_get_document_metadata_success(self, test_client, mock_cache_client):
        """Test getting document metadata."""
        # Mock cache response
        mock_metadata = {
            "id": "doc123",
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "status": "uploaded",
            "blob_url": "https://storage.blob.core.windows.net/container/doc/test.pdf",
        }
        mock_cache_client.get = AsyncMock(return_value=mock_metadata)

        response = test_client.get("/api/documents/doc123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "doc123"
        assert data["filename"] == "test.pdf"

    async def test_get_document_metadata_not_found(self, test_client, mock_cache_client):
        """Test getting metadata for non-existent document."""
        mock_cache_client.get = AsyncMock(return_value=None)

        response = test_client.get("/api/documents/nonexistent")

        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    async def test_download_document_success(
        self, test_client, mock_blob_service_client, mock_cache_client
    ):
        """Test successful document download."""
        # Mock cache response
        mock_metadata = {
            "id": "doc123",
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024,
        }
        mock_cache_client.get = AsyncMock(return_value=mock_metadata)

        # Mock blob download
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()

        async def mock_chunks():
            yield b"chunk1"
            yield b"chunk2"

        mock_stream = MagicMock()
        mock_stream.chunks = mock_chunks

        mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)
        mock_container_client.get_blob_client = MagicMock(return_value=mock_blob_client)

        mock_blob_service_client.get_container_client = MagicMock(
            return_value=mock_container_client
        )

        response = test_client.get("/api/documents/doc123/download")

        assert response.status_code == 200
        assert response.headers["content-disposition"] == "attachment; filename=test.pdf"

    async def test_download_document_not_found(self, test_client, mock_cache_client):
        """Test downloading non-existent document."""
        mock_cache_client.get = AsyncMock(return_value=None)

        response = test_client.get("/api/documents/nonexistent/download")

        assert response.status_code == 404

    async def test_delete_document_success(
        self, test_client, mock_blob_service_client, mock_cache_client
    ):
        """Test successful document deletion."""
        # Mock cache response
        mock_metadata = {
            "id": "doc123",
            "filename": "test.pdf",
        }
        mock_cache_client.get = AsyncMock(return_value=mock_metadata)
        mock_cache_client.delete = AsyncMock()

        # Mock blob deletion
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_client.delete_blob = AsyncMock()

        mock_container_client.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service_client.get_container_client = MagicMock(
            return_value=mock_container_client
        )

        response = test_client.delete("/api/documents/doc123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify blob delete was called
        mock_blob_client.delete_blob.assert_called_once()

        # Verify cache delete was called
        mock_cache_client.delete.assert_called_once_with("document:doc123")

    async def test_delete_document_not_found(self, test_client, mock_cache_client):
        """Test deleting non-existent document."""
        mock_cache_client.get = AsyncMock(return_value=None)

        response = test_client.delete("/api/documents/nonexistent")

        assert response.status_code == 404

    async def test_list_documents(self, test_client):
        """Test listing documents."""
        response = test_client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_count" in data
        assert isinstance(data["documents"], list)

