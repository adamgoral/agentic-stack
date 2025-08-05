#!/usr/bin/env python3
"""
MCP Web Search Server
Provides web search capabilities via the Model Context Protocol.
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP
import httpx

# Create the MCP server
app = FastMCP("Web Search")


@app.tool()
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
        Dictionary containing:
        - results: List of search results with title, url, snippet
        - query: The original search query
        - timestamp: When the search was performed
        - success: Boolean indicating if search succeeded
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


@app.tool()
async def fetch_webpage(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a webpage.

    Args:
        url: The URL to fetch

    Returns:
        Dictionary containing:
        - content: The extracted text content
        - title: Page title if available
        - url: The fetched URL
        - success: Boolean indicating if fetch succeeded
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


@app.tool()
def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text for search optimization.

    Args:
        text: The text to extract keywords from
        max_keywords: Maximum number of keywords to return

    Returns:
        List of extracted keywords
    """
    # Simple keyword extraction (in production, use NLP libraries)
    import re

    # Remove special characters and convert to lowercase
    words = re.findall(r"\b[a-z]+\b", text.lower())

    # Filter out common stop words
    stop_words = {
        "the",
        "is",
        "at",
        "which",
        "on",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "with",
        "to",
        "for",
        "of",
        "as",
        "from",
        "by",
        "that",
        "this",
    }

    keywords = [w for w in words if len(w) > 3 and w not in stop_words]

    # Count frequency and return top keywords
    from collections import Counter

    word_freq = Counter(keywords)

    return [word for word, _ in word_freq.most_common(max_keywords)]


if __name__ == "__main__":
    # Run the server with stdio transport
    app.run()

