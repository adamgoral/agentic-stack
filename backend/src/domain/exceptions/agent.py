"""Agent-related domain exceptions."""


class AgentError(Exception):
    """Base exception for agent-related errors."""


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent with ID {agent_id} not found")
        self.agent_id = agent_id


class AgentNotAvailableError(AgentError):
    """Raised when an agent is not available for task execution."""

    def __init__(self, agent_name: str, reason: str = "Agent is busy") -> None:
        super().__init__(f"Agent {agent_name} is not available: {reason}")
        self.agent_name = agent_name
        self.reason = reason


class InvalidAgentCapabilityError(AgentError):
    """Raised when an invalid capability is requested from an agent."""

    def __init__(self, agent_name: str, capability: str) -> None:
        super().__init__(f"Agent {agent_name} does not have capability: {capability}")
        self.agent_name = agent_name
        self.capability = capability