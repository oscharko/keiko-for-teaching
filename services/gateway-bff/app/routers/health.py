"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy", "service": "gateway-bff", "version": "0.1.0"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Return service readiness status."""
    return {"status": "ready"}

