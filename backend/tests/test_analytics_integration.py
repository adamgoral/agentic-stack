#!/usr/bin/env python3
"""
Integration test for Analytics Agent with Orchestrator
"""

import asyncio
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_analytics_integration():
    """Test analytics agent integration via HTTP"""
    import aiohttp
    
    analytics_agent_url = "http://localhost:8003"
    
    # Test health check
    async with aiohttp.ClientSession() as session:
        try:
            # Health check
            async with session.get(f"{analytics_agent_url}/health") as resp:
                if resp.status == 200:
                    health = await resp.json()
                    logger.info(f"Analytics Agent Health: {health}")
                else:
                    logger.error(f"Health check failed: {resp.status}")
                    return
            
            # Get capabilities
            async with session.get(f"{analytics_agent_url}/capabilities") as resp:
                if resp.status == 200:
                    capabilities = await resp.json()
                    logger.info(f"Analytics Agent Capabilities: {capabilities}")
            
            # Test A2A task submission
            test_task = {
                "message": "Analyze the monthly revenue data: Jan: 45000, Feb: 52000, Mar: 48000, Apr: 61000, May: 58000, Jun: 63000. Calculate growth rate, identify trends, and suggest visualizations.",
                "context_id": f"test-integration-{datetime.now().isoformat()}",
                "metadata": {
                    "task_id": "analytics-test-001",
                    "source": "integration_test",
                    "data": {
                        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                        "revenue": [45000, 52000, 48000, 61000, 58000, 63000]
                    }
                }
            }
            
            logger.info("\nSubmitting analytics task via A2A...")
            async with session.post(
                f"{analytics_agent_url}/a2a/tasks",
                json=test_task
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"Task submitted successfully!")
                    logger.info(f"Task ID: {result.get('task_id')}")
                    logger.info(f"Status: {result.get('status')}")
                    
                    if result.get('result'):
                        analysis = result['result']
                        logger.info(f"\nAnalysis Results:")
                        logger.info(f"- Insights: {len(analysis.get('insights', []))} insights found")
                        logger.info(f"- Metrics: {analysis.get('metrics', {})}")
                        logger.info(f"- Visualizations: {len(analysis.get('visualizations', []))} suggested")
                        logger.info(f"- Recommendations: {len(analysis.get('recommendations', []))} provided")
                        
                        # Display some insights
                        if analysis.get('insights'):
                            logger.info("\nTop Insights:")
                            for i, insight in enumerate(analysis['insights'][:3], 1):
                                logger.info(f"  {i}. {insight}")
                        
                        # Display visualizations
                        if analysis.get('visualizations'):
                            logger.info("\nSuggested Visualizations:")
                            for viz in analysis['visualizations']:
                                logger.info(f"  - {viz.get('type', 'Unknown')}: {viz.get('description', '')}")
                else:
                    logger.error(f"Task submission failed: {resp.status}")
                    error_text = await resp.text()
                    logger.error(f"Error: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            logger.info("Make sure the analytics agent is running on port 8003")
            logger.info("You can start it with: python -m agents.analytics_agent --port 8003")


if __name__ == "__main__":
    logger.info("Testing Analytics Agent Integration...")
    logger.info("="*50)
    asyncio.run(test_analytics_integration())