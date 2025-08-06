#!/usr/bin/env python3
"""
Test script for orchestrator result aggregation
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_orchestrator_aggregation():
    """Test the orchestrator's ability to aggregate results from multiple agents"""
    
    orchestrator_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Simple research request
        logger.info("Test 1: Research request")
        test_message = "Research the latest developments in quantum computing"
        
        response = await send_ag_ui_request(client, orchestrator_url, test_message)
        logger.info(f"Response for research: {response}")
        
        # Test 2: Code generation request
        logger.info("\nTest 2: Code generation request")
        test_message = "Generate Python code to calculate fibonacci numbers"
        
        response = await send_ag_ui_request(client, orchestrator_url, test_message)
        logger.info(f"Response for code: {response}")
        
        # Test 3: Multi-agent request
        logger.info("\nTest 3: Multi-agent request")
        test_message = "Research machine learning algorithms and generate Python code for a simple neural network"
        
        response = await send_ag_ui_request(client, orchestrator_url, test_message)
        logger.info(f"Response for multi-agent: {response}")
        
        # Test 4: Analytics request
        logger.info("\nTest 4: Analytics request")
        test_message = "Analyze the data trends in AI adoption over the last 5 years"
        
        response = await send_ag_ui_request(client, orchestrator_url, test_message)
        logger.info(f"Response for analytics: {response}")


async def send_ag_ui_request(client: httpx.AsyncClient, orchestrator_url: str, message: str):
    """Send a request to the orchestrator via AG-UI protocol"""
    
    # Prepare AG-UI request
    payload = {
        "message": message,
        "context_id": f"test-{datetime.utcnow().isoformat()}",
        "metadata": {}
    }
    
    try:
        # Send request to orchestrator's AG-UI endpoint
        logger.info(f"Sending request: {message}")
        
        response = await client.post(
            f"{orchestrator_url}/ag-ui/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Parse streaming response
            results = []
            for line in response.text.split("\n"):
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "text_message":
                            results.append(event.get("content", ""))
                        elif event.get("type") == "error":
                            logger.error(f"Error in response: {event.get('message')}")
                        logger.debug(f"Event: {event}")
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse line: {line}")
            
            return "\n".join(results) if results else "No content in response"
        else:
            logger.error(f"Request failed with status {response.status_code}: {response.text}")
            return f"Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error sending request: {e}")
        return f"Error: {str(e)}"


async def test_direct_a2a():
    """Test direct A2A communication to verify agents are responding"""
    
    agents = {
        "research": "http://localhost:8001",
        "code": "http://localhost:8002",
        "analytics": "http://localhost:8003"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for agent_name, agent_url in agents.items():
            logger.info(f"\nTesting {agent_name} agent at {agent_url}")
            
            # Check health
            try:
                health_response = await client.get(f"{agent_url}/health")
                logger.info(f"{agent_name} health: {health_response.json()}")
            except Exception as e:
                logger.error(f"{agent_name} health check failed: {e}")
            
            # Send A2A task
            try:
                task_payload = {
                    "message": f"Test task for {agent_name}",
                    "context_id": "test-context",
                    "metadata": {"test": True}
                }
                
                task_response = await client.post(
                    f"{agent_url}/a2a/tasks",
                    json=task_payload,
                    headers={"X-A2A-Version": "0.2.5"}
                )
                
                if task_response.status_code == 200:
                    result = task_response.json()
                    logger.info(f"{agent_name} A2A response: {json.dumps(result, indent=2)}")
                    
                    # If we got a task_id, try to get the result
                    task_id = result.get("task_id")
                    if task_id:
                        await asyncio.sleep(2)  # Give it time to process
                        
                        result_response = await client.get(
                            f"{agent_url}/a2a/tasks/{task_id}",
                            headers={"X-A2A-Version": "0.2.5"}
                        )
                        
                        if result_response.status_code == 200:
                            logger.info(f"{agent_name} task result: {result_response.json()}")
                else:
                    logger.error(f"{agent_name} A2A task failed: {task_response.status_code}")
                    
            except Exception as e:
                logger.error(f"{agent_name} A2A test failed: {e}")


async def main():
    """Main test function"""
    
    # First test direct A2A to ensure agents are running
    logger.info("=" * 60)
    logger.info("Testing direct A2A communication with agents")
    logger.info("=" * 60)
    await test_direct_a2a()
    
    # Then test orchestrator aggregation
    logger.info("\n" + "=" * 60)
    logger.info("Testing orchestrator result aggregation")
    logger.info("=" * 60)
    await test_orchestrator_aggregation()


if __name__ == "__main__":
    asyncio.run(main())