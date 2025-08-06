"""Task service - manages task lifecycle."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.entities import Task, TaskPriority, TaskStatus
from src.domain.exceptions import InvalidTaskStateError, TaskNotFoundError

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks."""

    def __init__(self, task_repository: Any) -> None:
        """Initialize task service."""
        self.task_repository = task_repository

    async def create_task(
        self,
        title: str,
        description: str,
        agent_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            agent_id=agent_id,
            conversation_id=conversation_id,
            priority=priority,
        )
        
        await self.task_repository.save(str(task.id), task)
        logger.info(f"Created task: {task.title} ({task.id})")
        return task

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID."""
        return await self.task_repository.get(str(task_id), Task)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
        """List tasks with optional filtering."""
        # Placeholder implementation
        all_tasks = []
        task_keys = await self.task_repository.list_keys("*")
        
        for key in task_keys[:limit]:
            task = await self.task_repository.get(key, Task)
            if task:
                if status is None or task.status.value == status:
                    all_tasks.append(task)
        
        return all_tasks

    async def start_task(self, task_id: UUID) -> Task:
        """Start a task."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        task.start()
        await self.task_repository.save(str(task.id), task)
        logger.info(f"Started task: {task.title} ({task.id})")
        return task

    async def complete_task(self, task_id: UUID, output: Dict[str, Any]) -> Task:
        """Complete a task with output."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        task.complete(output)
        await self.task_repository.save(str(task.id), task)
        logger.info(f"Completed task: {task.title} ({task.id})")
        return task

    async def fail_task(self, task_id: UUID, error: str) -> Task:
        """Mark a task as failed."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        task.fail(error)
        await self.task_repository.save(str(task.id), task)
        logger.error(f"Task failed: {task.title} ({task.id}) - {error}")
        return task

    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a task."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        try:
            task.cancel()
            await self.task_repository.save(str(task.id), task)
            logger.info(f"Cancelled task: {task.title} ({task.id})")
            return True
        except ValueError:
            return False

    async def update_task(self, task_id: UUID, updates: Dict[str, Any]) -> Optional[Task]:
        """Update task fields."""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        # Update allowed fields
        if "status" in updates:
            task.status = TaskStatus(updates["status"])
        if "output_data" in updates:
            task.output_data = updates["output_data"]
        
        await self.task_repository.save(str(task.id), task)
        return task