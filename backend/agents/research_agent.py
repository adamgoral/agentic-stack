"""
Research Agent - Specialized agent for web research and information gathering
Handles research tasks via A2A, delegates to web search MCP server
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncio

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.ag_ui import StateDeps

from models.state import ConversationState, AgentTaskState
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Research agent specialized in web search and information gathering
    """

    def __init__(
        self, a2a_manager: A2AManager, context_store: ContextStore, model: str = "openai:gpt-4o"
    ):
        self.a2a_manager = a2a_manager
        self.context_store = context_store
        self.is_running = False

        # Initialize MCP connection to web search server
        self.mcp_servers = self._initialize_mcp_servers()

        # Create the PydanticAI agent with research-specific instructions
        self.agent = Agent(
            model,
            instructions="""You are a specialized research agent with expertise in:
            1. Web search and information retrieval
            2. Fact-checking and verification
            3. Summarizing and synthesizing information from multiple sources
            4. Academic and technical research
            5. Market research and competitive analysis
            
            Your capabilities include:
            - Conducting comprehensive web searches
            - Finding authoritative sources
            - Cross-referencing information
            - Identifying trends and patterns
            - Creating research summaries and reports
            
            When handling research tasks:
            1. Break down complex queries into specific search terms
            2. Search for information from multiple perspectives
            3. Prioritize authoritative and recent sources
            4. Verify facts when possible
            5. Synthesize findings into clear, actionable insights
            
            Always provide:
            - Source citations for important claims
            - Confidence levels for findings
            - Alternative viewpoints when relevant
            - Clear summaries of complex information""",
            toolsets=list(self.mcp_servers.values()),
        )

        # Store agent metadata
        self.agent_name = "research"
        self.agent_version = "1.0.0"

    def _initialize_mcp_servers(self) -> Dict[str, Any]:
        """Initialize MCP server connections"""
        servers = {}

        # Determine if we're running in Docker
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
        
        # Connect to web search server using SSE
        web_search_url = "http://mcp-web-search:3001/sse" if is_docker else "http://localhost:3001/sse"
        
        try:
            servers["web_search"] = MCPServerSSE(
                url=web_search_url, 
                prefix="search_"
            )
            logger.info(f"Connected to web search MCP server at {web_search_url}")
        except Exception as e:
            logger.error(f"Failed to connect to web search server at {web_search_url}: {e}")
            # Try alternative URL if first attempt fails
            alt_url = "http://localhost:3001/sse" if is_docker else "http://mcp-web-search:3001/sse"
            try:
                servers["web_search"] = MCPServerSSE(
                    url=alt_url, 
                    prefix="search_"
                )
                logger.info(f"Connected to web search MCP server at {alt_url} (fallback)")
            except Exception as e2:
                logger.error(f"Failed to connect to web search server at {alt_url}: {e2}")

        return servers

    async def start(self):
        """Start the research agent"""
        self.is_running = True
        logger.info("Research agent started")

        # Connect to MCP servers
        for name, server in self.mcp_servers.items():
            try:
                await server.__aenter__()
                logger.info(f"Connected to MCP server: {name}")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {name}: {e}")

    async def stop(self):
        """Stop the research agent"""
        self.is_running = False

        # Disconnect from MCP servers
        for name, server in self.mcp_servers.items():
            try:
                await server.__aexit__(None, None, None)
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server {name}: {e}")

        logger.info("Research agent stopped")

    async def process_research_task(
        self, task: str, context_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a research task
        
        Args:
            task: The research task to perform
            context_id: Context ID for the conversation
            metadata: Optional metadata about the task
            
        Returns:
            Research results including sources and summaries
        """
        try:
            logger.info(f"Processing research task: {task[:100]}...")

            # Create task state
            task_state = AgentTaskState(
                task_id=metadata.get("task_id") if metadata else None,
                agent_name=self.agent_name,
                status="in_progress",
                input_data={"task": task, "metadata": metadata},
                output_data=None,
                error=None,
            )
            task_state.start()

            # Run the research task
            async with self.agent as agent:
                # Enhance the prompt with research-specific guidance
                research_prompt = f"""
                Research Task: {task}
                
                Please conduct thorough research on this topic. Use web search to:
                1. Find authoritative and recent sources
                2. Gather multiple perspectives
                3. Verify key facts
                4. Identify trends or patterns
                
                Provide a comprehensive response that includes:
                - Key findings with source citations
                - Summary of important points
                - Any conflicting information or debates
                - Recommendations or insights based on the research
                """

                # Execute the research
                response = await agent.run(research_prompt)

                # Process and structure the results
                results = {
                    "findings": str(response),
                    "sources": self._extract_sources(str(response)),
                    "confidence": self._assess_confidence(str(response)),
                    "timestamp": datetime.utcnow().isoformat(),
                    "task_id": task_state.task_id,
                    "agent": self.agent_name,
                }

                # Update task state
                task_state.complete(results)
                await self.context_store.store_task(task_state)

                logger.info(f"Research task completed: {task_state.task_id}")
                return results

        except Exception as e:
            logger.error(f"Error processing research task: {e}")
            if 'task_state' in locals():
                task_state.fail(str(e))
                await self.context_store.store_task(task_state)
            raise

    def _extract_sources(self, response: str) -> List[str]:
        """Extract source citations from the response"""
        # This is a simplified implementation
        # In production, you'd use more sophisticated parsing
        sources = []
        
        # Look for URLs in the response
        import re
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(response)
        sources.extend(urls)

        # Look for citations in common formats
        citation_pattern = re.compile(r'\[([^\]]+)\]')
        citations = citation_pattern.findall(response)
        sources.extend(citations)

        return list(set(sources))  # Remove duplicates

    def _assess_confidence(self, response: str) -> str:
        """Assess confidence level based on the response"""
        # Simplified confidence assessment
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["verified", "confirmed", "certain", "definitely"]):
            return "high"
        elif any(word in response_lower for word in ["likely", "probably", "appears", "seems"]):
            return "medium"
        elif any(word in response_lower for word in ["uncertain", "unclear", "disputed", "conflicting"]):
            return "low"
        else:
            return "medium"

    async def handle_a2a_request(
        self, message: str, context_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an A2A request from another agent
        
        Args:
            message: The task message
            context_id: Context ID for the conversation
            metadata: Optional metadata
            
        Returns:
            Task result for A2A response
        """
        try:
            # Process the research task
            results = await self.process_research_task(message, context_id, metadata)

            # Format for A2A response
            return {
                "status": "completed",
                "result": results,
                "artifacts": {
                    "sources": results.get("sources", []),
                    "confidence": results.get("confidence", "medium"),
                },
                "metadata": {
                    "agent": self.agent_name,
                    "version": self.agent_version,
                    "model": self.agent.model,
                },
            }

        except Exception as e:
            logger.error(f"Error handling A2A request: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "metadata": {
                    "agent": self.agent_name,
                    "version": self.agent_version,
                },
            }

    async def run_ag_ui(self, message: str, state: ConversationState) -> AsyncGenerator[str, None]:
        """
        Process a request and stream AG-UI events
        For direct frontend communication (if needed)
        """
        try:
            # Start event
            yield json.dumps(
                {
                    "type": "start",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": state.context_id,
                    "agent": self.agent_name,
                }
            )

            # Status update
            yield json.dumps(
                {"type": "status", "message": "Starting research..."}
            )

            # Process the research task
            results = await self.process_research_task(message, state.context_id)

            # Stream the results
            yield json.dumps({
                "type": "text_message",
                "content": results["findings"],
                "metadata": {
                    "sources": results.get("sources", []),
                    "confidence": results.get("confidence", "medium"),
                }
            })

            # Complete event
            yield json.dumps({
                "type": "complete",
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in AG-UI execution: {e}")
            yield json.dumps({"type": "error", "message": str(e)})

    def to_a2a(self):
        """Convert to A2A server for agent-to-agent communication"""
        return self.agent.to_a2a()

    def to_ag_ui(self):
        """Convert to AG-UI server for frontend communication"""
        return self.agent.to_ag_ui()

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent": self.agent_name,
            "version": self.agent_version,
            "status": "running" if self.is_running else "stopped",
            "model": self.agent.model,
            "mcp_servers": {
                name: hasattr(server, "_client") and server._client is not None
                for name, server in self.mcp_servers.items()
            },
        }

    async def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        return [
            "web_search",
            "fact_checking",
            "source_verification",
            "information_synthesis",
            "trend_analysis",
            "competitive_research",
            "academic_research",
            "market_research",
        ]