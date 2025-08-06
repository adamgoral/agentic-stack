"""Message domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class MessageType(str, Enum):
    """Message types in the system."""

    USER_INPUT = "user_input"
    AGENT_OUTPUT = "agent_output"
    SYSTEM = "system"
    ERROR = "error"
    NOTIFICATION = "notification"
    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class Message:
    """Domain entity representing a message in the system."""

    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.USER_INPUT
    content: str = ""
    sender: str = ""
    recipient: Optional[str] = None
    conversation_id: Optional[UUID] = None
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate message after initialization."""
        if not self.content:
            raise ValueError("Message content is required")
        if not self.sender:
            raise ValueError("Message sender is required")

    def is_error(self) -> bool:
        """Check if this is an error message."""
        return self.type == MessageType.ERROR

    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.type == MessageType.SYSTEM

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "content": self.content,
            "sender": self.sender,
            "recipient": self.recipient,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }