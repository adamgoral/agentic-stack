"""Main application entry point with clean architecture."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.endpoints import (
    agents_router,
    conversations_router,
    health_router,
    tasks_router,
)
from src.core import Settings, get_settings, setup_logging, setup_monitoring
from src.infrastructure.persistence import RedisRepository
from src.application.services import (
    AgentService,
    TaskService,
    ConversationService,
    OrchestratorService,
)

logger = logging.getLogger(__name__)


def create_application(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        """Application lifespan manager."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        
        # Setup monitoring
        if settings.telemetry_enabled:
            setup_monitoring()
        
        # Initialize persistence
        redis_repo = RedisRepository(settings.redis_url)
        await redis_repo.connect()
        app.state.redis_repo = redis_repo
        
        # Initialize services with repositories
        app.state.agent_service = AgentService(agent_repository=redis_repo)
        app.state.task_service = TaskService(task_repository=redis_repo)
        app.state.conversation_service = ConversationService(conversation_repository=redis_repo)
        app.state.orchestrator_service = OrchestratorService(
            agent_service=app.state.agent_service,
            task_service=app.state.task_service,
            conversation_service=app.state.conversation_service,
        )
        
        logger.info("Application startup complete")
        
        yield
        
        # Cleanup
        logger.info("Shutting down application...")
        await redis_repo.disconnect()
        logger.info("Shutdown complete")
    
    app = FastAPI(
        title=settings.app_name,
        description="Multi-agent orchestration system with clean architecture",
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    api_v1_prefix = f"{settings.api_prefix}{settings.api_v1_prefix}"
    app.include_router(health_router, prefix=api_v1_prefix)
    app.include_router(agents_router, prefix=api_v1_prefix)
    app.include_router(tasks_router, prefix=api_v1_prefix)
    app.include_router(conversations_router, prefix=api_v1_prefix)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "api_docs": f"/docs" if not settings.is_production else None,
        }
    
    return app


# Create application instance
settings = get_settings()
setup_logging(settings.log_level)
app = create_application(settings)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )