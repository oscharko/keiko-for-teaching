"""Health check endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for liveness probe."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, str]:
    """Readiness check endpoint - verifies dependencies are available."""
    # Check if blob service client is initialized
    if not hasattr(request.app.state, "blob_service_client"):
        return {"status": "not ready", "reason": "blob service client not initialized"}
    
    # Check if cache client is connected
    if not hasattr(request.app.state, "cache_client"):
        return {"status": "not ready", "reason": "cache client not initialized"}
    
    return {"status": "ready"}

