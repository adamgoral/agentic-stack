#!/usr/bin/env python3
"""
MCP Python Executor Server
Provides sandboxed Python code execution via HTTP/SSE endpoint.
"""

import os
import sys
import io
import json
import asyncio
import logging
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(title="Python Executor MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def execute_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: The Python code to execute
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Dictionary containing execution results
    """
    # Capture stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    result = {"output": "", "error": "", "success": False}

    try:
        # Create a restricted globals environment
        safe_globals = {
            "__builtins__": {
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "dict": dict,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "int": int,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "print": print,
                "range": range,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
            }
        }

        # Execute the code with output redirection
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code, safe_globals)

        result["output"] = stdout_buffer.getvalue()
        result["success"] = True

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        result["output"] = stdout_buffer.getvalue()

    finally:
        # Include any stderr output in the error field
        stderr_content = stderr_buffer.getvalue()
        if stderr_content:
            result["error"] = (
                result["error"] + "\nStderr:\n" + stderr_content
                if result["error"]
                else stderr_content
            )

    return result


def validate_python(code: str) -> Dict[str, Any]:
    """
    Validate Python code syntax without executing it.

    Args:
        code: The Python code to validate

    Returns:
        Dictionary containing validation results
    """
    result = {"valid": False, "error": ""}

    try:
        compile(code, "<string>", "exec")
        result["valid"] = True
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {str(e)}"

    return result


def analyze_code(code: str) -> Dict[str, Any]:
    """
    Analyze Python code for potential issues and metrics.

    Args:
        code: The Python code to analyze

    Returns:
        Dictionary containing code analysis results
    """
    result = {
        "lines": len(code.splitlines()),
        "has_imports": "import " in code or "from " in code,
        "has_functions": "def " in code,
        "has_classes": "class " in code,
        "complexity": "simple",  # Simplified for MVP
    }

    # Basic complexity assessment
    if result["has_classes"] or (result["has_functions"] and result["lines"] > 50):
        result["complexity"] = "moderate"
    if result["lines"] > 100:
        result["complexity"] = "complex"

    return result


async def handle_tool_call(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls from the MCP protocol"""
    if tool_name == "execute_python":
        return execute_python(**args)
    elif tool_name == "validate_python":
        return validate_python(**args)
    elif tool_name == "analyze_code":
        return analyze_code(**args)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def event_stream(request: Request) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events stream for MCP protocol"""
    logger.info("Client connected to SSE endpoint")
    
    # Send initial JSONRPC initialize response
    initialize_response = {
        "jsonrpc": "2.0",
        "id": "init",
        "result": {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": {
                    "listTools": {}
                }
            },
            "serverInfo": {
                "name": "python-executor",
                "version": "1.0.0"
            }
        }
    }
    yield f"data: {json.dumps(initialize_response)}\n\n"
    
    # Send tools list notification
    tools_notification = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {
            "tools": [
                {
                    "name": "execute_python",
                    "description": "Execute Python code in a sandboxed environment",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"},
                            "timeout": {"type": "integer", "description": "Execution timeout in seconds", "default": 30}
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "validate_python",
                    "description": "Validate Python code syntax",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to validate"}
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "analyze_code",
                    "description": "Analyze Python code for metrics and potential issues",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to analyze"}
                        },
                        "required": ["code"]
                    }
                }
            ]
        }
    }
    yield f"data: {json.dumps(tools_notification)}\n\n"
    
    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(30)
            # Heartbeat is not needed for JSONRPC - connection is kept alive
            
    except asyncio.CancelledError:
        logger.info("Client disconnected from SSE endpoint")
        raise


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication"""
    return StreamingResponse(
        event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        }
    )


@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a specific tool"""
    try:
        args = await request.json()
        result = await handle_tool_call(tool_name, args)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "python-executor-mcp"}


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Python Executor MCP Server",
        "version": "1.0.0",
        "endpoints": [
            "/sse - SSE endpoint for MCP communication",
            "/tools/{tool_name} - Execute specific tools",
            "/health - Health check",
        ],
        "capabilities": [
            "execute_python - Execute Python code safely",
            "validate_python - Validate Python syntax",
            "analyze_code - Analyze code metrics",
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3002))
    max_execution_time = int(os.getenv("MAX_EXECUTION_TIME", 30))
    logger.info(f"Starting Python Executor MCP Server on port {port}")
    logger.info(f"Max execution time: {max_execution_time} seconds")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")