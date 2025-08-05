"""
A2A Protocol Manager - Handles agent-to-agent communication
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class A2AManager:
    """
    Manages A2A (Agent-to-Agent) protocol communication
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.clients: Dict[str, httpx.AsyncClient] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    async def _get_client(self, agent_url: str) -> httpx.AsyncClient:
        """Get or create HTTP client for an agent"""
        if agent_url not in self.clients:
            self.clients[agent_url] = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self.clients[agent_url]

    async def send_task_to_agent(
        self,
        agent_url: str,
        message: str,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a task to another agent via A2A protocol

        Args:
            agent_url: URL of the target agent's A2A endpoint
            message: The task message to send
            context_id: Optional context ID for conversation continuity
            metadata: Optional metadata to include

        Returns:
            Response from the agent including task_id
        """
        client = await self._get_client(agent_url)

        # Generate context_id if not provided
        if not context_id:
            context_id = str(uuid.uuid4())

        # Prepare A2A request payload
        payload = {
            "message": message,
            "context_id": context_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            logger.info(f"Sending A2A task to {agent_url}: {message[:100]}...")

            # Send request to agent's A2A endpoint
            response = await client.post(
                f"{agent_url}/tasks",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-A2A-Version": "0.2.5",  # A2A protocol version
                },
            )

            response.raise_for_status()
            result = response.json()

            # Track active task
            task_id = result.get("task_id")
            if task_id:
                self.active_tasks[task_id] = {
                    "agent_url": agent_url,
                    "context_id": context_id,
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                }

            logger.info(f"A2A task created: {task_id}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending A2A task to {agent_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending A2A task to {agent_url}: {e}")
            raise

    async def get_task_result(
        self, agent_url: str, task_id: str, wait: bool = True
    ) -> Dict[str, Any]:
        """
        Get the result of a task from an agent

        Args:
            agent_url: URL of the agent's A2A endpoint
            task_id: ID of the task to retrieve
            wait: Whether to wait for task completion

        Returns:
            Task result including status and artifacts
        """
        client = await self._get_client(agent_url)

        try:
            endpoint = f"{agent_url}/tasks/{task_id}"
            if wait:
                endpoint += "?wait=true"

            logger.info(f"Getting A2A task result: {task_id}")

            response = await client.get(endpoint, headers={"X-A2A-Version": "0.2.5"})

            response.raise_for_status()
            result = response.json()

            # Update task tracking
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = result.get("status", "unknown")
                if result.get("status") in ["completed", "failed"]:
                    self.active_tasks[task_id]["completed_at"] = datetime.utcnow()

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting task result from {agent_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting task result from {agent_url}: {e}")
            raise

    async def get_context_history(self, agent_url: str, context_id: str) -> Dict[str, Any]:
        """
        Get the conversation history for a context

        Args:
            agent_url: URL of the agent's A2A endpoint
            context_id: Context ID to retrieve history for

        Returns:
            Conversation history and related tasks
        """
        client = await self._get_client(agent_url)

        try:
            logger.info(f"Getting context history: {context_id}")

            response = await client.get(
                f"{agent_url}/contexts/{context_id}", headers={"X-A2A-Version": "0.2.5"}
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting context from {agent_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting context from {agent_url}: {e}")
            raise

    async def ping_agent(self, agent_url: str) -> bool:
        """
        Check if an agent is reachable via A2A

        Args:
            agent_url: URL of the agent's A2A endpoint

        Returns:
            True if agent is reachable, False otherwise
        """
        client = await self._get_client(agent_url)

        try:
            response = await client.get(f"{agent_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Agent {agent_url} not reachable: {e}")
            return False

    async def stream_task_events(self, agent_url: str, task_id: str):
        """
        Stream events from a running task (if supported by agent)

        Args:
            agent_url: URL of the agent's A2A endpoint
            task_id: ID of the task to stream

        Yields:
            Event dictionaries from the task execution
        """
        client = await self._get_client(agent_url)

        try:
            async with client.stream(
                "GET",
                f"{agent_url}/tasks/{task_id}/stream",
                headers={"X-A2A-Version": "0.2.5", "Accept": "text/event-stream"},
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in stream: {data}")

        except Exception as e:
            logger.error(f"Error streaming task events: {e}")
            raise

    async def cancel_task(self, agent_url: str, task_id: str) -> bool:
        """
        Cancel a running task

        Args:
            agent_url: URL of the agent's A2A endpoint
            task_id: ID of the task to cancel

        Returns:
            True if cancellation was successful
        """
        client = await self._get_client(agent_url)

        try:
            logger.info(f"Cancelling A2A task: {task_id}")

            response = await client.delete(
                f"{agent_url}/tasks/{task_id}", headers={"X-A2A-Version": "0.2.5"}
            )

            if response.status_code in [200, 204]:
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]["status"] = "cancelled"
                    self.active_tasks[task_id]["cancelled_at"] = datetime.utcnow()
                return True
            return False

        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return False

    async def close(self):
        """Close all HTTP clients"""
        for client in self.clients.values():
            await client.aclose()
        self.clients.clear()
        logger.info("A2A manager closed")

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks"""
        return self.active_tasks.copy()

    def clear_completed_tasks(self):
        """Clear completed tasks from tracking"""
        completed = [
            task_id
            for task_id, task in self.active_tasks.items()
            if task["status"] in ["completed", "failed", "cancelled"]
        ]
        for task_id in completed:
            del self.active_tasks[task_id]
        logger.info(f"Cleared {len(completed)} completed tasks")

