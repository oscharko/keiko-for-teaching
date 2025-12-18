"""Document proxy router - forwards requests to document service."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...), request: Request = None  # noqa: B008
) -> dict[str, Any]:
    """Proxy document upload to document service.

    Args:
        file: File to upload
        request: FastAPI request object

    Returns:
        dict: Upload response from document service

    Raises:
        HTTPException: If document service request fails
    """
    http_client: httpx.AsyncClient = request.app.state.http_client

    try:
        # Read file content
        file_content = await file.read()

        # Forward to document service
        files = {"file": (file.filename, file_content, file.content_type)}
        response = await http_client.post(
            f"{settings.document_service_url}/api/documents/upload",
            files=files,
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Document service error: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Document service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Document service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Document service unavailable"
        ) from e


@router.get("/documents/{document_id}")
async def get_document_metadata(
    document_id: str, request: Request
) -> dict[str, Any]:
    """Get document metadata from document service.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        dict: Document metadata

    Raises:
        HTTPException: If document service request fails
    """
    http_client: httpx.AsyncClient = request.app.state.http_client

    try:
        response = await http_client.get(
            f"{settings.document_service_url}/api/documents/{document_id}",
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Document service error: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Document service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Document service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Document service unavailable"
        ) from e


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str, request: Request
) -> StreamingResponse:
    """Download document from document service.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        StreamingResponse: File download stream

    Raises:
        HTTPException: If document service request fails
    """
    http_client: httpx.AsyncClient = request.app.state.http_client

    try:
        response = await http_client.get(
            f"{settings.document_service_url}/api/documents/{document_id}/download",
            timeout=60.0,
        )
        response.raise_for_status()

        # Stream the response
        return StreamingResponse(
            response.aiter_bytes(),
            media_type=response.headers.get("content-type", "application/octet-stream"),
            headers=dict(response.headers),
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"Document service error: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Document service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Document service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Document service unavailable"
        ) from e


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, request: Request) -> dict[str, Any]:
    """Delete document via document service.

    Args:
        document_id: Document ID
        request: FastAPI request object

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException: If document service request fails
    """
    http_client: httpx.AsyncClient = request.app.state.http_client

    try:
        response = await http_client.delete(
            f"{settings.document_service_url}/api/documents/{document_id}",
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Document service error: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Document service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error(f"Document service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Document service unavailable"
        ) from e

