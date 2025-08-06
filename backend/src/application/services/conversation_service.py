"""Conversation service - manages conversation lifecycle."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.entities import Conversation, ConversationStatus
from src.domain.exceptions import ConversationNotFoundError

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations."""

    def __init__(self, conversation_repository: Any) -> None:
        """Initialize conversation service."""
        self.conversation_repository = conversation_repository

    async def create_conversation(
        self,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            user_preferences=user_preferences or {},
        )
        
        await self.conversation_repository.save(str(conversation.id), conversation)
        logger.info(f"Created conversation: {conversation.id}")
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        return await self.conversation_repository.get(str(conversation_id), Conversation)

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update a conversation."""
        await self.conversation_repository.save(str(conversation.id), conversation)
        return conversation

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Conversation]:
        """List conversations with optional filtering."""
        # Placeholder implementation
        all_conversations = []
        conversation_keys = await self.conversation_repository.list_keys("*")
        
        for key in conversation_keys[:limit]:
            conversation = await self.conversation_repository.get(key, Conversation)
            if conversation:
                if user_id and conversation.user_id != user_id:
                    continue
                if status and conversation.status.value != status:
                    continue
                all_conversations.append(conversation)
        
        return all_conversations

    async def archive_conversation(self, conversation_id: UUID) -> bool:
        """Archive a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.archive()
        await self.conversation_repository.save(str(conversation.id), conversation)
        logger.info(f"Archived conversation: {conversation.id}")
        return True

    async def add_task_to_conversation(
        self,
        conversation_id: UUID,
        task_id: UUID,
    ) -> bool:
        """Add a task to a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(str(conversation_id))
        
        conversation.add_task(task_id)
        await self.conversation_repository.save(str(conversation.id), conversation)
        return True

    async def add_message_to_conversation(
        self,
        conversation_id: UUID,
        message_id: UUID,
    ) -> bool:
        """Add a message to a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(str(conversation_id))
        
        conversation.add_message(message_id)
        await self.conversation_repository.save(str(conversation.id), conversation)
        return True