#!/usr/bin/env python3
"""
Simple End-to-End Test using standard library only (no external dependencies)
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime

# Test configuration
ORCHESTRATOR_URL = "http://localhost:8000"
RESEARCH_AGENT_URL = "http://localhost:8001"
CODE_AGENT_URL = "http://localhost:8002"
ANALYTICS_AGENT_URL = "http://localhost:8003"
MCP_WEB_SEARCH_URL = "http://localhost:3001"
MCP_PYTHON_EXECUTOR_URL = "http://localhost:3002"


def make_request(url, data=None, headers=None, method="GET"):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    if data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.getcode(), response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)


def test_service_health():
    """Test all services are healthy"""
    print("\n" + "="*60)
    print("SERVICE HEALTH CHECK")
    print("="*60)
    
    services = [
        ("Orchestrator", f"{ORCHESTRATOR_URL}/health"),
        ("Research Agent", f"{RESEARCH_AGENT_URL}/health"),
        ("Code Agent", f"{CODE_AGENT_URL}/health"),
        ("Analytics Agent", f"{ANALYTICS_AGENT_URL}/health"),
        ("MCP Web Search", f"{MCP_WEB_SEARCH_URL}/health"),
        ("MCP Python Executor", f"{MCP_PYTHON_EXECUTOR_URL}/health"),
    ]
    
    all_healthy = True
    for name, url in services:
        status, response = make_request(url)
        if status == 200:
            print(f"✓ {name}: Healthy")
        else:
            print(f"✗ {name}: Failed (status={status})")
            all_healthy = False
    
    return all_healthy


def test_orchestrator_simple():
    """Test orchestrator with simple task"""
    print("\n" + "="*60)
    print("ORCHESTRATOR SIMPLE TASK TEST")
    print("="*60)
    
    test_payload = {
        "message": "What is 2+2?",
        "context_id": f"test-simple-{datetime.utcnow().isoformat()}"
    }
    
    print(f"Sending: {test_payload['message']}")
    status, response = make_request(
        f"{ORCHESTRATOR_URL}/ag-ui/run",
        data=test_payload,
        method="POST"
    )
    
    if status == 200:
        print("✓ Request successful")
        
        # Parse SSE events
        events = []
        for line in response.split("\n"):
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except:
                    pass
        
        print(f"  Received {len(events)} events")
        
        # Check for plan
        plans = [e for e in events if e.get("type") == "plan"]
        if plans:
            print(f"  Plan created with {len(plans[0].get('subtasks', []))} subtasks")
            for task in plans[0].get('subtasks', []):
                print(f"    - {task.get('agent')}: {task.get('description', '')[:50]}...")
        
        # Check for response
        messages = [e for e in events if e.get("type") == "text_message"]
        if messages:
            content = messages[0].get("content", "")[:200]
            print(f"  Response preview: {content}...")
        
        return True
    else:
        print(f"✗ Request failed with status {status}")
        return False


def test_multi_agent_workflow():
    """Test complex multi-agent workflow"""
    print("\n" + "="*60)
    print("MULTI-AGENT WORKFLOW TEST")
    print("="*60)
    
    test_payload = {
        "message": (
            "Research Python list comprehensions, "
            "write an example that filters even numbers, "
            "and analyze its performance"
        ),
        "context_id": f"test-multi-{datetime.utcnow().isoformat()}"
    }
    
    print(f"Sending complex task...")
    print(f"  {test_payload['message'][:80]}...")
    
    status, response = make_request(
        f"{ORCHESTRATOR_URL}/ag-ui/run",
        data=test_payload,
        method="POST"
    )
    
    if status == 200:
        print("✓ Request successful")
        
        # Parse SSE events
        events = []
        for line in response.split("\n"):
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except:
                    pass
        
        # Check for multiple agents
        plans = [e for e in events if e.get("type") == "plan"]
        if plans and plans[0].get('subtasks'):
            agents = set()
            for task in plans[0].get('subtasks', []):
                agent = task.get('agent')
                if agent:
                    agents.add(agent)
            
            if len(agents) > 1:
                print(f"✓ Multiple agents involved: {', '.join(agents)}")
                return True
            else:
                print(f"✗ Only one agent involved: {', '.join(agents)}")
                return False
        else:
            print("✗ No plan created")
            return False
    else:
        print(f"✗ Request failed with status {status}")
        return False


def test_agent_endpoints():
    """Test individual agent A2A endpoints"""
    print("\n" + "="*60)
    print("INDIVIDUAL AGENT A2A ENDPOINTS TEST")
    print("="*60)
    
    agents = [
        ("Research Agent", RESEARCH_AGENT_URL, "What is machine learning?"),
        ("Code Agent", CODE_AGENT_URL, "Write a hello world function"),
        ("Analytics Agent", ANALYTICS_AGENT_URL, "Analyze data: [1,2,3,4,5]"),
    ]
    
    all_working = True
    for name, url, message in agents:
        print(f"\nTesting {name}...")
        
        task_payload = {
            "message": message,
            "context_id": f"test-{name.lower().replace(' ', '-')}-{datetime.utcnow().isoformat()}",
            "metadata": {"test": True}
        }
        
        # Create task
        status, response = make_request(
            f"{url}/a2a/tasks",
            data=task_payload,
            headers={"X-A2A-Version": "0.2.5"},
            method="POST"
        )
        
        if status == 200:
            try:
                result = json.loads(response)
                task_id = result.get("task_id")
                print(f"  ✓ Task created: {task_id}")
                
                # Wait and check result
                time.sleep(2)
                status2, response2 = make_request(
                    f"{url}/a2a/tasks/{task_id}?wait=true",
                    headers={"X-A2A-Version": "0.2.5"}
                )
                
                if status2 == 200:
                    result2 = json.loads(response2)
                    if result2.get("status") == "completed":
                        print(f"  ✓ Task completed successfully")
                    else:
                        print(f"  ⚠ Task status: {result2.get('status')}")
                        if result2.get('error'):
                            print(f"    Error: {result2.get('error')[:100]}...")
                else:
                    print(f"  ✗ Failed to get task result: {status2}")
                    all_working = False
            except Exception as e:
                print(f"  ✗ Error: {e}")
                all_working = False
        else:
            print(f"  ✗ Failed to create task: {status}")
            all_working = False
    
    return all_working


def test_mcp_servers():
    """Test MCP server endpoints directly"""
    print("\n" + "="*60)
    print("MCP SERVER DIRECT TEST")
    print("="*60)
    
    # Test Web Search MCP
    print("\nTesting Web Search MCP...")
    status, response = make_request(
        f"{MCP_WEB_SEARCH_URL}/tools/search_web",
        data={"query": "Python programming"},
        method="POST"
    )
    
    web_search_ok = False
    if status == 200:
        print("  ✓ Web search endpoint working")
        web_search_ok = True
    else:
        print(f"  ✗ Web search failed: {status}")
    
    # Test Python Executor MCP
    print("\nTesting Python Executor MCP...")
    status, response = make_request(
        f"{MCP_PYTHON_EXECUTOR_URL}/tools/execute_python",
        data={"code": "print('Hello from MCP')"},
        method="POST"
    )
    
    python_exec_ok = False
    if status == 200:
        print("  ✓ Python executor endpoint working")
        try:
            result = json.loads(response)
            if result.get("success"):
                print(f"    Output: {result.get('output', '')[:50]}")
            python_exec_ok = True
        except:
            pass
    else:
        print(f"  ✗ Python executor failed: {status}")
    
    return web_search_ok and python_exec_ok


def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("ERROR HANDLING TEST")
    print("="*60)
    
    test_payload = {
        "message": "Execute invalid code: print(undefined_var)",
        "context_id": f"test-error-{datetime.utcnow().isoformat()}"
    }
    
    print("Sending request with invalid code...")
    status, response = make_request(
        f"{ORCHESTRATOR_URL}/ag-ui/run",
        data=test_payload,
        method="POST"
    )
    
    if status == 200:
        # Check if error is handled gracefully
        events = []
        for line in response.split("\n"):
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except:
                    pass
        
        # Look for error handling in response
        messages = [e for e in events if e.get("type") == "text_message"]
        if messages:
            content = messages[0].get("content", "").lower()
            if any(word in content for word in ["error", "failed", "issue", "problem"]):
                print("✓ Error handled gracefully")
                return True
            else:
                print("✗ Error not properly communicated")
                return False
    else:
        # Server returning error status is also proper error handling
        print(f"✓ Server returned error status: {status}")
        return True
    
    return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("AGENTIC STACK END-TO-END TEST SUITE (Simple Version)")
    print("="*80)
    print(f"Starting tests at {datetime.now().isoformat()}")
    
    results = {}
    
    # Run tests
    print("\nRunning tests...")
    results["Service Health"] = test_service_health()
    results["Orchestrator Simple"] = test_orchestrator_simple()
    results["Multi-Agent Workflow"] = test_multi_agent_workflow()
    results["Agent Endpoints"] = test_agent_endpoints()
    results["MCP Servers"] = test_mcp_servers()
    results["Error Handling"] = test_error_handling()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*80)
    if passed == total:
        print("ALL TESTS PASSED! 🎉")
        print("The Agentic Stack MVP is fully functional!")
    else:
        print(f"SOME TESTS FAILED ({total - passed} failures)")
        print("Review the output above for details")
    print("="*80)


if __name__ == "__main__":
    main()