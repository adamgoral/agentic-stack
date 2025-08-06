"""Conversation-related domain exceptions."""


class ConversationError(Exception):
    """Base exception for conversation-related errors."""


class ConversationNotFoundError(ConversationError):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"Conversation with ID {conversation_id} not found")
        self.conversation_id = conversation_id


class InvalidConversationStateError(ConversationError):
    """Raised when a conversation operation is invalid for its current state."""

    def __init__(self, conversation_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot perform {operation} on conversation {conversation_id} in state {current_state}"
        )
        self.conversation_id = conversation_id
        self.current_state = current_state
        self.operation = operation