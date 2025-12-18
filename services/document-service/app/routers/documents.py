"""Document management endpoints."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from azure.core.exceptions import AzureError, ResourceNotFoundError
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    id: str
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    uploaded_by: str | None = None
    status: str = "uploaded"  # uploaded, processing, indexed, failed
    blob_url: str | None = None


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: list[DocumentMetadata]
    total_count: int


class UploadResponse(BaseModel):
    """Upload response model."""

    document_id: str
    filename: str
    size: int
    status: str
    message: str


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    if file.filename:
        extension = file.filename.split(".")[-1].lower()
        if extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}",
            )


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    request: Request = None,
) -> UploadResponse:
    """Upload a document to blob storage.
    
    Args:
        file: File to upload
        request: FastAPI request object
        
    Returns:
        UploadResponse: Upload result with document ID
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate file
    _validate_file(file)
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    blob_name = f"{document_id}/{file.filename}"
    
    try:
        # Get blob client
        blob_service_client = request.app.state.blob_service_client
        container_client = blob_service_client.get_container_client(
            settings.azure_storage_container_name
        )
        
        # Create container if it doesn't exist
        try:
            await container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        # Upload file
        blob_client = container_client.get_blob_client(blob_name)
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes",
            )
        
        await blob_client.upload_blob(
            file_content,
            overwrite=True,
            metadata={
                "document_id": document_id,
                "filename": file.filename or "unknown",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        
        # Store metadata in cache
        metadata = DocumentMetadata(
            id=document_id,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            size=len(file_content),
            uploaded_at=datetime.now(timezone.utc),
            status="uploaded",
            blob_url=blob_client.url,
        )
        
        cache_client = request.app.state.cache_client
        await cache_client.set(f"document:{document_id}", metadata.model_dump())
        
        logger.info(f"Uploaded document {document_id}: {file.filename}")
        
        # TODO: Trigger ingestion service to process the document
        # This would be done via gRPC call to ingestion-service
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename or "unknown",
            size=len(file_content),
            status="uploaded",
            message="Document uploaded successfully. Processing will begin shortly.",
        )
        
    except AzureError as e:
        logger.error(f"Azure error during upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}")
async def get_document_metadata(
    document_id: str, request: Request
) -> DocumentMetadata:
    """Get document metadata.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        DocumentMetadata: Document metadata

    Raises:
        HTTPException: If document not found
    """
    cache_client = request.app.state.cache_client

    # Try to get from cache
    metadata = await cache_client.get(f"document:{document_id}")

    if metadata:
        return DocumentMetadata(**metadata)

    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, request: Request) -> StreamingResponse:
    """Download a document from blob storage.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        StreamingResponse: File download stream

    Raises:
        HTTPException: If document not found
    """
    cache_client = request.app.state.cache_client

    # Get metadata from cache
    metadata = await cache_client.get(f"document:{document_id}")

    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Get blob client
        blob_service_client = request.app.state.blob_service_client
        container_client = blob_service_client.get_container_client(
            settings.azure_storage_container_name
        )

        blob_name = f"{document_id}/{metadata['filename']}"
        blob_client = container_client.get_blob_client(blob_name)

        # Download blob
        stream = await blob_client.download_blob()

        async def iterfile():
            async for chunk in stream.chunks():
                yield chunk

        return StreamingResponse(
            iterfile(),
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename={metadata['filename']}"
            },
        )

    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found in storage")
    except AzureError as e:
        logger.error(f"Azure error during download: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> DocumentListResponse:
    """List all documents.

    Args:
        request: FastAPI request object
        skip: Number of documents to skip
        limit: Maximum number of documents to return

    Returns:
        DocumentListResponse: List of documents
    """
    # TODO: Implement proper pagination with database or blob storage listing
    # For now, this is a placeholder that would need a proper storage backend

    return DocumentListResponse(
        documents=[],
        total_count=0,
    )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, request: Request) -> dict[str, str]:
    """Delete a document.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException: If document not found or deletion fails
    """
    cache_client = request.app.state.cache_client

    # Get metadata from cache
    metadata = await cache_client.get(f"document:{document_id}")

    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Delete from blob storage
        blob_service_client = request.app.state.blob_service_client
        container_client = blob_service_client.get_container_client(
            settings.azure_storage_container_name
        )

        blob_name = f"{document_id}/{metadata['filename']}"
        blob_client = container_client.get_blob_client(blob_name)
        await blob_client.delete_blob()

        # Delete from cache
        await cache_client.delete(f"document:{document_id}")

        logger.info(f"Deleted document {document_id}")

        return {"status": "success", "message": "Document deleted successfully"}

    except ResourceNotFoundError:
        # Document not in storage but in cache - clean up cache
        await cache_client.delete(f"document:{document_id}")
        raise HTTPException(status_code=404, detail="Document not found in storage")
    except AzureError as e:
        logger.error(f"Azure error during deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during deletion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


