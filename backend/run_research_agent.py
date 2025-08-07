#!/usr/bin/env python3
"""
Run the Research Agent as a standalone service
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.agents.research_agent import ResearchAgent
from src.infrastructure.persistence.redis_repository import RedisRepository
from src.infrastructure.persistence.context_store import ContextStore
from src.infrastructure.protocols.a2a_manager import A2AManager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TaskRequest(BaseModel):
    task_id: str
    prompt: str
    context: dict = {}


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: dict = {}
    error: str = None


def create_app() -> FastAPI:
    """Create FastAPI app for the research agent"""
    app = FastAPI(
        title="Research Agent",
        description="Specialized agent for web research and information gathering",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize components
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_repo = RedisRepository(redis_url, prefix="research_agent")
    context_store = ContextStore(redis_url)
    a2a_manager = A2AManager(redis_url)
    research_agent = ResearchAgent(a2a_manager, context_store)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "agent": "research"}

    @app.post("/execute", response_model=TaskResponse)
    async def execute_task(request: TaskRequest):
        """Execute a research task"""
        try:
            logger.info(f"Executing task {request.task_id}: {request.prompt}")
            
            # Execute the research task
            result = await research_agent.execute(
                request.prompt,
                context=request.context
            )
            
            # Store result in Redis
            await redis_repo.set(f"task:{request.task_id}", {
                "status": "completed",
                "result": result
            })
            
            return TaskResponse(
                task_id=request.task_id,
                status="completed",
                result=result
            )
        except Exception as e:
            logger.error(f"Error executing task {request.task_id}: {e}")
            
            # Store error in Redis
            await redis_repo.set(f"task:{request.task_id}", {
                "status": "failed",
                "error": str(e)
            })
            
            return TaskResponse(
                task_id=request.task_id,
                status="failed",
                error=str(e)
            )

    @app.get("/status/{task_id}", response_model=TaskResponse)
    async def get_status(task_id: str):
        """Get task status"""
        result = await redis_repo.get(f"task:{task_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            task_id=task_id,
            status=result.get("status", "unknown"),
            result=result.get("result", {}),
            error=result.get("error")
        )

    return app


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Research Agent")
    parser.add_argument("--port", type=int, default=8001, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    logger.info(f"Starting Research Agent on {args.host}:{args.port}")
    
    app = create_app()
    
    config = uvicorn.Config(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())