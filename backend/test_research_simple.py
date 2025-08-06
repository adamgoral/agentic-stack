#!/usr/bin/env python3
"""
Simple test script for Research Agent MCP integration
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.research_agent import ResearchAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Test research agent with actual MCP calls"""
    logger.info("=" * 70)
    logger.info("Research Agent MCP Integration Test")
    logger.info("=" * 70)
    
    # Initialize components
    a2a_manager = A2AManager()
    context_store = ContextStore()
    
    # Create research agent
    agent = ResearchAgent(a2a_manager, context_store)
    
    try:
        # Start the agent
        await agent.start()
        logger.info("✓ Research agent started")
        
        # Test queries
        queries = [
            "What are the latest AI developments in 2024?",
            "How does quantum computing work?",
            "Best practices for Python FastAPI development"
        ]
        
        for i, query in enumerate(queries, 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"Query {i}: {query}")
            logger.info("="*70)
            
            # Execute research
            result = await agent.process_research_task(
                task=query,
                context_id=f"test-{i:03d}",
                metadata={"test": True}
            )
            
            # Display results
            logger.info(f"\n📊 Results:")
            logger.info(f"  • Task ID: {result.get('task_id')}")
            logger.info(f"  • Confidence: {result.get('confidence')}")
            logger.info(f"  • MCP Success: {result.get('mcp_success', False)}")
            logger.info(f"  • Sources: {len(result.get('sources', []))}")
            
            # Show first part of findings
            findings = result.get('findings', '')
            if findings:
                lines = findings.split('\n')[:15]
                logger.info("\n📝 Findings Preview:")
                for line in lines:
                    if line.strip():
                        logger.info(f"  {line[:100]}")
            
            await asyncio.sleep(1)
        
        logger.info("\n" + "="*70)
        logger.info("✓ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await agent.stop()
        await context_store.close()
        logger.info("Agent stopped and resources cleaned up")


if __name__ == "__main__":
    asyncio.run(main())