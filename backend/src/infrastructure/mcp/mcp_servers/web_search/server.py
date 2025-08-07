#!/usr/bin/env python3
"""
MCP Web Search Server
Provides web search capabilities via HTTP/SSE endpoint.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from collections import Counter
import re

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(title="Web Search MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def search_web(
    query: str, max_results: int = 5, search_type: str = "general"
) -> Dict[str, Any]:
    """
    Search the web for information.

    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 5)
        search_type: Type of search - "general", "news", "academic" (default: "general")

    Returns:
        Dictionary containing search results
    """
    result = {
        "results": [],
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "error": None,
    }

    try:
        # Mock search results for MVP
        # In production, integrate with a real search API like Serper, Bing, or Google
        mock_results = [
            {
                "title": f"Result {i + 1} for: {query}",
                "url": f"https://example.com/result{i + 1}",
                "snippet": f"This is a relevant snippet about {query}. "
                f"It contains useful information that helps answer the query.",
                "source": "example.com",
                "published": datetime.now().isoformat(),
            }
            for i in range(min(max_results, 5))
        ]

        result["results"] = mock_results
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


async def fetch_webpage(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a webpage.

    Args:
        url: The URL to fetch

    Returns:
        Dictionary containing webpage content
    """
    result = {"content": "", "title": "", "url": url, "success": False, "error": None}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

            # Basic content extraction (in production, use BeautifulSoup or similar)
            result["content"] = response.text[:5000]  # Limit content size
            result["success"] = True

            # Try to extract title from HTML
            if "<title>" in response.text and "</title>" in response.text:
                start = response.text.index("<title>") + 7
                end = response.text.index("</title>")
                result["title"] = response.text[start:end].strip()

    except httpx.HTTPError as e:
        result["error"] = f"HTTP error: {str(e)}"
    except Exception as e:
        result["error"] = f"Error fetching webpage: {str(e)}"

    return result


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text for search optimization.

    Args:
        text: The text to extract keywords from
        max_keywords: Maximum number of keywords to return

    Returns:
        List of extracted keywords
    """
    # Remove special characters and convert to lowercase
    words = re.findall(r"\b[a-z]+\b", text.lower())

    # Filter out common stop words
    stop_words = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "but",
        "in", "with", "to", "for", "of", "as", "from", "by", "that", "this",
    }

    keywords = [w for w in words if len(w) > 3 and w not in stop_words]

    # Count frequency and return top keywords
    word_freq = Counter(keywords)
    return [word for word, _ in word_freq.most_common(max_keywords)]


async def handle_tool_call(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls from the MCP protocol"""
    if tool_name == "search_web":
        return await search_web(**args)
    elif tool_name == "fetch_webpage":
        return await fetch_webpage(**args)
    elif tool_name == "extract_keywords":
        return extract_keywords(**args)
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
                "name": "web-search",
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
                    "name": "search_web",
                    "description": "Search the web for information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5},
                            "search_type": {"type": "string", "description": "Type of search", "default": "general"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "fetch_webpage",
                    "description": "Fetch and extract content from a webpage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to fetch"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "extract_keywords",
                    "description": "Extract keywords from text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to extract keywords from"},
                            "max_keywords": {"type": "integer", "description": "Maximum keywords to extract", "default": 10}
                        },
                        "required": ["text"]
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
    return {"status": "healthy", "service": "web-search-mcp"}


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Web Search MCP Server",
        "version": "1.0.0",
        "endpoints": [
            "/sse - SSE endpoint for MCP communication",
            "/tools/{tool_name} - Execute specific tools",
            "/health - Health check",
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    logger.info(f"Starting Web Search MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")