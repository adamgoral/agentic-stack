"""Task-related domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

from .base import DomainEvent


@dataclass
class TaskCreatedEvent(DomainEvent):
    """Event emitted when a task is created."""

    task_id: UUID = field(default_factory=UUID)
    task_type: str = ""
    conversation_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStartedEvent(DomainEvent):
    """Event emitted when a task starts processing."""

    task_id: UUID = field(default_factory=UUID)
    task_type: str = ""
    agent_id: Optional[UUID] = None


@dataclass
class TaskCompletedEvent(DomainEvent):
    """Event emitted when a task completes."""

    task_id: UUID = field(default_factory=UUID)
    task_type: str = ""
    agent_id: Optional[UUID] = None
    result: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskFailedEvent(DomainEvent):
    """Event emitted when a task fails."""

    task_id: UUID = field(default_factory=UUID)
    task_type: str = ""
    agent_id: Optional[UUID] = None
    error: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)