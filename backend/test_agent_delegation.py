#!/usr/bin/env python3
"""
Test script for agent delegation in the agentic-stack system.
Tests that the orchestrator properly delegates tasks to specialized agents based on task type.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List
import httpx
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentDelegationTester:
    """Test class for agent delegation"""
    
    def __init__(self, orchestrator_url: str = None):
        # Detect if running in Docker
        import os
        self.is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
        
        if orchestrator_url:
            self.orchestrator_url = orchestrator_url
        else:
            # Use localhost from host, or container name from inside Docker
            self.orchestrator_url = "http://localhost:8000"
            
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def check_system_health(self) -> Dict[str, Any]:
        """Check if all components are running"""
        health_status = {
            "orchestrator": False,
            "agents": {
                "research": False,
                "code": False,
                "analytics": False
            },
            "mcp_servers": {
                "web_search": False,
                "python_executor": False
            }
        }
        
        # Check orchestrator
        try:
            response = await self.client.get(f"{self.orchestrator_url}/health")
            health_status["orchestrator"] = response.status_code == 200
            logger.info(f"Orchestrator health: {response.status_code}")
        except Exception as e:
            logger.error(f"Orchestrator health check failed: {e}")
            
        # Check agents via their direct endpoints
        agent_endpoints = {
            "research": "http://agentic-research-agent:8001" if self.is_docker else "http://localhost:8001",
            "code": "http://agentic-code-agent:8002" if self.is_docker else "http://localhost:8002",
            "analytics": "http://agentic-analytics-agent:8003" if self.is_docker else "http://localhost:8003"
        }
        
        for agent_name, endpoint in agent_endpoints.items():
            try:
                response = await self.client.get(f"{endpoint}/health")
                health_status["agents"][agent_name] = response.status_code == 200
                logger.info(f"{agent_name.capitalize()} agent health: {response.status_code}")
            except Exception as e:
                logger.warning(f"{agent_name.capitalize()} agent health check failed: {e}")
                
        # Check MCP servers
        mcp_endpoints = {
            "web_search": "http://mcp-web-search:3001" if self.is_docker else "http://localhost:3001",
            "python_executor": "http://mcp-python-executor:3002" if self.is_docker else "http://localhost:3002"
        }
        
        for server_name, endpoint in mcp_endpoints.items():
            try:
                response = await self.client.get(f"{endpoint}/health")
                health_status["mcp_servers"][server_name] = response.status_code == 200
                logger.info(f"{server_name} MCP server health: {response.status_code}")
            except Exception as e:
                logger.warning(f"{server_name} MCP server health check failed: {e}")
                
        return health_status
    
    async def send_task_to_orchestrator(self, message: str, test_name: str) -> Dict[str, Any]:
        """Send a task to the orchestrator via AG-UI endpoint and monitor delegation"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST: {test_name}")
        logger.info(f"Message: {message}")
        logger.info(f"{'='*60}")
        
        result = {
            "test_name": test_name,
            "message": message,
            "delegated_to": [],
            "events": [],
            "success": False,
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Prepare the request with SSE format expected by AG-UI
            context_id = str(uuid.uuid4())
            
            # Send request to AG-UI endpoint
            async with self.client.stream(
                'POST',
                f"{self.orchestrator_url}/ag-ui",
                json={
                    "message": message,
                    "context_id": context_id
                },
                headers={
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json"
                }
            ) as response:
                
                if response.status_code != 200:
                    result["error"] = f"HTTP {response.status_code}: {await response.aread()}"
                    logger.error(f"Request failed: {result['error']}")
                    return result
                
                # Process SSE stream
                async for line in response.aiter_lines():
                    if not line:
                        continue
                        
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            logger.info("Stream completed")
                            break
                            
                        try:
                            event = json.loads(data_str)
                            result["events"].append(event)
                            
                            # Log event details
                            event_type = event.get("type", "unknown")
                            logger.info(f"Event: {event_type}")
                            
                            # Track delegation from plan events
                            if event_type == "plan":
                                subtasks = event.get("subtasks", [])
                                for subtask in subtasks:
                                    agent = subtask.get("agent")
                                    task = subtask.get("task")
                                    result["delegated_to"].append(agent)
                                    logger.info(f"  → Delegating to {agent}: {task[:50]}...")
                                    
                            elif event_type == "status":
                                logger.info(f"  Status: {event.get('message', '')}")
                                
                            elif event_type == "text_message":
                                content = event.get("content", "")
                                logger.info(f"  Response: {content[:100]}...")
                                
                            elif event_type == "error":
                                result["error"] = event.get("message", "Unknown error")
                                logger.error(f"  Error: {result['error']}")
                                
                            elif event_type == "complete":
                                result["success"] = True
                                logger.info("  Task completed successfully")
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse event: {data_str[:100]}")
                            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Test failed with exception: {e}")
            
        return result
    
    async def run_delegation_tests(self) -> List[Dict[str, Any]]:
        """Run a series of tests to verify delegation logic"""
        
        test_cases = [
            # Research agent tests
            {
                "name": "Research Task - Explicit",
                "message": "Research the latest trends in AI and machine learning",
                "expected_agent": "research"
            },
            {
                "name": "Research Task - Find",
                "message": "Find information about quantum computing applications",
                "expected_agent": "research"
            },
            {
                "name": "Research Task - Search",
                "message": "Search for best practices in microservices architecture",
                "expected_agent": "research"
            },
            
            # Code agent tests
            {
                "name": "Code Task - Python",
                "message": "Generate Python code for a simple REST API",
                "expected_agent": "code"
            },
            {
                "name": "Code Task - Implement",
                "message": "Implement a binary search algorithm",
                "expected_agent": "code"
            },
            {
                "name": "Code Task - Generate",
                "message": "Generate a JavaScript function for data validation",
                "expected_agent": "code"
            },
            
            # Analytics agent tests
            {
                "name": "Analytics Task - Analyze",
                "message": "Analyze the performance metrics from the last quarter",
                "expected_agent": "analytics"
            },
            {
                "name": "Analytics Task - Data",
                "message": "Process this data and create a summary report",
                "expected_agent": "analytics"
            },
            {
                "name": "Analytics Task - Visualize",
                "message": "Visualize the sales trends for the past year",
                "expected_agent": "analytics"
            },
            
            # Multi-agent tests
            {
                "name": "Multi-Agent Task - Research and Code",
                "message": "Research Python web frameworks and then generate code for a simple Flask app",
                "expected_agents": ["research", "code"]
            },
            {
                "name": "Multi-Agent Task - All Three",
                "message": "Research data analysis techniques, implement a Python script for it, and analyze the results",
                "expected_agents": ["research", "code", "analytics"]
            },
            
            # Default fallback test
            {
                "name": "Ambiguous Task - Should Default to Research",
                "message": "Tell me about the weather patterns",
                "expected_agent": "research"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            # Add delay between tests to avoid overwhelming the system
            await asyncio.sleep(2)
            
            result = await self.send_task_to_orchestrator(
                test_case["message"],
                test_case["name"]
            )
            
            # Check if delegation matched expectations
            if "expected_agent" in test_case:
                expected = test_case["expected_agent"]
                if expected in result["delegated_to"]:
                    result["delegation_correct"] = True
                    logger.info(f"✓ Correctly delegated to {expected}")
                else:
                    result["delegation_correct"] = False
                    logger.error(f"✗ Expected delegation to {expected}, got {result['delegated_to']}")
                    
            elif "expected_agents" in test_case:
                expected = test_case["expected_agents"]
                if all(agent in result["delegated_to"] for agent in expected):
                    result["delegation_correct"] = True
                    logger.info(f"✓ Correctly delegated to all: {expected}")
                else:
                    result["delegation_correct"] = False
                    logger.error(f"✗ Expected delegation to {expected}, got {result['delegated_to']}")
            
            results.append(result)
            self.test_results.append(result)
            
        return results
    
    async def monitor_agent_logs(self, duration: int = 5):
        """Monitor Docker logs to verify delegation is happening"""
        logger.info(f"\n{'='*60}")
        logger.info("Monitoring agent logs for delegation evidence...")
        logger.info(f"{'='*60}")
        
        containers = [
            "agentic-orchestrator",
            "agentic-research-agent",
            "agentic-code-agent",
            "agentic-analytics-agent"
        ]
        
        import subprocess
        
        for container in containers:
            try:
                # Get recent logs
                result = subprocess.run(
                    ["docker", "logs", "--tail", "20", container],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info(f"\nRecent logs from {container}:")
                    logger.info("-" * 40)
                    
                    # Look for delegation indicators
                    for line in result.stdout.split('\n')[-10:]:
                        if any(keyword in line.lower() for keyword in 
                               ['delegat', 'task', 'a2a', 'received', 'processing']):
                            logger.info(f"  {line[:120]}")
                            
            except Exception as e:
                logger.warning(f"Could not get logs from {container}: {e}")
    
    def generate_report(self) -> str:
        """Generate a summary report of test results"""
        report = []
        report.append("\n" + "="*80)
        report.append("AGENT DELEGATION TEST REPORT")
        report.append("="*80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Total Tests: {len(self.test_results)}")
        
        successful = sum(1 for r in self.test_results if r.get("success"))
        failed = len(self.test_results) - successful
        
        report.append(f"Successful: {successful}")
        report.append(f"Failed: {failed}")
        
        # Delegation accuracy
        correct_delegations = sum(1 for r in self.test_results 
                                 if r.get("delegation_correct", False))
        if self.test_results:
            accuracy = (correct_delegations / len(self.test_results)) * 100
            report.append(f"Delegation Accuracy: {accuracy:.1f}%")
        
        report.append("\n" + "-"*80)
        report.append("DETAILED RESULTS:")
        report.append("-"*80)
        
        for result in self.test_results:
            report.append(f"\nTest: {result['test_name']}")
            report.append(f"  Message: {result['message'][:60]}...")
            report.append(f"  Success: {'✓' if result['success'] else '✗'}")
            report.append(f"  Delegated to: {', '.join(result['delegated_to']) if result['delegated_to'] else 'None'}")
            
            if "delegation_correct" in result:
                report.append(f"  Delegation Correct: {'✓' if result['delegation_correct'] else '✗'}")
                
            if result.get("error"):
                report.append(f"  Error: {result['error']}")
                
            # Event summary
            event_types = [e.get("type") for e in result.get("events", [])]
            report.append(f"  Events: {', '.join(set(event_types))}")
        
        report.append("\n" + "="*80)
        report.append("SUMMARY:")
        report.append("="*80)
        
        # Agent usage statistics
        agent_usage = {"research": 0, "code": 0, "analytics": 0}
        for result in self.test_results:
            for agent in result.get("delegated_to", []):
                if agent in agent_usage:
                    agent_usage[agent] += 1
                    
        report.append("\nAgent Usage:")
        for agent, count in agent_usage.items():
            report.append(f"  {agent.capitalize()}: {count} tasks")
        
        # Issues found
        report.append("\nIssues Found:")
        issues = []
        
        for result in self.test_results:
            if not result["success"] and result.get("error"):
                issues.append(f"  - {result['test_name']}: {result['error']}")
            elif "delegation_correct" in result and not result["delegation_correct"]:
                issues.append(f"  - {result['test_name']}: Incorrect delegation")
                
        if issues:
            report.extend(issues)
        else:
            report.append("  None - All tests passed successfully!")
        
        return "\n".join(report)
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()

async def main():
    """Main test execution"""
    tester = AgentDelegationTester()
    
    try:
        # Step 1: Check system health
        logger.info("Step 1: Checking system health...")
        health = await tester.check_system_health()
        
        if not health["orchestrator"]:
            logger.error("Orchestrator is not running! Please start it first.")
            return
        
        logger.info(f"System health check complete:")
        logger.info(f"  Orchestrator: {'✓' if health['orchestrator'] else '✗'}")
        for agent, status in health["agents"].items():
            logger.info(f"  {agent.capitalize()} Agent: {'✓' if status else '✗'}")
        for server, status in health["mcp_servers"].items():
            logger.info(f"  {server} MCP: {'✓' if status else '✗'}")
        
        # Step 2: Run delegation tests
        logger.info("\nStep 2: Running delegation tests...")
        await tester.run_delegation_tests()
        
        # Step 3: Monitor logs for delegation evidence
        logger.info("\nStep 3: Checking Docker logs for delegation evidence...")
        await tester.monitor_agent_logs()
        
        # Step 4: Generate report
        report = tester.generate_report()
        print(report)
        
        # Save report to file
        report_file = f"/home/adam/agentic-stack/backend/delegation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"\nReport saved to: {report_file}")
        
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())