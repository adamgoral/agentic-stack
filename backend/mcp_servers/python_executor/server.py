#!/usr/bin/env python3
"""
MCP Python Executor Server
Provides sandboxed Python code execution via the Model Context Protocol.
"""

import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Create the MCP server
app = FastMCP("Python Executor")


@app.tool()
def execute_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: The Python code to execute
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Dictionary containing:
        - output: The stdout output from the code
        - error: Any error messages or exceptions
        - success: Boolean indicating if execution succeeded
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


@app.tool()
def validate_python(code: str) -> Dict[str, Any]:
    """
    Validate Python code syntax without executing it.

    Args:
        code: The Python code to validate

    Returns:
        Dictionary containing:
        - valid: Boolean indicating if syntax is valid
        - error: Any syntax error messages
    """
    result = {"valid": False, "error": ""}

    try:
        compile(code, "<string>", "exec")
        result["valid"] = True
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {str(e)}"

    return result


if __name__ == "__main__":
    # Run the server with stdio transport
    app.run()

