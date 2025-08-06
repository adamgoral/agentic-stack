"""Conversation-related domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEvent


@dataclass
class ConversationStartedEvent(DomainEvent):
    """Event emitted when a conversation starts."""

    conversation_id: UUID = field(default_factory=UUID)
    participant_ids: List[UUID] = field(default_factory=list)
    initial_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationCompletedEvent(DomainEvent):
    """Event emitted when a conversation completes."""

    conversation_id: UUID = field(default_factory=UUID)
    participant_ids: List[UUID] = field(default_factory=list)
    final_result: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0