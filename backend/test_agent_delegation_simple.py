#!/usr/bin/env python3
"""
Simple test script for agent delegation using built-in libraries
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime

def test_health(url, name):
    """Test if a service is healthy"""
    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ {name}: {data}")
            return True
    except Exception as e:
        print(f"✗ {name}: {str(e)[:50]}")
        return False

def send_task_to_orchestrator(message, test_name):
    """Send a task to the orchestrator and analyze delegation"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Message: {message}")
    print(f"{'='*60}")
    
    # Prepare request
    url = "http://localhost:8000/ag-ui/run"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    data = json.dumps({
        "message": message,
        "context_id": f"test-{int(time.time())}"
    }).encode()
    
    delegated_to = []
    events_received = []
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            # Read SSE stream
            for line_bytes in response:
                line = line_bytes.decode('utf-8').strip()
                
                if not line:
                    continue
                    
                if line.startswith("data: "):
                    data_str = line[6:]
                    
                    if data_str == "[DONE]":
                        print("  Stream completed")
                        break
                    
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type", "unknown")
                        events_received.append(event_type)
                        
                        # Track delegation
                        if event_type == "plan":
                            subtasks = event.get("subtasks", [])
                            for subtask in subtasks:
                                agent = subtask.get("agent")
                                task = subtask.get("task", "")[:50]
                                delegated_to.append(agent)
                                print(f"  → Delegating to {agent}: {task}...")
                                
                        elif event_type == "status":
                            print(f"  Status: {event.get('message', '')}")
                            
                        elif event_type == "error":
                            print(f"  Error: {event.get('message', '')}")
                            
                        elif event_type == "complete":
                            print("  ✓ Task completed")
                            
                    except json.JSONDecodeError:
                        pass
                        
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None, []
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
        return None, []
    
    return delegated_to, events_received

def check_docker_logs():
    """Check Docker logs for delegation evidence"""
    import subprocess
    
    print(f"\n{'='*60}")
    print("Docker Logs - Delegation Evidence")
    print(f"{'='*60}")
    
    containers = [
        "agentic-orchestrator",
        "agentic-research-agent",
        "agentic-code-agent",
        "agentic-analytics-agent"
    ]
    
    for container in containers:
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", "5", container],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                print(f"\n{container}:")
                # Look for delegation patterns
                for line in result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['delegat', 'task', 'received', 'processing']):
                        print(f"  {line[:100]}")
                        
        except Exception as e:
            pass

def main():
    """Run delegation tests"""
    
    print("="*80)
    print("AGENT DELEGATION TEST")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Check system health
    print("\n1. SYSTEM HEALTH CHECK")
    print("-"*40)
    
    health_ok = True
    health_ok &= test_health("http://localhost:8000", "Orchestrator")
    health_ok &= test_health("http://localhost:8001", "Research Agent")
    health_ok &= test_health("http://localhost:8002", "Code Agent")
    health_ok &= test_health("http://localhost:8003", "Analytics Agent")
    
    if not health_ok:
        print("\n⚠ Some services are not healthy. Tests may fail.")
        
    # Step 2: Run delegation tests
    print("\n2. DELEGATION TESTS")
    print("-"*40)
    
    test_cases = [
        {
            "name": "Research Task",
            "message": "Research the latest trends in artificial intelligence",
            "expected": "research"
        },
        {
            "name": "Code Task",
            "message": "Generate Python code for a binary search algorithm",
            "expected": "code"
        },
        {
            "name": "Analytics Task",
            "message": "Analyze the data and create a performance report",
            "expected": "analytics"
        },
        {
            "name": "Multi-Agent Task",
            "message": "Research Python frameworks, generate code for a web app, and analyze its performance",
            "expected": ["research", "code", "analytics"]
        }
    ]
    
    results = []
    
    for test in test_cases:
        time.sleep(2)  # Delay between tests
        
        delegated, events = send_task_to_orchestrator(test["message"], test["name"])
        
        if delegated is not None:
            # Check if delegation matches expectation
            expected = test["expected"]
            if isinstance(expected, str):
                expected = [expected]
                
            if all(agent in delegated for agent in expected):
                print(f"  ✓ Correctly delegated to: {', '.join(delegated)}")
                results.append((test["name"], True, delegated))
            else:
                print(f"  ✗ Expected {expected}, got {delegated}")
                results.append((test["name"], False, delegated))
        else:
            results.append((test["name"], False, []))
    
    # Step 3: Check logs
    check_docker_logs()
    
    # Step 4: Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for name, success, agents in results:
        status = "✓" if success else "✗"
        agents_str = ', '.join(agents) if agents else "None"
        print(f"  {status} {name}: Delegated to [{agents_str}]")
    
    # Agent usage stats
    agent_usage = {"research": 0, "code": 0, "analytics": 0}
    for _, _, agents in results:
        for agent in agents:
            if agent in agent_usage:
                agent_usage[agent] += 1
                
    print("\nAgent Usage Statistics:")
    for agent, count in agent_usage.items():
        print(f"  {agent.capitalize()}: {count} tasks")
    
    if passed == total:
        print("\n✅ All delegation tests passed!")
    else:
        print(f"\n⚠ {total - passed} tests failed")

if __name__ == "__main__":
    main()