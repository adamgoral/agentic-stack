"""Conversation domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ConversationStatus(str, Enum):
    """Conversation status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Conversation:
    """Domain entity representing a conversation context."""

    id: UUID = field(default_factory=uuid4)
    user_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    title: Optional[str] = None
    current_task: Optional[str] = None
    task_ids: List[UUID] = field(default_factory=list)
    message_ids: List[UUID] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_task(self, task_id: UUID) -> None:
        """Add a task to the conversation."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self.updated_at = datetime.utcnow()

    def add_message(self, message_id: UUID) -> None:
        """Add a message to the conversation."""
        if message_id not in self.message_ids:
            self.message_ids.append(message_id)
            self.updated_at = datetime.utcnow()

    def store_agent_output(self, agent_name: str, output: Any) -> None:
        """Store output from an agent."""
        self.agent_outputs[agent_name] = {
            "output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.updated_at = datetime.utcnow()

    def update_current_task(self, task: str) -> None:
        """Update the current task being processed."""
        self.current_task = task
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the conversation."""
        self.status = ConversationStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume the conversation."""
        if self.status == ConversationStatus.PAUSED:
            self.status = ConversationStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE