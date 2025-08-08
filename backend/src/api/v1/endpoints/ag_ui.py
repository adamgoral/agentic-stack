"""AG-UI Protocol endpoint for CopilotKit integration."""

import json
import logging
from typing import AsyncIterator, Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.application.services import OrchestratorService
from src.domain.entities import Message, MessageType, Conversation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AG-UI"])


class AGUIMessage(BaseModel):
    """AG-UI protocol message."""
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class AGUIRequest(BaseModel):
    """AG-UI protocol request."""
    messages: List[AGUIMessage]
    context_id: Optional[str] = None
    stream: bool = True


async def format_sse_event(event_type: str, data: Any) -> str:
    """Format data as Server-Sent Event."""
    if isinstance(data, dict):
        data_str = json.dumps(data)
    else:
        data_str = str(data)
    
    return f"event: {event_type}\ndata: {data_str}\n\n"


async def stream_ag_ui_response(
    orchestrator: OrchestratorService,
    messages: List[Message],
    context_id: str
) -> AsyncIterator[str]:
    """Stream AG-UI protocol responses."""
    try:
        # Send initial state
        yield await format_sse_event("state", {
            "type": "state_update",
            "state": "thinking",
            "details": "Processing your request..."
        })
        
        # Process with orchestrator
        result = await orchestrator.process_request(
            messages=messages,
            context_id=context_id
        )
        
        # Send result
        yield await format_sse_event("message", {
            "type": "assistant",
            "content": result.get("response", "I processed your request but couldn't generate a response."),
            "metadata": {
                "agents_used": result.get("agents_used", []),
                "processing_time": result.get("processing_time", 0)
            }
        })
        
        # Send completion state
        yield await format_sse_event("state", {
            "type": "state_update",
            "state": "complete",
            "details": "Request processed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in AG-UI stream: {e}")
        yield await format_sse_event("error", {
            "type": "error",
            "message": str(e)
        })


@router.post("/ag-ui")
async def handle_ag_ui_request(
    request: Request,
    ag_ui_request: AGUIRequest
) -> StreamingResponse:
    """
    Handle AG-UI protocol requests from CopilotKit.
    
    This endpoint processes messages from the frontend through the AG-UI protocol,
    delegates to appropriate agents, and streams responses back.
    """
    try:
        # Get orchestrator service from app state
        orchestrator: OrchestratorService = request.app.state.orchestrator_service
        
        # Convert AG-UI messages to domain messages
        messages = []
        for msg in ag_ui_request.messages:
            # Map role to MessageType
            if msg.role == "user":
                msg_type = MessageType.USER_INPUT
                sender = "user"
            elif msg.role == "assistant":
                msg_type = MessageType.AGENT_OUTPUT
                sender = "assistant"
            else:
                msg_type = MessageType.SYSTEM
                sender = msg.role
            
            messages.append(
                Message(
                    type=msg_type,
                    content=msg.content,
                    sender=sender,
                    metadata=msg.metadata or {}
                )
            )
        
        # Generate context ID if not provided
        context_id = ag_ui_request.context_id or f"ag-ui-{id(ag_ui_request)}"
        
        # Stream response
        return StreamingResponse(
            stream_ag_ui_response(orchestrator, messages, context_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Error handling AG-UI request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ag-ui/health")
async def ag_ui_health():
    """Health check for AG-UI endpoint."""
    return {
        "status": "healthy",
        "protocol": "AG-UI",
        "version": "1.0.0"
    }


@router.get("/ag-ui/info")
async def ag_ui_info():
    """
    Provide agent information for CopilotKit discovery.
    This endpoint tells CopilotKit what agents and actions are available.
    """
    return {
        "version": "1.0.0",
        "agents": [
            {
                "name": "orchestrator",
                "description": "Multi-agent orchestrator that coordinates research, code, and analytics agents",
                "capabilities": [
                    "research",
                    "code_generation",
                    "code_analysis",
                    "data_analysis",
                    "web_search"
                ]
            }
        ],
        "actions": [
            {
                "name": "process_request",
                "description": "Process a user request by delegating to appropriate agents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The user's request or question"
                        }
                    },
                    "required": ["message"]
                }
            }
        ]
    }