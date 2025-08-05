#!/usr/bin/env python3
"""
Test script for the Analytics Agent
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.analytics_agent import AnalyticsAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore
from storage.redis_config import create_redis_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_analytics_agent():
    """Test the analytics agent functionality"""
    
    # Create mock dependencies
    redis_pool = await create_redis_pool("redis://localhost:6379")
    a2a_manager = A2AManager(timeout=30)
    context_store = ContextStore(redis_pool)
    
    # Create analytics agent
    agent = AnalyticsAgent(
        a2a_manager=a2a_manager,
        context_store=context_store,
        model="openai:gpt-4o"
    )
    
    # Start the agent
    await agent.start()
    
    # Test capabilities
    capabilities = await agent.get_capabilities()
    logger.info(f"Agent capabilities: {capabilities}")
    
    # Test status
    status = await agent.get_status()
    logger.info(f"Agent status: {status}")
    
    # Test processing an analytics task
    test_tasks = [
        "Analyze the following sales data: January: 100, February: 120, March: 110, April: 140, May: 160. Identify trends and provide insights.",
        "Calculate the average, median, and standard deviation for these values: 23, 45, 67, 89, 12, 34, 56, 78, 90",
        "Compare the performance metrics between Q1 (revenue: 500k, costs: 300k) and Q2 (revenue: 650k, costs: 400k). Provide recommendations.",
    ]
    
    for task in test_tasks:
        logger.info(f"\nTesting task: {task[:50]}...")
        try:
            result = await agent.process_analytics_task(
                task=task,
                context_id="test-context-001",
                metadata={"task_id": f"test-{hash(task)}"}
            )
            
            logger.info("Task completed successfully!")
            logger.info(f"Insights found: {len(result.get('insights', []))}")
            logger.info(f"Metrics calculated: {result.get('metrics', {}).keys()}")
            logger.info(f"Visualizations suggested: {len(result.get('visualizations', []))}")
            logger.info(f"Recommendations: {len(result.get('recommendations', []))}")
            
        except Exception as e:
            logger.error(f"Task failed: {e}")
    
    # Test A2A request handling
    logger.info("\nTesting A2A request handling...")
    a2a_result = await agent.handle_a2a_request(
        message="Analyze customer satisfaction scores: 4.5, 4.2, 4.8, 3.9, 4.6",
        context_id="test-context-002",
        metadata={"source": "test", "task_id": "a2a-test-001"}
    )
    logger.info(f"A2A request status: {a2a_result.get('status')}")
    
    # Stop the agent
    await agent.stop()
    
    # Close Redis connection
    redis_pool.close()
    await redis_pool.wait_closed()
    
    logger.info("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(test_analytics_agent())