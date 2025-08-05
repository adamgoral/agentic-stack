#!/usr/bin/env python3
"""
Run the Analytics Agent as a standalone service
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.analytics_agent import AnalyticsAgent
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


def create_app(analytics_agent: AnalyticsAgent) -> FastAPI:
    """Create FastAPI app for the analytics agent"""
    app = FastAPI(
        title="Analytics Agent",
        description="Specialized agent for data analysis, visualization, and insights",
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
        return {"status": "healthy", "agent": "analytics", "version": "1.0.0"}

    @app.get("/status")
    async def get_status():
        """Get agent status"""
        status = await analytics_agent.get_status()
        return status

    @app.get("/capabilities")
    async def get_capabilities():
        """Get agent capabilities"""
        capabilities = await analytics_agent.get_capabilities()
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
            result = await analytics_agent.handle_a2a_request(
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
                "metadata": {"agent": "analytics"},
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
        """Start the analytics agent on app startup"""
        await analytics_agent.start()
        logger.info("Analytics agent service started")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Stop the analytics agent on app shutdown"""
        await analytics_agent.stop()
        logger.info("Analytics agent service stopped")

    return app


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run the Analytics Agent")
    parser.add_argument(
        "--port", type=int, default=8003, help="Port to run the agent on"
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
    logger.info("Initializing Analytics Agent...")

    # Create Redis connection
    redis_pool = await create_redis_pool(args.redis_url)

    # Initialize A2A manager
    a2a_manager = A2AManager(timeout=30)

    # Initialize context store
    context_store = ContextStore(redis_pool)

    # Create analytics agent
    analytics_agent = AnalyticsAgent(
        a2a_manager=a2a_manager,
        context_store=context_store,
        model=args.model,
    )

    # Create FastAPI app
    app = create_app(analytics_agent)

    # Run the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=args.port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    logger.info(f"Starting Analytics Agent on port {args.port}...")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())