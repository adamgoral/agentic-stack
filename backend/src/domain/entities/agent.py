"""Agent domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AgentCapability(str, Enum):
    """Agent capabilities."""

    RESEARCH = "research"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    DATA_ANALYSIS = "data_analysis"
    VISUALIZATION = "visualization"
    WEB_SEARCH = "web_search"
    DOCUMENTATION = "documentation"


class AgentStatus(str, Enum):
    """Agent operational status."""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Agent:
    """Domain entity representing an AI agent."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate agent after initialization."""
        if not self.name:
            raise ValueError("Agent name is required")
        if not self.capabilities:
            raise ValueError("Agent must have at least one capability")

    def can_handle(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def is_available(self) -> bool:
        """Check if agent is available for tasks."""
        return self.status == AgentStatus.IDLE

    def set_busy(self) -> None:
        """Mark agent as busy."""
        self.status = AgentStatus.BUSY
        self.updated_at = datetime.utcnow()

    def set_idle(self) -> None:
        """Mark agent as idle."""
        self.status = AgentStatus.IDLE
        self.updated_at = datetime.utcnow()

    def set_error(self, error_msg: Optional[str] = None) -> None:
        """Mark agent as in error state."""
        self.status = AgentStatus.ERROR
        if error_msg:
            self.metadata["last_error"] = error_msg
        self.updated_at = datetime.utcnow()