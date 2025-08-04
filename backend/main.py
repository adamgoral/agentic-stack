"""
Main application entry point for the Agentic Stack MVP
Integrates AG-UI, A2A, and MCP protocols
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from dotenv import load_dotenv

from agents.orchestrator import OrchestratorAgent
from protocols.ag_ui_handler import setup_ag_ui_routes
from protocols.a2a_manager import A2AManager
from models.state import ConversationState
from storage.context_store import ContextStore
from monitoring import setup_monitoring

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Agentic Stack MVP...")
    
    # Initialize monitoring
    setup_monitoring()
    
    # Initialize storage
    app.state.context_store = ContextStore()
    await app.state.context_store.initialize()
    
    # Initialize A2A manager
    app.state.a2a_manager = A2AManager()
    
    # Initialize orchestrator agent
    app.state.orchestrator = OrchestratorAgent(
        a2a_manager=app.state.a2a_manager,
        context_store=app.state.context_store
    )
    
    # Start orchestrator
    await app.state.orchestrator.start()
    
    logger.info("Agentic Stack MVP started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Agentic Stack MVP...")
    await app.state.orchestrator.stop()
    await app.state.context_store.close()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Agentic Stack MVP",
    description="Multi-agent system with AG-UI, A2A, and MCP protocols",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Agentic Stack MVP",
        "status": "running",
        "protocols": {
            "ag_ui": "enabled",
            "a2a": "enabled",
            "mcp": "enabled"
        }
    }


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    orchestrator = request.app.state.orchestrator
    return {
        "status": "healthy",
        "orchestrator": orchestrator.is_running,
        "connected_agents": await orchestrator.get_connected_agents(),
        "mcp_servers": await orchestrator.get_mcp_servers()
    }


# Setup AG-UI routes for frontend communication
@app.post("/ag-ui/run")
async def run_agent_ag_ui(request: Request):
    """Handle AG-UI requests with SSE streaming"""
    orchestrator = request.app.state.orchestrator
    data = await request.json()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from agent execution"""
        try:
            # Create or retrieve conversation state
            state = ConversationState(
                context_id=data.get("context_id"),
                user_preferences=data.get("preferences", {}),
                current_task=data.get("message"),
                task_history=[],
                agent_outputs={}
            )
            
            # Run agent with AG-UI protocol
            async for event in orchestrator.run_ag_ui(
                message=data["message"],
                state=state
            ):
                yield f"data: {event}\n\n"
                
        except Exception as e:
            logger.error(f"Error in AG-UI execution: {e}")
            yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Mount A2A server
@app.on_event("startup")
async def mount_a2a():
    """Mount A2A server for agent-to-agent communication"""
    orchestrator = app.state.orchestrator
    a2a_app = orchestrator.to_a2a()
    app.mount("/a2a", a2a_app)
    logger.info("A2A server mounted at /a2a")


# API endpoints for task management
@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str, request: Request):
    """Get task status and results"""
    context_store = request.app.state.context_store
    task = await context_store.get_task(task_id)
    if not task:
        return {"error": "Task not found"}, 404
    return task


@app.get("/contexts/{context_id}")
async def get_context(context_id: str, request: Request):
    """Get conversation context"""
    context_store = request.app.state.context_store
    context = await context_store.get_context(context_id)
    if not context:
        return {"error": "Context not found"}, 404
    return context


@app.get("/agents")
async def list_agents(request: Request):
    """List all available agents and their status"""
    orchestrator = request.app.state.orchestrator
    return await orchestrator.get_agent_status()


@app.get("/mcp/servers")
async def list_mcp_servers(request: Request):
    """List all connected MCP servers"""
    orchestrator = request.app.state.orchestrator
    return await orchestrator.get_mcp_servers()


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENV", "development") == "development"
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )