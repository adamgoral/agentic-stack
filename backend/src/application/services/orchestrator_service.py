"""Orchestrator service - coordinates agent execution and task management."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from src.domain.entities import (
    Agent,
    AgentCapability,
    Conversation,
    Message,
    MessageType,
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

    async def process_request(
        self,
        messages: List[Message],
        context_id: str,
    ) -> Dict[str, Any]:
        """Process an AG-UI request with multiple messages."""
        try:
            # Get the last user message
            user_message = None
            for msg in reversed(messages):
                if msg.type == MessageType.USER_INPUT:
                    user_message = msg.content
                    break
            
            if not user_message:
                return {
                    "response": "I didn't receive a message to process.",
                    "agents_used": [],
                    "processing_time": 0
                }
            
            # Analyze and determine capabilities needed
            required_capabilities = await self._analyze_request(user_message)
            
            # For now, return a simple response
            # In production, this would delegate to actual agents
            agents_used = []
            for cap in required_capabilities:
                if cap == AgentCapability.RESEARCH:
                    agents_used.append("research_agent")
                elif cap in [AgentCapability.CODE_GENERATION, AgentCapability.CODE_ANALYSIS]:
                    agents_used.append("code_agent")
                elif cap in [AgentCapability.DATA_ANALYSIS, AgentCapability.VISUALIZATION]:
                    agents_used.append("analytics_agent")
            
            # Check if we have API keys configured
            import os
            has_openai = bool(os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("your_"))
            has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_API_KEY").startswith("your_"))
            
            if has_openai or has_anthropic:
                # We have API keys - provide a more intelligent response
                response = f"I can help you with that! Based on your request: '{user_message}'\n\n"
                
                if required_capabilities:
                    response += f"I'll use the following capabilities: {', '.join([cap.value for cap in required_capabilities])}\n\n"
                    
                    # Provide capability-specific responses
                    if AgentCapability.RESEARCH in required_capabilities:
                        response += "🔍 **Research**: I can search for information and provide comprehensive answers.\n"
                    if AgentCapability.CODE_GENERATION in required_capabilities or AgentCapability.CODE_ANALYSIS in required_capabilities:
                        response += "💻 **Code**: I can generate, analyze, and debug code in multiple languages.\n"
                    if AgentCapability.DATA_ANALYSIS in required_capabilities:
                        response += "📊 **Analytics**: I can analyze data and provide insights.\n"
                    
                response += "\nHow would you like me to proceed with your request?"
            else:
                # No API keys - provide informative message
                response = f"I understand you want me to help with: {user_message}\n\n"
                
                if required_capabilities:
                    response += f"I would use the following capabilities: {', '.join([cap.value for cap in required_capabilities])}\n\n"
                
                response += "However, the system needs API keys configured to provide actual AI responses. "
                response += "Please add your OpenAI or Anthropic API keys to the .env file."
            
            return {
                "response": response,
                "agents_used": agents_used,
                "processing_time": 0.1,
                "capabilities_detected": [cap.value for cap in required_capabilities]
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "response": f"An error occurred while processing your request: {str(e)}",
                "agents_used": [],
                "processing_time": 0,
                "error": str(e)
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