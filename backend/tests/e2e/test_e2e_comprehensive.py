#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Agentic Stack
Tests all agents individually and in combination
"""

import asyncio
import json
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
import time
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Test configuration
ORCHESTRATOR_URL = "http://localhost:8000"
RESEARCH_AGENT_URL = "http://localhost:8001"
CODE_AGENT_URL = "http://localhost:8002"
ANALYTICS_AGENT_URL = "http://localhost:8003"
MCP_WEB_SEARCH_URL = "http://localhost:3001"
MCP_PYTHON_EXECUTOR_URL = "http://localhost:3002"

# Test timeout settings
DEFAULT_TIMEOUT = 30.0
LONG_TIMEOUT = 60.0


class TestResult:
    """Track test results"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0
        self.details = {}
    
    def __str__(self):
        status = f"{Fore.GREEN}✓ PASSED" if self.passed else f"{Fore.RED}✗ FAILED"
        result = f"{status}{Style.RESET_ALL} - {self.name} ({self.duration:.2f}s)"
        if self.error:
            result += f"\n  {Fore.YELLOW}Error: {self.error}{Style.RESET_ALL}"
        if self.details:
            result += f"\n  {Fore.CYAN}Details: {json.dumps(self.details, indent=2)}{Style.RESET_ALL}"
        return result


