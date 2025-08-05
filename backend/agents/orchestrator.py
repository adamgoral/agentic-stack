"""
Orchestrator Agent - Main controller for the multi-agent system
Handles user interactions via AG-UI, delegates tasks via A2A, and manages tool access via MCP
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncio

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE, MCPServerStdio
from pydantic_ai.ag_ui import StateDeps

from models.state import ConversationState, AgentTaskState
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Main orchestrator agent that coordinates all other agents
    """

    def __init__(
        self, a2a_manager: A2AManager, context_store: ContextStore, model: str = "openai:gpt-4o"
    ):
        self.a2a_manager = a2a_manager
        self.context_store = context_store
        self.is_running = False

        # Initialize MCP connections for general tools
        self.mcp_servers = self._initialize_mcp_servers()

        # Create the main PydanticAI agent
        self.agent = Agent(
            model,
            instructions="""You are an intelligent orchestrator agent that:
            1. Understands and analyzes user requests
            2. Decomposes complex tasks into subtasks
            3. Delegates subtasks to specialized agents (Research, Code, Analytics)
            4. Aggregates and synthesizes results from multiple agents
            5. Maintains conversation context and state
            
            Available specialized agents:
            - Research Agent: Web research, documentation analysis, information gathering
            - Code Agent: Code generation, debugging, optimization, testing
            - Analytics Agent: Data analysis, visualization, metrics calculation
            
            When receiving a request:
            1. Analyze what needs to be done
            2. Decide which agents are needed
            3. Create a plan with clear subtasks
            4. Delegate and coordinate execution
            5. Synthesize results into a coherent response
            
            Always maintain a helpful, professional tone and provide clear, actionable insights.""",
            toolsets=list(self.mcp_servers.values()),
        )

        # Agent endpoints for A2A communication
        # Use container names in Docker, localhost otherwise
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
        host_prefix = "agentic-" if is_docker else "localhost"
        
        self.agent_endpoints = {
            "research": f"http://{host_prefix}research-agent:8001" if is_docker else "http://localhost:8001",
            "code": f"http://{host_prefix}code-agent:8002" if is_docker else "http://localhost:8002",
            "analytics": f"http://{host_prefix}analytics-agent:8003" if is_docker else "http://localhost:8003",
        }

    def _initialize_mcp_servers(self) -> Dict[str, Any]:
        """Initialize MCP server connections"""
        servers = {}
        
        # Determine if we're running in Docker
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"

        # Web search server (SSE)
        web_search_url = "http://mcp-web-search:3001/sse" if is_docker else "http://localhost:3001/sse"
        try:
            servers["web_search"] = MCPServerSSE(url=web_search_url, prefix="search_")
            logger.info(f"Connected to web search MCP server at {web_search_url}")
        except Exception as e:
            logger.warning(f"Could not connect to web search server: {e}")

        # Python executor (stdio)
        try:
            servers["python_executor"] = MCPServerStdio(
                "python", args=["-m", "mcp_servers.python_executor.server"]
            )
            logger.info("Connected to Python executor MCP server")
        except Exception as e:
            logger.warning(f"Could not connect to Python executor: {e}")

        return servers

    async def start(self):
        """Start the orchestrator agent"""
        self.is_running = True
        logger.info("Orchestrator agent started")

        # Connect to MCP servers
        for name, server in self.mcp_servers.items():
            try:
                await server.__aenter__()
                logger.info(f"Connected to MCP server: {name}")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {name}: {e}")

    async def stop(self):
        """Stop the orchestrator agent"""
        self.is_running = False

        # Disconnect from MCP servers
        for name, server in self.mcp_servers.items():
            try:
                await server.__aexit__(None, None, None)
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server {name}: {e}")

        logger.info("Orchestrator agent stopped")

    async def decompose_task(self, message: str) -> List[Dict[str, Any]]:
        """
        Decompose a user request into subtasks for different agents
        """
        # Use the agent to analyze and decompose the task
        decomposition_prompt = f"""
        Analyze this user request and decompose it into subtasks:
        
        Request: {message}
        
        Return a JSON list of subtasks with the following structure:
        [
            {{
                "agent": "research|code|analytics",
                "task": "specific task description",
                "priority": 1-5,
                "dependencies": ["task_ids that must complete first"]
            }}
        ]
        """

        # For now, use a simple heuristic-based decomposition
        # In production, this would use the LLM
        subtasks = []

        message_lower = message.lower()

        if any(
            word in message_lower
            for word in ["research", "find", "search", "explore", "investigate"]
        ):
            subtasks.append(
                {
                    "agent": "research",
                    "task": f"Research information about: {message}",
                    "priority": 1,
                    "dependencies": [],
                }
            )

        if any(
            word in message_lower
            for word in ["code", "implement", "generate", "program", "python", "javascript"]
        ):
            subtasks.append(
                {
                    "agent": "code",
                    "task": f"Generate code for: {message}",
                    "priority": 2,
                    "dependencies": ["research"] if subtasks else [],
                }
            )

        if any(
            word in message_lower for word in ["analyze", "data", "metrics", "visualize", "report"]
        ):
            subtasks.append(
                {
                    "agent": "analytics",
                    "task": f"Analyze data for: {message}",
                    "priority": 3,
                    "dependencies": [],
                }
            )

        # If no specific keywords, default to research
        if not subtasks:
            subtasks.append(
                {"agent": "research", "task": message, "priority": 1, "dependencies": []}
            )

        return subtasks

    async def delegate_to_agent(
        self, agent_name: str, task: str, context_id: str
    ) -> Dict[str, Any]:
        """
        Delegate a task to a specialized agent via A2A
        """
        agent_url = self.agent_endpoints.get(agent_name)
        if not agent_url:
            raise ValueError(f"Unknown agent: {agent_name}")

        logger.info(f"Delegating to {agent_name}: {task}")

        try:
            # Send task via A2A protocol
            result = await self.a2a_manager.send_task_to_agent(
                agent_url=agent_url, message=task, context_id=context_id
            )

            # Store task state
            task_state = AgentTaskState(
                task_id=result.get("task_id"),
                agent_name=agent_name,
                status="in_progress",
                input_data={"task": task},
                output_data=None,
                error=None,
            )
            await self.context_store.store_task(task_state)

            return result

        except Exception as e:
            logger.error(f"Error delegating to {agent_name}: {e}")
            raise

    async def execute_subtasks(
        self, subtasks: List[Dict[str, Any]], context_id: str
    ) -> Dict[str, Any]:
        """
        Execute subtasks in parallel or sequence based on dependencies
        """
        results = {}

        # Group tasks by dependency level
        dependency_levels = {}
        for task in subtasks:
            level = len(task.get("dependencies", []))
            if level not in dependency_levels:
                dependency_levels[level] = []
            dependency_levels[level].append(task)

        # Execute tasks level by level
        for level in sorted(dependency_levels.keys()):
            level_tasks = dependency_levels[level]

            # Execute tasks at the same level in parallel
            tasks = []
            for task in level_tasks:
                coro = self.delegate_to_agent(
                    agent_name=task["agent"], task=task["task"], context_id=context_id
                )
                tasks.append(coro)

            # Wait for all tasks at this level to complete
            level_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Store results
            for task, result in zip(level_tasks, level_results):
                if isinstance(result, Exception):
                    results[task["agent"]] = {"error": str(result)}
                else:
                    results[task["agent"]] = result

        return results

    async def run_ag_ui(self, message: str, state: ConversationState) -> AsyncGenerator[str, None]:
        """
        Process a request and stream AG-UI events
        """
        try:
            # Start event
            yield json.dumps(
                {
                    "type": "start",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": state.context_id,
                }
            )

            # Task decomposition
            yield json.dumps(
                {"type": "status", "message": "Analyzing request and planning tasks..."}
            )

            subtasks = await self.decompose_task(message)

            yield json.dumps({"type": "plan", "subtasks": subtasks})

            # Execute subtasks
            yield json.dumps(
                {"type": "status", "message": "Delegating tasks to specialized agents..."}
            )

            results = await self.execute_subtasks(subtasks, state.context_id)

            # Synthesize results
            yield json.dumps({"type": "status", "message": "Synthesizing results..."})

            # Use the main agent to synthesize
            async with self.agent as agent:
                synthesis_prompt = f"""
                User request: {message}
                
                Results from specialized agents:
                {json.dumps(results, indent=2)}
                
                Please synthesize these results into a coherent response.
                """

                response = await agent.run(synthesis_prompt)

                # Stream the synthesized response
                yield json.dumps({"type": "text_message", "content": str(response)})

            # Update state
            state.task_history.append(
                {
                    "message": message,
                    "subtasks": subtasks,
                    "results": results,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Store updated state
            await self.context_store.store_context(state)

            # Complete event
            yield json.dumps({"type": "complete", "timestamp": datetime.utcnow().isoformat()})

        except Exception as e:
            logger.error(f"Error in AG-UI execution: {e}")
            yield json.dumps({"type": "error", "message": str(e)})

    def to_a2a(self):
        """Convert to A2A server for agent-to-agent communication"""
        return self.agent.to_a2a()

    def to_ag_ui(self):
        """Convert to AG-UI server for frontend communication"""
        return self.agent.to_ag_ui()

    async def get_connected_agents(self) -> List[str]:
        """Get list of connected agents"""
        connected = []
        for name, url in self.agent_endpoints.items():
            # Check if agent is reachable
            if await self.a2a_manager.ping_agent(url):
                connected.append(name)
        return connected

    async def get_mcp_servers(self) -> Dict[str, bool]:
        """Get status of MCP servers"""
        status = {}
        for name, server in self.mcp_servers.items():
            # Check if server is connected
            status[name] = hasattr(server, "_client") and server._client is not None
        return status

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed status of all agents"""
        status = {
            "orchestrator": {
                "status": "running" if self.is_running else "stopped",
                "model": self.agent.model,
                "mcp_servers": await self.get_mcp_servers(),
            },
            "agents": {},
        }

        for name, url in self.agent_endpoints.items():
            is_connected = await self.a2a_manager.ping_agent(url)
            status["agents"][name] = {
                "url": url,
                "status": "connected" if is_connected else "disconnected",
            }

        return status

