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

from agents.code_agent import CodeAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore
from storage.redis_config import create_redis_pool
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

            # Process task asynchronously
            result = await code_agent.handle_a2a_request(
                message=message,
                context_id=context_id,
                metadata=metadata
            )

            return {
                "task_id": task_id,
                "status": result.get("status", "accepted"),
                "result": result.get("result"),
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"Error handling A2A task: {e}")
            return {
                "status": "error",
                "error": str(e),
                "metadata": {"agent": "code"},
            }

    @app.get("/a2a/tasks/{task_id}")
    async def get_task_status(task_id: str):
        """Get task status (for A2A protocol)"""
        # In a full implementation, this would retrieve task status from storage
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task status retrieval not yet implemented",
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