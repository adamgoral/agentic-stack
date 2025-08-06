"""Health check endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.v1.dependencies import get_orchestrator_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(
    orchestrator_service: Any = Depends(get_orchestrator_service),
) -> Dict[str, Any]:
    """Readiness check with service status."""
    agents_status = await orchestrator_service.get_agent_status()
    
    return {
        "status": "ready",
        "services": {
            "orchestrator": "running",
            "agents": len(agents_status),
        },
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}