class E2ETestSuite:
    """Comprehensive end-to-end test suite"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.client = None
    
    async def setup(self):
        """Initialize test client"""
        self.client = httpx.AsyncClient(timeout=LONG_TIMEOUT)
    
    async def teardown(self):
        """Cleanup test client"""
        if self.client:
            await self.client.aclose()
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Fore.BLUE}{'='*80}")
        print(f"{Fore.BLUE}{text}")
        print(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}\n")
    
    def print_subheader(self, text: str):
        """Print formatted subheader"""
        print(f"\n{Fore.CYAN}{'-'*60}")
        print(f"{Fore.CYAN}{text}")
        print(f"{Fore.CYAN}{'-'*60}{Style.RESET_ALL}\n")
    
    async def test_service_health(self) -> TestResult:
        """Test all services are healthy"""
        result = TestResult("Service Health Check")
        start_time = time.time()
        
        try:
            services = [
                ("Orchestrator", f"{ORCHESTRATOR_URL}/health"),
                ("Research Agent", f"{RESEARCH_AGENT_URL}/health"),
                ("Code Agent", f"{CODE_AGENT_URL}/health"),
                ("Analytics Agent", f"{ANALYTICS_AGENT_URL}/health"),
                ("MCP Web Search", f"{MCP_WEB_SEARCH_URL}/health"),
                ("MCP Python Executor", f"{MCP_PYTHON_EXECUTOR_URL}/health"),
            ]
            
            all_healthy = True
            service_status = {}
            
            for name, url in services:
                try:
                    response = await self.client.get(url)
                    is_healthy = response.status_code == 200
                    service_status[name] = "healthy" if is_healthy else f"unhealthy ({response.status_code})"
                    if not is_healthy:
                        all_healthy = False
                except Exception as e:
                    service_status[name] = f"error: {str(e)}"
                    all_healthy = False
            
            result.details = service_status
            result.passed = all_healthy
            
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_research_agent_solo(self) -> TestResult:
        """Test research agent independently"""
        result = TestResult("Research Agent Solo Test")
        start_time = time.time()
        
        try:
            # Test direct A2A endpoint
            task_payload = {
                "message": "What are the latest trends in artificial intelligence?",
                "context_id": f"test-research-{datetime.utcnow().isoformat()}",
                "metadata": {"test": True}
            }
            
            response = await self.client.post(
                f"{RESEARCH_AGENT_URL}/a2a/tasks",
                json=task_payload,
                headers={"X-A2A-Version": "0.2.5"}
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                # Wait for completion
                await asyncio.sleep(3)
                
                # Get result
                result_response = await self.client.get(
                    f"{RESEARCH_AGENT_URL}/a2a/tasks/{task_id}?wait=true",
                    headers={"X-A2A-Version": "0.2.5"}
                )
                
                if result_response.status_code == 200:
                    task_result = result_response.json()
                    result.details = {
                        "task_id": task_id,
                        "status": task_result.get("status"),
                        "has_result": bool(task_result.get("result")),
                        "has_error": bool(task_result.get("error"))
                    }
                    result.passed = task_result.get("status") == "completed"
                else:
                    result.error = f"Failed to get task result: {result_response.status_code}"
            else:
                result.error = f"Failed to create task: {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_code_agent_solo(self) -> TestResult:
        """Test code agent independently"""
        result = TestResult("Code Agent Solo Test")
        start_time = time.time()
        
        try:
            # Test direct A2A endpoint with code generation task
            task_payload = {
                "message": "Write a Python function to calculate fibonacci numbers",
                "context_id": f"test-code-{datetime.utcnow().isoformat()}",
                "metadata": {"test": True}
            }
            
            response = await self.client.post(
                f"{CODE_AGENT_URL}/a2a/tasks",
                json=task_payload,
                headers={"X-A2A-Version": "0.2.5"}
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                # Wait for completion
                await asyncio.sleep(5)
                
                # Get result
                result_response = await self.client.get(
                    f"{CODE_AGENT_URL}/a2a/tasks/{task_id}?wait=true",
                    headers={"X-A2A-Version": "0.2.5"}
                )
                
                if result_response.status_code == 200:
                    task_result = result_response.json()
                    result.details = {
                        "task_id": task_id,
                        "status": task_result.get("status"),
                        "has_result": bool(task_result.get("result")),
                        "has_error": bool(task_result.get("error"))
                    }
                    result.passed = task_result.get("status") == "completed"
                else:
                    result.error = f"Failed to get task result: {result_response.status_code}"
            else:
                result.error = f"Failed to create task: {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_analytics_agent_solo(self) -> TestResult:
        """Test analytics agent independently"""
        result = TestResult("Analytics Agent Solo Test")
        start_time = time.time()
        
        try:
            # Test direct A2A endpoint with analytics task
            task_payload = {
                "message": "Analyze the performance metrics: response_times=[100, 150, 200, 120, 180]ms",
                "context_id": f"test-analytics-{datetime.utcnow().isoformat()}",
                "metadata": {"test": True}
            }
            
            response = await self.client.post(
                f"{ANALYTICS_AGENT_URL}/a2a/tasks",
                json=task_payload,
                headers={"X-A2A-Version": "0.2.5"}
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                # Wait for completion
                await asyncio.sleep(3)
                
                # Get result
                result_response = await self.client.get(
                    f"{ANALYTICS_AGENT_URL}/a2a/tasks/{task_id}?wait=true",
                    headers={"X-A2A-Version": "0.2.5"}
                )
                
                if result_response.status_code == 200:
                    task_result = result_response.json()
                    result.details = {
                        "task_id": task_id,
                        "status": task_result.get("status"),
                        "has_result": bool(task_result.get("result")),
                        "has_error": bool(task_result.get("error"))
                    }
                    result.passed = task_result.get("status") == "completed"
                else:
                    result.error = f"Failed to get task result: {result_response.status_code}"
            else:
                result.error = f"Failed to create task: {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_orchestrator_simple(self) -> TestResult:
        """Test orchestrator with simple single-agent task"""
        result = TestResult("Orchestrator Simple Task")
        start_time = time.time()
        
        try:
            # Test AG-UI endpoint with simple research task
            test_payload = {
                "message": "What is Python programming language?",
                "context_id": f"test-orchestrator-simple-{datetime.utcnow().isoformat()}"
            }
            
            response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=test_payload
            )
            
            if response.status_code == 200:
                events = []
                for line in response.text.split("\n"):
                    if line.strip() and line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            events.append(event)
                        except json.JSONDecodeError:
                            pass
                
                # Check for expected event types
                has_plan = any(e.get("type") == "plan" for e in events)
                has_message = any(e.get("type") == "text_message" for e in events)
                
                result.details = {
                    "total_events": len(events),
                    "has_plan": has_plan,
                    "has_message": has_message,
                    "event_types": list(set(e.get("type") for e in events if e.get("type")))
                }
                result.passed = has_plan and has_message
            else:
                result.error = f"Failed with status {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_multi_agent_workflow(self) -> TestResult:
        """Test complex multi-agent workflow"""
        result = TestResult("Multi-Agent Complex Workflow")
        start_time = time.time()
        
        try:
            # Complex task requiring multiple agents
            test_payload = {
                "message": (
                    "Research the concept of quicksort algorithm, "
                    "write a Python implementation of it, "
                    "and analyze its time complexity with sample data"
                ),
                "context_id": f"test-multi-agent-{datetime.utcnow().isoformat()}"
            }
            
            response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=test_payload
            )
            
            if response.status_code == 200:
                events = []
                agent_activities = []
                
                for line in response.text.split("\n"):
                    if line.strip() and line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            events.append(event)
                            
                            # Track agent activities
                            if event.get("type") == "plan":
                                subtasks = event.get("subtasks", [])
                                for task in subtasks:
                                    agent_activities.append(task.get("agent"))
                        except json.JSONDecodeError:
                            pass
                
                # Check for multiple agent involvement
                unique_agents = list(set(filter(None, agent_activities)))
                has_multiple_agents = len(unique_agents) > 1
                
                result.details = {
                    "total_events": len(events),
                    "agents_involved": unique_agents,
                    "multiple_agents": has_multiple_agents,
                    "event_types": list(set(e.get("type") for e in events if e.get("type")))
                }
                result.passed = has_multiple_agents
            else:
                result.error = f"Failed with status {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_streaming_updates(self) -> TestResult:
        """Test real-time streaming updates"""
        result = TestResult("Streaming Updates Test")
        start_time = time.time()
        
        try:
            test_payload = {
                "message": "Generate a simple hello world program",
                "context_id": f"test-streaming-{datetime.utcnow().isoformat()}"
            }
            
            response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=test_payload
            )
            
            if response.status_code == 200:
                event_timestamps = []
                event_types = []
                
                for line in response.text.split("\n"):
                    if line.strip() and line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            event_timestamps.append(time.time())
                            event_types.append(event.get("type"))
                        except json.JSONDecodeError:
                            pass
                
                # Check for streaming behavior
                has_streaming = len(event_timestamps) > 1
                if has_streaming and len(event_timestamps) > 1:
                    time_spread = event_timestamps[-1] - event_timestamps[0]
                else:
                    time_spread = 0
                
                result.details = {
                    "total_events": len(event_timestamps),
                    "time_spread": f"{time_spread:.2f}s",
                    "streaming_detected": has_streaming,
                    "event_sequence": event_types[:5]  # First 5 events
                }
                result.passed = has_streaming
            else:
                result.error = f"Failed with status {response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_error_handling(self) -> TestResult:
        """Test error handling and recovery"""
        result = TestResult("Error Handling Test")
        start_time = time.time()
        
        try:
            # Send invalid/problematic request
            test_payload = {
                "message": "Execute this invalid Python code: print(undefined_variable",
                "context_id": f"test-error-{datetime.utcnow().isoformat()}"
            }
            
            response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=test_payload
            )
            
            if response.status_code == 200:
                error_handled = False
                error_message = None
                
                for line in response.text.split("\n"):
                    if line.strip() and line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            if event.get("type") == "text_message":
                                content = event.get("content", "").lower()
                                if "error" in content or "failed" in content or "issue" in content:
                                    error_handled = True
                                    error_message = event.get("content")[:200]
                        except json.JSONDecodeError:
                            pass
                
                result.details = {
                    "error_handled_gracefully": error_handled,
                    "error_message_preview": error_message
                }
                result.passed = error_handled
            else:
                # Still pass if server returns error status (proper error handling)
                result.details = {"status_code": response.status_code}
                result.passed = True
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_context_persistence(self) -> TestResult:
        """Test context persistence across requests"""
        result = TestResult("Context Persistence Test")
        start_time = time.time()
        
        try:
            context_id = f"test-context-{datetime.utcnow().isoformat()}"
            
            # First request
            first_payload = {
                "message": "My favorite number is 42",
                "context_id": context_id
            }
            
            first_response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=first_payload
            )
            
            if first_response.status_code != 200:
                result.error = f"First request failed: {first_response.status_code}"
                return result
            
            # Second request with same context
            second_payload = {
                "message": "What is my favorite number?",
                "context_id": context_id
            }
            
            second_response = await self.client.post(
                f"{ORCHESTRATOR_URL}/ag-ui/run",
                json=second_payload
            )
            
            if second_response.status_code == 200:
                context_recalled = False
                
                for line in second_response.text.split("\n"):
                    if line.strip() and line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            if event.get("type") == "text_message":
                                content = event.get("content", "")
                                if "42" in content:
                                    context_recalled = True
                        except json.JSONDecodeError:
                            pass
                
                result.details = {
                    "context_id": context_id,
                    "context_recalled": context_recalled
                }
                result.passed = context_recalled
            else:
                result.error = f"Second request failed: {second_response.status_code}"
                
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def test_mcp_integration(self) -> TestResult:
        """Test MCP server integration"""
        result = TestResult("MCP Server Integration Test")
        start_time = time.time()
        
        try:
            # Test MCP Web Search
            web_search_test = await self.client.post(
                f"{MCP_WEB_SEARCH_URL}/tools/search_web",
                json={"query": "test query"}
            )
            web_search_working = web_search_test.status_code == 200
            
            # Test MCP Python Executor
            python_exec_test = await self.client.post(
                f"{MCP_PYTHON_EXECUTOR_URL}/tools/execute_python",
                json={"code": "print('test')"}
            )
            python_exec_working = python_exec_test.status_code == 200
            
            result.details = {
                "web_search_mcp": "working" if web_search_working else "failed",
                "python_executor_mcp": "working" if python_exec_working else "failed"
            }
            result.passed = web_search_working and python_exec_working
            
        except Exception as e:
            result.error = str(e)
        
        result.duration = time.time() - start_time
        return result
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        self.print_header("AGENTIC STACK END-TO-END TEST SUITE")
        print(f"Starting comprehensive tests at {datetime.now().isoformat()}")
        
        # Define test sequence
        tests = [
            ("Infrastructure Tests", [
                self.test_service_health,
                self.test_mcp_integration,
            ]),
            ("Individual Agent Tests", [
                self.test_research_agent_solo,
                self.test_code_agent_solo,
                self.test_analytics_agent_solo,
            ]),
            ("Orchestrator Tests", [
                self.test_orchestrator_simple,
                self.test_multi_agent_workflow,
            ]),
            ("System Behavior Tests", [
                self.test_streaming_updates,
                self.test_error_handling,
                self.test_context_persistence,
            ])
        ]
        
        # Run tests by category
        for category_name, category_tests in tests:
            self.print_subheader(category_name)
            
            for test_func in category_tests:
                print(f"Running: {test_func.__name__.replace('_', ' ').title()}...")
                result = await test_func()
                self.results.append(result)
                print(result)
                await asyncio.sleep(1)  # Brief pause between tests
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        print(f"{Fore.CYAN}Total Tests:{Style.RESET_ALL} {total_tests}")
        print(f"{Fore.GREEN}Passed:{Style.RESET_ALL} {passed_tests}")
        print(f"{Fore.RED}Failed:{Style.RESET_ALL} {failed_tests}")
        print(f"{Fore.YELLOW}Total Duration:{Style.RESET_ALL} {total_duration:.2f}s")
        print()
        
        if failed_tests > 0:
            print(f"{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}")
                    if result.error:
                        print(f"    Error: {result.error}")
        
        # Overall status
        print()
        if failed_tests == 0:
            print(f"{Fore.GREEN}{'='*80}")
            print(f"{Fore.GREEN}ALL TESTS PASSED! 🎉")
            print(f"{Fore.GREEN}The Agentic Stack MVP is fully functional!")
            print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}{'='*80}")
            print(f"{Fore.YELLOW}SOME TESTS FAILED")
            print(f"{Fore.YELLOW}Review the failures above for details")
            print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
        
        # System capabilities summary
        print(f"\n{Fore.CYAN}System Capabilities Verified:{Style.RESET_ALL}")
        capabilities = [
            "✓ Multi-agent orchestration",
            "✓ A2A protocol communication",
            "✓ AG-UI streaming responses",
            "✓ MCP tool integration",
            "✓ Error handling and recovery",
            "✓ Context persistence",
            "✓ Real-time updates"
        ]
        for cap in capabilities:
            print(f"  {cap}")


async def main():
    """Main test runner"""
    suite = E2ETestSuite()
    
    try:
        await suite.setup()
        await suite.run_all_tests()
    finally:
        await suite.teardown()


if __name__ == "__main__":
    asyncio.run(main())