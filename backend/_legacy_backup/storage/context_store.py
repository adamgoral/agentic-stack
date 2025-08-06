"""
Context Store - Manages conversation context and task persistence
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
from models.state import ConversationState, AgentTaskState

logger = logging.getLogger(__name__)


class ContextStore:
    """
    Storage layer for conversation contexts and task states
    Uses Redis for fast access and persistence
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Context store initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory storage if Redis is not available
            self.redis_client = None
            self._memory_store = {}
            logger.warning("Using in-memory storage (data will not persist)")

    async def store_context(self, context: ConversationState) -> bool:
        """Store or update a conversation context"""
        try:
            key = f"context:{context.context_id}"
            value = context.model_dump_json()

            if self.redis_client:
                await self.redis_client.set(key, value)
                # Set expiration to 24 hours
                await self.redis_client.expire(key, 86400)
            else:
                self._memory_store[key] = value

            logger.debug(f"Stored context: {context.context_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False

    async def get_context(self, context_id: str) -> Optional[ConversationState]:
        """Retrieve a conversation context"""
        try:
            key = f"context:{context_id}"

            if self.redis_client:
                value = await self.redis_client.get(key)
            else:
                value = self._memory_store.get(key)

            if value:
                return ConversationState.model_validate_json(value)
            return None

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None

    async def store_task(self, task: AgentTaskState) -> bool:
        """Store or update a task state"""
        try:
            key = f"task:{task.task_id}"
            value = task.model_dump_json()

            if self.redis_client:
                await self.redis_client.set(key, value)
                # Set expiration to 24 hours
                await self.redis_client.expire(key, 86400)
            else:
                self._memory_store[key] = value

            logger.debug(f"Stored task: {task.task_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing task: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[AgentTaskState]:
        """Retrieve a task state"""
        try:
            key = f"task:{task_id}"

            if self.redis_client:
                value = await self.redis_client.get(key)
            else:
                value = self._memory_store.get(key)

            if value:
                return AgentTaskState.model_validate_json(value)
            return None

        except Exception as e:
            logger.error(f"Error retrieving task: {e}")
            return None

    async def get_context_tasks(self, context_id: str) -> List[AgentTaskState]:
        """Get all tasks associated with a context"""
        tasks = []
        try:
            if self.redis_client:
                # Use Redis scan to find all tasks
                cursor = 0
                pattern = "task:*"
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                    for key in keys:
                        value = await self.redis_client.get(key)
                        if value:
                            task = AgentTaskState.model_validate_json(value)
                            # Check if task belongs to this context
                            if task.input_data.get("context_id") == context_id:
                                tasks.append(task)
                    if cursor == 0:
                        break
            else:
                # In-memory search
                for key, value in self._memory_store.items():
                    if key.startswith("task:"):
                        task = AgentTaskState.model_validate_json(value)
                        if task.input_data.get("context_id") == context_id:
                            tasks.append(task)

            return tasks

        except Exception as e:
            logger.error(f"Error getting context tasks: {e}")
            return []

    async def list_contexts(self, limit: int = 100) -> List[str]:
        """List all context IDs"""
        contexts = []
        try:
            if self.redis_client:
                cursor = 0
                pattern = "context:*"
                count = 0
                while count < limit:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match=pattern, count=min(100, limit - count)
                    )
                    for key in keys:
                        contexts.append(key.replace("context:", ""))
                        count += 1
                        if count >= limit:
                            break
                    if cursor == 0:
                        break
            else:
                for key in self._memory_store.keys():
                    if key.startswith("context:"):
                        contexts.append(key.replace("context:", ""))
                        if len(contexts) >= limit:
                            break

            return contexts

        except Exception as e:
            logger.error(f"Error listing contexts: {e}")
            return []

    async def delete_context(self, context_id: str) -> bool:
        """Delete a context and all associated tasks"""
        try:
            # Delete context
            context_key = f"context:{context_id}"
            if self.redis_client:
                await self.redis_client.delete(context_key)
            else:
                self._memory_store.pop(context_key, None)

            # Delete associated tasks
            tasks = await self.get_context_tasks(context_id)
            for task in tasks:
                task_key = f"task:{task.task_id}"
                if self.redis_client:
                    await self.redis_client.delete(task_key)
                else:
                    self._memory_store.pop(task_key, None)

            logger.info(f"Deleted context {context_id} and {len(tasks)} tasks")
            return True

        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get storage metrics"""
        try:
            if self.redis_client:
                info = await self.redis_client.info()
                return {
                    "storage_type": "redis",
                    "connected": True,
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "total_keys": await self.redis_client.dbsize(),
                    "contexts": len(await self.list_contexts()),
                }
            else:
                return {
                    "storage_type": "memory",
                    "connected": True,
                    "total_keys": len(self._memory_store),
                    "contexts": len(
                        [k for k in self._memory_store.keys() if k.startswith("context:")]
                    ),
                    "tasks": len([k for k in self._memory_store.keys() if k.startswith("task:")]),
                }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close storage connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Context store closed")

