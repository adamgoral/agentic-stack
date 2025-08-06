"""
Test script for Research Agent
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research_agent import ResearchAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore
from storage.redis_config import create_redis_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_research_agent():
    """Test the research agent functionality"""
    logger.info("Starting Research Agent test...")

    # Initialize dependencies
    redis_pool = await create_redis_pool("redis://localhost:6379")
    a2a_manager = A2AManager(timeout=30)
    context_store = ContextStore(redis_pool)

    # Create research agent
    research_agent = ResearchAgent(
        a2a_manager=a2a_manager,
        context_store=context_store,
        model="openai:gpt-4o-mini",  # Use mini for testing
    )

    try:
        # Start the agent
        await research_agent.start()
        logger.info("Research agent started successfully")

        # Test 1: Process a simple research task
        logger.info("\n=== Test 1: Simple Research Task ===")
        result = await research_agent.process_research_task(
            task="What are the latest developments in quantum computing?",
            context_id="test-context-001",
            metadata={"task_id": "test-task-001"}
        )
        logger.info(f"Research result: {result}")

        # Test 2: Handle A2A request
        logger.info("\n=== Test 2: A2A Request Handling ===")
        a2a_result = await research_agent.handle_a2a_request(
            message="Research the benefits of microservices architecture",
            context_id="test-context-002",
            metadata={"task_id": "test-task-002", "source": "orchestrator"}
        )
        logger.info(f"A2A result: {a2a_result}")

        # Test 3: Get agent status
        logger.info("\n=== Test 3: Agent Status ===")
        status = await research_agent.get_status()
        logger.info(f"Agent status: {status}")

        # Test 4: Get capabilities
        logger.info("\n=== Test 4: Agent Capabilities ===")
        capabilities = await research_agent.get_capabilities()
        logger.info(f"Agent capabilities: {capabilities}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

    finally:
        # Stop the agent
        await research_agent.stop()
        await a2a_manager.close()
        await redis_pool.close()
        logger.info("Research agent test completed")


if __name__ == "__main__":
    asyncio.run(test_research_agent())