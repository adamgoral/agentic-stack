"""Task management endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.v1.dependencies import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Task creation request."""
    
    title: str
    description: str
    agent_id: Optional[str] = None
    priority: str = "medium"


class TaskUpdate(BaseModel):
    """Task update request."""
    
    status: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 100,
    task_service: Any = Depends(get_task_service),
) -> List[Dict[str, Any]]:
    """List tasks with optional filtering."""
    tasks = await task_service.list_tasks(status=status, limit=limit)
    return [
        {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
        }
        for task in tasks
    ]


@router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    task_service: Any = Depends(get_task_service),
) -> Dict[str, Any]:
    """Get task details."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "agent_id": str(task.agent_id) if task.agent_id else None,
        "input_data": task.input_data,
        "output_data": task.output_data,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "duration_seconds": task.duration_seconds,
    }


@router.post("")
async def create_task(
    task_data: TaskCreate,
    task_service: Any = Depends(get_task_service),
) -> Dict[str, Any]:
    """Create a new task."""
    task = await task_service.create_task(
        title=task_data.title,
        description=task_data.description,
        agent_id=task_data.agent_id,
        priority=task_data.priority,
    )
    return {"id": str(task.id), "status": "created"}


@router.patch("/{task_id}")
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    task_service: Any = Depends(get_task_service),
) -> Dict[str, Any]:
    """Update task status or output."""
    task = await task_service.update_task(task_id, update_data.dict(exclude_none=True))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return {"id": str(task.id), "status": task.status.value}


@router.delete("/{task_id}")
async def cancel_task(
    task_id: UUID,
    task_service: Any = Depends(get_task_service),
) -> Dict[str, Any]:
    """Cancel a task."""
    success = await task_service.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found or already completed",
        )
    return {"id": str(task_id), "status": "cancelled"}