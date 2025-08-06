"""Conversation management endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from src.api.v1.dependencies import get_conversation_service, get_orchestrator_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    """Conversation creation request."""
    
    user_id: Optional[str] = None
    title: Optional[str] = None
    user_preferences: Dict[str, Any] = {}


class MessageRequest(BaseModel):
    """Message request for conversation."""
    
    message: str
    context_id: Optional[str] = None
    preferences: Dict[str, Any] = {}


@router.get("")
async def list_conversations(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    conversation_service: Any = Depends(get_conversation_service),
) -> List[Dict[str, Any]]:
    """List conversations with optional filtering."""
    conversations = await conversation_service.list_conversations(
        user_id=user_id,
        status=status,
        limit=limit,
    )
    return [
        {
            "id": str(conv.id),
            "title": conv.title,
            "status": conv.status.value,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    conversation_service: Any = Depends(get_conversation_service),
) -> Dict[str, Any]:
    """Get conversation details."""
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return {
        "id": str(conversation.id),
        "user_id": conversation.user_id,
        "status": conversation.status.value,
        "title": conversation.title,
        "current_task": conversation.current_task,
        "task_ids": [str(tid) for tid in conversation.task_ids],
        "message_ids": [str(mid) for mid in conversation.message_ids],
        "agent_outputs": conversation.agent_outputs,
        "user_preferences": conversation.user_preferences,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.post("")
async def create_conversation(
    data: ConversationCreate,
    conversation_service: Any = Depends(get_conversation_service),
) -> Dict[str, Any]:
    """Create a new conversation."""
    conversation = await conversation_service.create_conversation(
        user_id=data.user_id,
        title=data.title,
        user_preferences=data.user_preferences,
    )
    return {
        "id": str(conversation.id),
        "status": conversation.status.value,
    }


@router.post("/run")
async def run_conversation(
    request: Request,
    data: MessageRequest,
    orchestrator_service: Any = Depends(get_orchestrator_service),
) -> StreamingResponse:
    """Run a conversation with SSE streaming."""
    
    async def event_generator():
        """Generate SSE events from orchestrator."""
        try:
            async for event in orchestrator_service.process_user_request(
                message=data.message,
                conversation_id=data.context_id,
                user_preferences=data.preferences,
            ):
                import json
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            import json
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/{conversation_id}")
async def archive_conversation(
    conversation_id: UUID,
    conversation_service: Any = Depends(get_conversation_service),
) -> Dict[str, Any]:
    """Archive a conversation."""
    success = await conversation_service.archive_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return {"id": str(conversation_id), "status": "archived"}