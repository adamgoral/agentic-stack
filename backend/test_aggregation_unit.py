#!/usr/bin/env python3
"""
Unit test for orchestrator result aggregation
"""

import asyncio
import json
from agents.orchestrator import OrchestratorAgent


async def test_aggregation():
    """Test the aggregate_results method directly"""
    
    # Create a mock orchestrator (we only need the aggregation method)
    orchestrator = OrchestratorAgent(None, None)
    
    # Test Case 1: Successful results from all agents
    print("Test 1: All agents successful")
    print("-" * 50)
    
    test_request = "Research Python frameworks and generate code"
    test_results = {
        "research": {
            "status": "completed",
            "task": "Research information about Python frameworks",
            "result": {
                "findings": "Python has several popular web frameworks:\n1. Django - Full-featured framework\n2. FastAPI - Modern, fast, async\n3. Flask - Lightweight and flexible",
                "sources": ["python.org", "djangoproject.com", "fastapi.tiangolo.com"],
                "confidence": "high"
            }
        },
        "code": {
            "status": "completed", 
            "task": "Generate code for a REST API",
            "result": {
                "code": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                "explanation": "This is a simple FastAPI application",
                "language": "python"
            }
        }
    }
    
    aggregated = await orchestrator.aggregate_results(test_request, test_results)
    print(aggregated)
    print("\n")
    
    # Test Case 2: Mixed success and failure
    print("Test 2: Mixed results (one failure)")
    print("-" * 50)
    
    test_results_mixed = {
        "research": {
            "status": "completed",
            "task": "Research information",
            "result": {
                "findings": "Found information about the topic",
                "confidence": "medium"
            }
        },
        "code": {
            "status": "error",
            "task": "Generate code",
            "error": "Failed to generate code: API key missing"
        },
        "analytics": {
            "status": "timeout",
            "task": "Analyze data",
            "error": "Task timed out after 60 seconds"
        }
    }
    
    aggregated = await orchestrator.aggregate_results("Analyze and code", test_results_mixed)
    print(aggregated)
    print("\n")
    
    # Test Case 3: All failures
    print("Test 3: All agents failed")
    print("-" * 50)
    
    test_results_failed = {
        "research": {
            "status": "error",
            "error": "Connection refused"
        },
        "code": {
            "status": "error",
            "error": "API key not configured"
        }
    }
    
    aggregated = await orchestrator.aggregate_results("Do something", test_results_failed)
    print(aggregated)
    print("\n")
    
    # Test Case 4: Analytics agent result
    print("Test 4: Analytics result")
    print("-" * 50)
    
    test_results_analytics = {
        "analytics": {
            "status": "completed",
            "task": "Analyze data trends",
            "result": {
                "analysis": "Data shows increasing trend over time",
                "metrics": {
                    "average": 42.5,
                    "growth_rate": "15%",
                    "peak_value": 100
                },
                "insights": [
                    "Growth is accelerating",
                    "Peak occurred in Q3",
                    "Expect continued growth"
                ]
            }
        }
    }
    
    aggregated = await orchestrator.aggregate_results("Analyze trends", test_results_analytics)
    print(aggregated)


if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    asyncio.run(test_aggregation())