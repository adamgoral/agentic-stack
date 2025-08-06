#!/usr/bin/env python3
"""
Test script to verify MCP server integration with research agent
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research_agent import ResearchAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_mcp_server_direct():
    """Test direct connection to MCP server"""
    logger.info("Testing direct MCP server connection...")
    
    # Determine URL based on environment
    is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
    base_url = "http://mcp-web-search:3001" if is_docker else "http://localhost:3001"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test health endpoint
        try:
            logger.info(f"Testing health endpoint at {base_url}/health")
            response = await client.get(f"{base_url}/health")
            response.raise_for_status()
            logger.info(f"Health check successful: {response.json()}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Try fallback
            fallback_url = "http://localhost:3001" if is_docker else "http://mcp-web-search:3001"
            try:
                logger.info(f"Trying fallback URL: {fallback_url}/health")
                response = await client.get(f"{fallback_url}/health")
                response.raise_for_status()
                logger.info(f"Fallback health check successful: {response.json()}")
                base_url = fallback_url
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                return False
        
        # Test search_web tool
        try:
            logger.info("Testing search_web tool...")
            url = f"{base_url}/tools/search_web"
            payload = {
                "query": "artificial intelligence latest developments",
                "max_results": 3,
                "search_type": "general"
            }
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                search_results = result.get("result", {})
                logger.info(f"Search successful! Found {len(search_results.get('results', []))} results")
                
                # Display results
                for i, res in enumerate(search_results.get("results", []), 1):
                    logger.info(f"  Result {i}: {res.get('title', 'No title')}")
                    logger.info(f"    URL: {res.get('url', 'No URL')}")
                    logger.info(f"    Snippet: {res.get('snippet', 'No snippet')[:100]}...")
                
                return True
            else:
                logger.error(f"Search failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing search_web tool: {e}")
            return False


async def test_research_agent_mcp():
    """Test research agent with MCP integration"""
    logger.info("Testing Research Agent MCP integration...")
    
    # Initialize components
    a2a_manager = A2AManager()
    context_store = ContextStore()
    
    # Create research agent
    agent = ResearchAgent(a2a_manager, context_store)
    
    try:
        # Start the agent
        await agent.start()
        
        # Test execute_research method directly
        logger.info("Testing execute_research method...")
        query = "What are the latest advancements in quantum computing?"
        
        results = await agent.execute_research(query, max_results=3)
        
        if results.get("success"):
            logger.info("Research execution successful!")
            logger.info(f"Query: {results.get('query')}")
            logger.info(f"Results count: {len(results.get('results', []))}")
            
            for i, result in enumerate(results.get('results', []), 1):
                logger.info(f"\nResult {i}:")
                logger.info(f"  Title: {result.get('title', 'N/A')}")
                logger.info(f"  URL: {result.get('url', 'N/A')}")
                logger.info(f"  Source: {result.get('source', 'N/A')}")
                logger.info(f"  Snippet: {result.get('snippet', 'N/A')[:150]}...")
        else:
            logger.error(f"Research execution failed: {results.get('error')}")
        
        # Test full research task processing
        logger.info("\nTesting full research task processing...")
        task_results = await agent.process_research_task(
            task="Research the impact of AI on healthcare in 2024",
            context_id="test-context-001",
            metadata={"task_id": "test-task-001"}
        )
        
        logger.info("Research task completed!")
        logger.info(f"Task ID: {task_results.get('task_id')}")
        logger.info(f"Confidence: {task_results.get('confidence')}")
        logger.info(f"Sources found: {len(task_results.get('sources', []))}")
        logger.info(f"MCP Success: {task_results.get('mcp_success', False)}")
        
        # Display findings preview
        findings = task_results.get('findings', '')
        logger.info(f"\nFindings preview (first 500 chars):")
        logger.info(findings[:500])
        
    except Exception as e:
        logger.error(f"Error during research agent test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the agent
        await agent.stop()
        await context_store.close()


async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("MCP Integration Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Direct MCP server connection
    logger.info("\n[Test 1] Direct MCP Server Connection")
    logger.info("-" * 40)
    mcp_success = await test_mcp_server_direct()
    
    if mcp_success:
        logger.info("✓ Direct MCP server test passed")
    else:
        logger.warning("✗ Direct MCP server test failed - server may not be running")
    
    # Test 2: Research Agent MCP integration
    logger.info("\n[Test 2] Research Agent MCP Integration")
    logger.info("-" * 40)
    await test_research_agent_mcp()
    
    logger.info("\n" + "=" * 60)
    logger.info("Test suite completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())