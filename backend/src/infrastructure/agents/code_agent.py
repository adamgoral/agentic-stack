"""
Code Agent - Specialized agent for code analysis, generation, and execution
Handles code tasks via A2A, delegates to Python executor MCP server
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


class CodeAgent:
    """
    Code agent specialized in code analysis, generation, and execution
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
        self.mcp_base_url = "http://mcp-python-executor:3002" if self.is_docker else "http://localhost:3002"
        
        # HTTP client for MCP server calls
        self.http_client = None

        # Initialize MCP connection to Python executor server
        self.mcp_servers = self._initialize_mcp_servers()

        # Create the PydanticAI agent with code-specific instructions
        self.agent = Agent(
            model,
            instructions="""You are a specialized code agent with expertise in:
            1. Code analysis and understanding
            2. Code generation and implementation
            3. Code refactoring and optimization
            4. Debugging and error resolution
            5. Code execution and testing
            
            Your capabilities include:
            - Analyzing code for bugs, security issues, and performance problems
            - Generating code based on requirements and specifications
            - Executing Python code safely in an isolated environment
            - Refactoring code to improve readability and maintainability
            - Writing and running tests
            - Providing detailed explanations of code behavior
            
            When handling code tasks:
            1. Always analyze requirements carefully before implementation
            2. Follow best practices and design patterns
            3. Write clean, well-documented code
            4. Consider edge cases and error handling
            5. Test your code before providing it
            6. Explain your implementation decisions
            
            For code execution:
            - Always execute code in the safe sandbox environment
            - Handle errors gracefully and provide meaningful error messages
            - Include relevant output and results
            - Be mindful of resource usage and execution time
            
            Always provide:
            - Clear explanations of the code's purpose and behavior
            - Comments for complex logic
            - Error handling for edge cases
            - Example usage when appropriate
            - Performance considerations for large-scale use""",
            toolsets=list(self.mcp_servers.values()),
        )

        # Store agent metadata
        self.agent_name = "code"
        self.agent_version = "1.0.0"

    def _initialize_mcp_servers(self) -> Dict[str, Any]:
        """Initialize MCP server connections"""
        servers = {}

        # Determine if we're running in Docker
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
        
        # Connect to Python executor server using SSE
        python_executor_url = "http://mcp-python-executor:3002/sse" if is_docker else "http://localhost:3002/sse"
        
        try:
            servers["python_executor"] = MCPServerSSE(
                url=python_executor_url, 
                prefix="exec_"
            )
            logger.info(f"Connected to Python executor MCP server at {python_executor_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Python executor server at {python_executor_url}: {e}")
            # Try alternative URL if first attempt fails
            alt_url = "http://localhost:3002/sse" if is_docker else "http://mcp-python-executor:3002/sse"
            try:
                servers["python_executor"] = MCPServerSSE(
                    url=alt_url, 
                    prefix="exec_"
                )
                logger.info(f"Connected to Python executor MCP server at {alt_url} (fallback)")
            except Exception as e2:
                logger.error(f"Failed to connect to Python executor server at {alt_url}: {e2}")

        return servers

    async def start(self):
        """Start the code agent"""
        self.is_running = True
        logger.info("Code agent started")
        
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
        """Stop the code agent"""
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

        logger.info("Code agent stopped")

    async def process_code_task(
        self, task: str, context_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a code-related task
        
        Args:
            task: The code task to perform
            context_id: Context ID for the conversation
            metadata: Optional metadata about the task
            
        Returns:
            Code execution results, generated code, or analysis results
        """
        try:
            logger.info(f"Processing code task: {task[:100]}...")

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

            # Run the code task
            async with self.agent as agent:
                # Enhance the prompt with code-specific guidance
                code_prompt = f"""
                Code Task: {task}
                
                Please help with this code-related task. You can:
                1. Analyze existing code for issues or improvements
                2. Generate new code based on requirements
                3. Execute Python code to test solutions
                4. Debug and fix code problems
                5. Refactor code for better quality
                
                For code execution:
                - Use the Python executor to run and test code
                - Provide clear output and results
                - Handle errors gracefully
                
                For code generation:
                - Follow best practices and design patterns
                - Include proper error handling
                - Add helpful comments
                - Consider edge cases
                
                Provide a comprehensive response that includes:
                - The solution or analysis
                - Code snippets with explanations
                - Execution results if applicable
                - Any recommendations or considerations
                """

                # Execute the code task
                response = await agent.run(code_prompt)

                # Process and structure the results
                results = {
                    "response": str(response),
                    "code_snippets": self._extract_code_snippets(str(response)),
                    "execution_results": self._extract_execution_results(str(response)),
                    "timestamp": datetime.utcnow().isoformat(),
                    "task_id": task_state.task_id,
                    "agent": self.agent_name,
                }

                # Update task state
                task_state.complete(results)
                await self.context_store.store_task(task_state)

                logger.info(f"Code task completed: {task_state.task_id}")
                return results

        except Exception as e:
            logger.error(f"Error processing code task: {e}")
            if 'task_state' in locals():
                task_state.fail(str(e))
                await self.context_store.store_task(task_state)
            raise

    async def execute_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code using the MCP Python executor server
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Execution results from MCP server
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            # First validate the code syntax
            validation_result = await self.validate_code(code)
            if not validation_result.get("valid", False):
                return {
                    "success": False,
                    "error": validation_result.get("error", "Invalid Python syntax"),
                    "output": ""
                }
            
            # Execute the code
            url = f"{self.mcp_base_url}/tools/execute_python"
            payload = {
                "code": code,
                "timeout": timeout
            }
            
            logger.info(f"Executing code via MCP server at {url}")
            logger.debug(f"Code to execute: {code[:200]}...")
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                execution_result = result.get("result", {})
                logger.info(f"Code execution completed successfully")
                return execution_result
            else:
                error_msg = result.get("error", "Unknown execution error")
                logger.error(f"Code execution failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "output": ""
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling MCP server: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "output": ""
            }
        except httpx.RequestError as e:
            logger.error(f"Request error calling MCP server: {e}")
            
            # Try fallback URL if primary fails
            fallback_url = "http://localhost:3002/tools/execute_python" if self.is_docker else "http://mcp-python-executor:3002/tools/execute_python"
            
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
                "success": False,
                "error": f"Failed to connect to MCP server: {str(e)}",
                "output": ""
            }
        except Exception as e:
            logger.error(f"Unexpected error executing code: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "output": ""
            }
    
    async def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate Python code syntax using the MCP Python executor server
        
        Args:
            code: Python code to validate
            
        Returns:
            Validation results from MCP server
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            url = f"{self.mcp_base_url}/tools/validate_python"
            payload = {"code": code}
            
            logger.debug(f"Validating code syntax via MCP server")
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                validation_result = result.get("result", {})
                return validation_result
            else:
                return {
                    "valid": False,
                    "error": result.get("error", "Validation failed")
                }
                
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            # Return as valid to allow execution attempt
            return {"valid": True, "error": ""}
    
    async def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze Python code for metrics and potential issues
        
        Args:
            code: Python code to analyze
            
        Returns:
            Analysis results from MCP server
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            url = f"{self.mcp_base_url}/tools/analyze_code"
            payload = {"code": code}
            
            logger.debug(f"Analyzing code via MCP server")
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                return result.get("result", {})
            else:
                return {
                    "lines": 0,
                    "complexity": "unknown",
                    "error": result.get("error", "Analysis failed")
                }
                
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {
                "lines": 0,
                "complexity": "unknown",
                "error": str(e)
            }

    def _extract_code_snippets(self, response: str) -> List[Dict[str, str]]:
        """Extract code snippets from the response"""
        snippets = []
        
        # Look for code blocks in markdown format
        import re
        code_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        matches = code_pattern.findall(response)
        
        for language, code in matches:
            snippets.append({
                "language": language or "python",
                "code": code.strip()
            })
        
        return snippets

    def _extract_execution_results(self, response: str) -> List[Dict[str, Any]]:
        """Extract execution results from the response"""
        results = []
        
        # Look for output blocks or execution results
        import re
        output_pattern = re.compile(r'Output:\s*\n```\n(.*?)\n```', re.DOTALL)
        matches = output_pattern.findall(response)
        
        for output in matches:
            results.append({
                "type": "output",
                "content": output.strip()
            })
        
        # Also look for error blocks
        error_pattern = re.compile(r'Error:\s*\n```\n(.*?)\n```', re.DOTALL)
        error_matches = error_pattern.findall(response)
        
        for error in error_matches:
            results.append({
                "type": "error",
                "content": error.strip()
            })
        
        return results

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
            # Process the code task
            results = await self.process_code_task(message, context_id, metadata)

            # Format for A2A response
            return {
                "status": "completed",
                "result": results,
                "artifacts": {
                    "code_snippets": results.get("code_snippets", []),
                    "execution_results": results.get("execution_results", []),
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
                {"type": "status", "message": "Processing code task..."}
            )

            # Process the code task
            results = await self.process_code_task(message, state.context_id)

            # Stream the results
            yield json.dumps({
                "type": "text_message",
                "content": results["response"],
                "metadata": {
                    "code_snippets": results.get("code_snippets", []),
                    "execution_results": results.get("execution_results", []),
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
            "code_analysis",
            "code_generation",
            "code_execution",
            "debugging",
            "refactoring",
            "testing",
            "performance_optimization",
            "security_analysis",
            "documentation_generation",
            "code_review",
        ]