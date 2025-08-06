"""API dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Request

from src.application.services import (
    AgentService,
    ConversationService,
    OrchestratorService,
    TaskService,
)


async def get_orchestrator_service(request: Request) -> OrchestratorService:
    """Get orchestrator service from app state."""
    return request.app.state.orchestrator_service


async def get_agent_service(request: Request) -> AgentService:
    """Get agent service from app state."""
    return request.app.state.agent_service


async def get_task_service(request: Request) -> TaskService:
    """Get task service from app state."""
    return request.app.state.task_service


async def get_conversation_service(request: Request) -> ConversationService:
    """Get conversation service from app state."""
    return request.app.state.conversation_service