"""Agent-related domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

from .base import DomainEvent


@dataclass
class AgentStartedEvent(DomainEvent):
    """Event emitted when an agent starts processing."""

    agent_id: UUID = field(default_factory=UUID)
    agent_type: str = ""
    task_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


@dataclass
class AgentCompletedEvent(DomainEvent):
    """Event emitted when an agent completes processing."""

    agent_id: UUID = field(default_factory=UUID)
    agent_type: str = ""
    task_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    result: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentFailedEvent(DomainEvent):
    """Event emitted when an agent fails."""

    agent_id: UUID = field(default_factory=UUID)
    agent_type: str = ""
    task_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    error: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)