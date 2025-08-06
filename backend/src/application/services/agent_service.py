"""Agent service - manages agent lifecycle and execution."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.entities import Agent, AgentCapability, AgentStatus
from src.domain.exceptions import AgentNotAvailableError, AgentNotFoundError

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents."""

    def __init__(self, agent_repository: Any) -> None:
        """Initialize agent service."""
        self.agent_repository = agent_repository
        self._agents: Dict[UUID, Agent] = {}

    async def register_agent(self, agent: Agent) -> Agent:
        """Register a new agent."""
        self._agents[agent.id] = agent
        await self.agent_repository.save(str(agent.id), agent)
        logger.info(f"Registered agent: {agent.name} ({agent.id})")
        return agent

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        if agent_id in self._agents:
            return self._agents[agent_id]
        
        agent = await self.agent_repository.get(str(agent_id), Agent)
        if agent:
            self._agents[agent_id] = agent
        return agent

    async def list_agents(self) -> List[Agent]:
        """List all registered agents."""
        return list(self._agents.values())

    async def find_available_agent(self, capability: AgentCapability) -> Optional[Agent]:
        """Find an available agent with the specified capability."""
        for agent in self._agents.values():
            if agent.can_handle(capability) and agent.is_available():
                return agent
        return None

    async def execute_task(self, agent_id: UUID, task: Any) -> Dict[str, Any]:
        """Execute a task on a specific agent."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))
        
        if not agent.is_available():
            raise AgentNotAvailableError(agent.name, f"Agent status: {agent.status}")
        
        try:
            # Mark agent as busy
            agent.set_busy()
            await self.agent_repository.save(str(agent.id), agent)
            
            # Execute task (placeholder - actual implementation would delegate to agent)
            result = {
                "agent": agent.name,
                "task_id": str(task.id) if hasattr(task, "id") else None,
                "status": "completed",
                "output": f"Task executed by {agent.name}",
            }
            
            # Mark agent as idle
            agent.set_idle()
            await self.agent_repository.save(str(agent.id), agent)
            
            return result
            
        except Exception as e:
            logger.error(f"Agent {agent.name} execution failed: {e}")
            agent.set_error(str(e))
            await self.agent_repository.save(str(agent.id), agent)
            raise

    async def update_agent_status(self, agent_id: UUID, status: AgentStatus) -> bool:
        """Update agent status."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.status = status
        agent.updated_at = datetime.utcnow()
        await self.agent_repository.save(str(agent.id), agent)
        return True