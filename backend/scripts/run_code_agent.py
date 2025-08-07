#!/usr/bin/env python3
"""
Run the Code Agent as a standalone service
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.agents.code_agent import CodeAgent
from src.infrastructure.agents.agent_task_manager import task_manager
from src.infrastructure.protocols.a2a_manager import A2AManager
from src.infrastructure.persistence.context_store import ContextStore
from src.infrastructure.persistence.redis_repository import create_redis_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(code_agent: CodeAgent) -> FastAPI:
    """Create FastAPI app for the code agent"""
    app = FastAPI(
        title="Code Agent",
        description="Specialized agent for code analysis, generation, and execution",
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

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "agent": "code", "version": "1.0.0"}

    @app.get("/status")
    async def get_status():
        """Get agent status"""
        status = await code_agent.get_status()
        return status

    @app.get("/capabilities")
    async def get_capabilities():
        """Get agent capabilities"""
        capabilities = await code_agent.get_capabilities()
        return {"capabilities": capabilities}

    @app.post("/a2a/tasks")
    async def handle_a2a_task(request: dict):
        """Handle A2A task request"""
        try:
            message = request.get("message", "")
            context_id = request.get("context_id", "")
            metadata = request.get("metadata", {})

            # Generate task ID if not provided
            import uuid
            task_id = metadata.get("task_id", str(uuid.uuid4()))
            metadata["task_id"] = task_id

            # Store task in manager
            await task_manager.create_task(task_id, message, context_id, metadata)
            
            # Process task asynchronously (don't wait for completion)
            asyncio.create_task(process_task_async(task_id, message, context_id, metadata))

            return {
                "task_id": task_id,
                "status": "accepted",
                "metadata": {"agent": "code"},
            }

        except Exception as e:
            logger.error(f"Error handling A2A task: {e}")
            return {
                "status": "error",
                "error": str(e),
                "metadata": {"agent": "code"},
            }
    
    async def process_task_async(task_id: str, message: str, context_id: str, metadata: dict):
        """Process task asynchronously and update task manager"""
        try:
            # Mark as in progress
            await task_manager.start_task_processing(task_id)
            
            # Process the task
            result = await code_agent.handle_a2a_request(
                message=message,
                context_id=context_id,
                metadata=metadata
            )
            
            # Update task manager with result
            if result.get("status") == "completed":
                await task_manager.complete_task(task_id, result)
            else:
                await task_manager.fail_task(task_id, result.get("error", "Unknown error"))
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await task_manager.fail_task(task_id, str(e))

    @app.get("/a2a/tasks/{task_id}")
    async def get_task_status(task_id: str, wait: bool = False):
        """Get task status (for A2A protocol)"""
        task = await task_manager.get_task(task_id, wait=wait)
        
        if not task:
            return {
                "task_id": task_id,
                "status": "not_found",
                "error": f"Task {task_id} not found"
            }
        
        # Format response based on task status
        if task["status"] == "completed":
            return task["result"] if task["result"] else {
                "task_id": task_id,
                "status": "completed",
                "result": {},
                "metadata": {"agent": "code"}
            }
        elif task["status"] == "failed":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": task.get("error", "Task failed"),
                "metadata": {"agent": "code"}
            }
        else:
            return {
                "task_id": task_id,
                "status": task["status"],
                "metadata": {"agent": "code"}
            }

    @app.on_event("startup")
    async def startup_event():
        """Start the code agent on app startup"""
        await code_agent.start()
        logger.info("Code agent service started")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Stop the code agent on app shutdown"""
        await code_agent.stop()
        logger.info("Code agent service stopped")

    return app


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run the Code Agent")
    parser.add_argument(
        "--port", type=int, default=8002, help="Port to run the agent on"
    )
    parser.add_argument(
        "--model", type=str, default="openai:gpt-4o", help="Model to use for the agent"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis URL for context storage",
    )

    args = parser.parse_args()

    # Initialize dependencies
    logger.info("Initializing Code Agent...")

    # Create Redis connection
    redis_pool = await create_redis_pool(args.redis_url)

    # Initialize A2A manager
    a2a_manager = A2AManager(timeout=30)

    # Initialize context store
    context_store = ContextStore(redis_pool)

    # Create code agent
    code_agent = CodeAgent(
        a2a_manager=a2a_manager,
        context_store=context_store,
        model=args.model,
    )

    # Create FastAPI app
    app = create_app(code_agent)

    # Run the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=args.port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    logger.info(f"Starting Code Agent on port {args.port}...")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())