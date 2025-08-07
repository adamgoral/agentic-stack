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
import httpx
import re

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.ag_ui import StateDeps

from src.domain.models import ConversationState, AgentTaskState
from src.infrastructure.protocols.a2a_manager import A2AManager
from src.infrastructure.persistence.context_store import ContextStore

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
        
        # Determine if we're running in Docker
        self.is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
        
        # Set MCP server base URL
        self.mcp_base_url = "http://mcp-web-search:3001" if self.is_docker else "http://localhost:3001"
        
        # HTTP client for MCP server calls
        self.http_client = None

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
                url=web_search_url
            )
            logger.info(f"Connected to web search MCP server at {web_search_url}")
        except Exception as e:
            logger.error(f"Failed to connect to web search server at {web_search_url}: {e}")
            # Try alternative URL if first attempt fails
            alt_url = "http://localhost:3001/sse" if is_docker else "http://mcp-web-search:3001/sse"
            try:
                servers["web_search"] = MCPServerSSE(
                    url=alt_url
                )
                logger.info(f"Connected to web search MCP server at {alt_url} (fallback)")
            except Exception as e2:
                logger.error(f"Failed to connect to web search server at {alt_url}: {e2}")

        return servers

    async def start(self):
        """Start the research agent"""
        self.is_running = True
        logger.info("Research agent started")
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

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
        
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()

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

            # Execute actual research using MCP server
            logger.info("Executing research via MCP server...")
            search_results = await self.execute_research(task)
            
            # Format the findings based on actual search results
            if search_results.get("success", False) and search_results.get("results"):
                findings = self._format_research_findings(task, search_results)
                sources = [result.get("url", "") for result in search_results.get("results", [])]
                confidence = "high" if len(search_results.get("results", [])) >= 3 else "medium"
            else:
                # Fallback to using the agent if MCP server fails
                logger.warning("MCP server call failed, falling back to agent-based research")
                
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
                    findings = str(response)
                    sources = self._extract_sources(findings)
                    confidence = self._assess_confidence(findings)
            
            # Process and structure the results
            results = {
                "findings": findings,
                "sources": sources,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                "task_id": task_state.task_id,
                "agent": self.agent_name,
                "mcp_success": search_results.get("success", False),
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

    def _format_research_findings(self, task: str, search_results: Dict[str, Any]) -> str:
        """
        Format search results into a comprehensive research report
        
        Args:
            task: The original research task
            search_results: Results from MCP server
            
        Returns:
            Formatted research findings
        """
        findings = []
        
        # Header
        findings.append(f"# Research Results for: {task}\n")
        findings.append(f"*Generated at: {datetime.utcnow().isoformat()}*\n")
        
        # Check if we have results
        results = search_results.get("results", [])
        
        if not results:
            findings.append("\n## No Results Found\n")
            findings.append("No search results were found for this query. Please try refining your search terms.\n")
            return "\n".join(findings)
        
        # Summary section
        findings.append(f"\n## Summary\n")
        findings.append(f"Found {len(results)} relevant sources for your research query.\n")
        
        # Key Findings section
        findings.append("\n## Key Findings\n")
        
        for i, result in enumerate(results, 1):
            title = result.get("title", f"Result {i}")
            url = result.get("url", "")
            snippet = result.get("snippet", "No description available")
            source = result.get("source", "Unknown source")
            published = result.get("published", "")
            
            findings.append(f"\n### {i}. {title}")
            findings.append(f"**Source:** {source}")
            if url:
                findings.append(f"**URL:** {url}")
            if published:
                findings.append(f"**Published:** {published}")
            findings.append(f"\n{snippet}\n")
        
        # Sources section
        findings.append("\n## Sources\n")
        for i, result in enumerate(results, 1):
            url = result.get("url", "")
            title = result.get("title", f"Result {i}")
            if url:
                findings.append(f"{i}. [{title}]({url})")
            else:
                findings.append(f"{i}. {title}")
        
        # Additional notes
        findings.append("\n## Notes\n")
        findings.append("- Results are ordered by relevance")
        findings.append("- Consider cross-referencing multiple sources for accuracy")
        findings.append("- Some results may be from mock data during testing phase")
        
        return "\n".join(findings)
    
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
    
    async def execute_research(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute actual research using MCP server tools
        
        Args:
            query: The research query
            max_results: Maximum number of results to return
            
        Returns:
            Research results from MCP server
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            # Call the search_web tool on the MCP server
            url = f"{self.mcp_base_url}/tools/search_web"
            payload = {
                "query": query,
                "max_results": max_results,
                "search_type": "general"
            }
            
            logger.info(f"Calling MCP server at {url} with query: {query[:100]}...")
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                search_results = result.get("result", {})
                logger.info(f"Successfully retrieved {len(search_results.get('results', []))} search results")
                return search_results
            else:
                error_msg = result.get("error", "Unknown error occurred")
                logger.error(f"MCP server returned error: {error_msg}")
                return {
                    "results": [],
                    "query": query,
                    "error": error_msg,
                    "success": False
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling MCP server: {e.response.status_code} - {e.response.text}")
            return {
                "results": [],
                "query": query,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "success": False
            }
        except httpx.RequestError as e:
            logger.error(f"Request error calling MCP server: {e}")
            # Try fallback URL if primary fails
            if self.is_docker:
                # Try local URL as fallback
                fallback_url = "http://localhost:3001/tools/search_web"
            else:
                # Try Docker URL as fallback
                fallback_url = "http://mcp-web-search:3001/tools/search_web"
            
            try:
                logger.info(f"Trying fallback URL: {fallback_url}")
                response = await self.http_client.post(fallback_url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return result.get("result", {})
                    
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
            return {
                "results": [],
                "query": query,
                "error": str(e),
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error calling MCP server: {e}")
            return {
                "results": [],
                "query": query,
                "error": str(e),
                "success": False
            }

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