"""Orchestrator service - coordinates agent execution and task management."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from src.domain.entities import (
    Agent,
    AgentCapability,
    Conversation,
    Task,
    TaskPriority,
)
from src.domain.exceptions import AgentNotAvailableError, TaskExecutionError

logger = logging.getLogger(__name__)


class OrchestratorService:
    """Service for orchestrating multi-agent workflows."""

    def __init__(
        self,
        agent_service: "AgentService",
        task_service: "TaskService",
        conversation_service: "ConversationService",
    ) -> None:
        """Initialize orchestrator service."""
        self.agent_service = agent_service
        self.task_service = task_service
        self.conversation_service = conversation_service

    async def process_user_request(
        self,
        message: str,
        conversation_id: Optional[UUID] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user request and coordinate agent execution."""
        # Get or create conversation
        if conversation_id:
            conversation = await self.conversation_service.get_conversation(conversation_id)
        else:
            conversation = await self.conversation_service.create_conversation(
                user_preferences=user_preferences or {}
            )

        # Update current task
        conversation.update_current_task(message)
        await self.conversation_service.update_conversation(conversation)

        # Analyze request and determine required capabilities
        required_capabilities = await self._analyze_request(message)

        # Create tasks for each capability
        tasks = await self._create_tasks(
            message, conversation.id, required_capabilities
        )

        # Execute tasks
        async for result in self._execute_tasks(tasks, conversation):
            yield result

        # Mark conversation as completed
        conversation.complete()
        await self.conversation_service.update_conversation(conversation)

    async def _analyze_request(self, message: str) -> List[AgentCapability]:
        """Analyze user request and determine required capabilities."""
        capabilities = []

        # Simple heuristic-based analysis (can be replaced with AI model)
        message_lower = message.lower()

        if any(word in message_lower for word in ["search", "find", "research", "look up"]):
            capabilities.append(AgentCapability.WEB_SEARCH)
            capabilities.append(AgentCapability.RESEARCH)

        if any(word in message_lower for word in ["code", "implement", "function", "debug"]):
            capabilities.append(AgentCapability.CODE_GENERATION)
            capabilities.append(AgentCapability.CODE_ANALYSIS)

        if any(word in message_lower for word in ["analyze", "data", "metrics", "statistics"]):
            capabilities.append(AgentCapability.DATA_ANALYSIS)

        if any(word in message_lower for word in ["chart", "graph", "visualize", "plot"]):
            capabilities.append(AgentCapability.VISUALIZATION)

        # Default to research if no specific capability detected
        if not capabilities:
            capabilities.append(AgentCapability.RESEARCH)

        return capabilities

    async def _create_tasks(
        self,
        message: str,
        conversation_id: UUID,
        capabilities: List[AgentCapability],
    ) -> List[Task]:
        """Create tasks for required capabilities."""
        tasks = []

        for capability in capabilities:
            # Find available agent for capability
            agent = await self.agent_service.find_available_agent(capability)
            if not agent:
                logger.warning(f"No available agent for capability: {capability}")
                continue

            # Create task
            task = await self.task_service.create_task(
                title=f"{capability.value} task",
                description=message,
                agent_id=agent.id,
                conversation_id=conversation_id,
                priority=TaskPriority.MEDIUM,
            )
            tasks.append(task)

        return tasks

    async def _execute_tasks(
        self, tasks: List[Task], conversation: Conversation
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute tasks and yield results."""
        for task in tasks:
            try:
                # Start task
                await self.task_service.start_task(task.id)

                # Get agent
                agent = await self.agent_service.get_agent(task.agent_id)

                # Yield progress event
                yield {
                    "type": "task_started",
                    "task_id": str(task.id),
                    "agent": agent.name,
                    "message": f"Starting {task.title}",
                }

                # Execute task via agent
                result = await self.agent_service.execute_task(agent.id, task)

                # Complete task
                await self.task_service.complete_task(task.id, result)

                # Store agent output in conversation
                conversation.store_agent_output(agent.name, result)

                # Yield result event
                yield {
                    "type": "task_completed",
                    "task_id": str(task.id),
                    "agent": agent.name,
                    "result": result,
                }

            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                await self.task_service.fail_task(task.id, str(e))

                yield {
                    "type": "task_failed",
                    "task_id": str(task.id),
                    "error": str(e),
                }

    async def get_agent_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        agents = await self.agent_service.list_agents()
        return [
            {
                "id": str(agent.id),
                "name": agent.name,
                "status": agent.status.value,
                "capabilities": [cap.value for cap in agent.capabilities],
            }
            for agent in agents
        ]