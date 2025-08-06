"""
Task Manager for storing and retrieving agent task results
Shared by all specialized agents for A2A task tracking
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgentTaskManager:
    """
    Manages task storage and retrieval for A2A protocol
    Uses in-memory storage for MVP (can be replaced with Redis later)
    """
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_locks: Dict[str, asyncio.Lock] = {}
    
    async def create_task(self, task_id: str, message: str, context_id: str, metadata: Dict[str, Any]) -> None:
        """Create a new task entry"""
        async with self._get_lock(task_id):
            self.tasks[task_id] = {
                "task_id": task_id,
                "message": message,
                "context_id": context_id,
                "metadata": metadata,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "result": None,
                "error": None,
                "completed_at": None
            }
            logger.info(f"Created task {task_id}")
    
    async def update_task_status(self, task_id: str, status: str, result: Any = None, error: str = None) -> None:
        """Update task status and result"""
        async with self._get_lock(task_id):
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return
            
            self.tasks[task_id]["status"] = status
            
            if result is not None:
                self.tasks[task_id]["result"] = result
            
            if error is not None:
                self.tasks[task_id]["error"] = error
            
            if status in ["completed", "failed"]:
                self.tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated task {task_id} to status {status}")
    
    async def get_task(self, task_id: str, wait: bool = False, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Get task by ID
        
        Args:
            task_id: Task ID to retrieve
            wait: If True, wait for task completion
            timeout: Maximum time to wait in seconds
            
        Returns:
            Task data or None if not found
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return None
        
        if not wait:
            return self.tasks[task_id].copy()
        
        # Wait for task completion
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            task = self.tasks.get(task_id)
            if task and task["status"] in ["completed", "failed"]:
                return task.copy()
            await asyncio.sleep(0.1)  # Poll every 100ms
        
        # Timeout reached
        task = self.tasks.get(task_id)
        if task:
            task_copy = task.copy()
            if task_copy["status"] == "pending":
                task_copy["status"] = "timeout"
                task_copy["error"] = f"Task timed out after {timeout} seconds"
            return task_copy
        
        return None
    
    async def start_task_processing(self, task_id: str) -> None:
        """Mark task as in_progress"""
        await self.update_task_status(task_id, "in_progress")
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> None:
        """Mark task as completed with result"""
        await self.update_task_status(task_id, "completed", result=result)
    
    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed with error"""
        await self.update_task_status(task_id, "failed", error=error)
    
    def _get_lock(self, task_id: str) -> asyncio.Lock:
        """Get or create a lock for a task"""
        if task_id not in self.task_locks:
            self.task_locks[task_id] = asyncio.Lock()
        return self.task_locks[task_id]
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks (for debugging)"""
        return self.tasks.copy()
    
    def clear_completed_tasks(self) -> int:
        """Clear completed/failed tasks older than 1 hour"""
        now = datetime.utcnow()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task["status"] in ["completed", "failed"]:
                completed_at = task.get("completed_at")
                if completed_at:
                    completed_time = datetime.fromisoformat(completed_at)
                    if (now - completed_time).total_seconds() > 3600:  # 1 hour
                        tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.task_locks:
                del self.task_locks[task_id]
        
        return len(tasks_to_remove)


# Global instance for sharing across agent processes
task_manager = AgentTaskManager()