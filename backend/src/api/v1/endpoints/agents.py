"""Agent management endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import get_agent_service, get_orchestrator_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents(
    orchestrator_service: Any = Depends(get_orchestrator_service),
) -> List[Dict[str, Any]]:
    """List all available agents and their status."""
    return await orchestrator_service.get_agent_status()


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    agent_service: Any = Depends(get_agent_service),
) -> Dict[str, Any]:
    """Get specific agent details."""
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "status": agent.status.value,
        "capabilities": [cap.value for cap in agent.capabilities],
    }


@router.post("/{agent_id}/execute")
async def execute_agent_task(
    agent_id: str,
    task_data: Dict[str, Any],
    agent_service: Any = Depends(get_agent_service),
) -> Dict[str, Any]:
    """Execute a task on a specific agent."""
    try:
        result = await agent_service.execute_task(agent_id, task_data)
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )