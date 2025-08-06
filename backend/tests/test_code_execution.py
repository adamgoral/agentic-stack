#!/usr/bin/env python3
"""
Test script to verify code agent's MCP integration for Python code execution
"""

import asyncio
import logging
from agents.code_agent import CodeAgent
from protocols.a2a_manager import A2AManager
from storage.context_store import ContextStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_code_execution():
    """Test the code agent's ability to execute Python code via MCP server"""
    
    # Initialize dependencies
    a2a_manager = A2AManager()
    context_store = ContextStore()
    
    # Create code agent
    code_agent = CodeAgent(a2a_manager, context_store)
    
    try:
        # Start the agent
        await code_agent.start()
        logger.info("Code agent started successfully")
        
        # Test 1: Simple code execution
        logger.info("\n=== Test 1: Simple Code Execution ===")
        simple_code = """
print("Hello from MCP Python executor!")
x = 5
y = 10
result = x + y
print(f"Result: {result}")
"""
        result = await code_agent.execute_code(simple_code)
        logger.info(f"Execution result: {result}")
        
        # Test 2: Code with error
        logger.info("\n=== Test 2: Code with Error ===")
        error_code = """
print("This will work")
undefined_variable
print("This won't be reached")
"""
        error_result = await code_agent.execute_code(error_code)
        logger.info(f"Error result: {error_result}")
        
        # Test 3: Code validation
        logger.info("\n=== Test 3: Code Validation ===")
        invalid_code = """
def broken_function(
    print("Missing closing parenthesis")
"""
        validation_result = await code_agent.validate_code(invalid_code)
        logger.info(f"Validation result: {validation_result}")
        
        # Test 4: Code analysis
        logger.info("\n=== Test 4: Code Analysis ===")
        complex_code = """
import math

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def calculate_circle_area(self, radius):
        area = math.pi * radius ** 2
        self.history.append(f"Circle area (r={radius}) = {area}")
        return area

# Test the calculator
calc = Calculator()
print(calc.add(5, 3))
print(calc.multiply(4, 7))
print(calc.calculate_circle_area(5))
print("History:", calc.history)
"""
        analysis_result = await code_agent.analyze_code(complex_code)
        logger.info(f"Analysis result: {analysis_result}")
        
        # Test 5: Execute the complex code
        logger.info("\n=== Test 5: Execute Complex Code ===")
        execution_result = await code_agent.execute_code(complex_code)
        logger.info(f"Complex code execution result: {execution_result}")
        
        # Test 6: Test with a code task through process_code_task
        logger.info("\n=== Test 6: Process Code Task ===")
        task = "Write a Python function that calculates the factorial of a number and test it with the values 5 and 10"
        task_result = await code_agent.process_code_task(
            task=task,
            context_id="test-context-123",
            metadata={"task_id": "test-task-001"}
        )
        logger.info(f"Task result: {task_result}")
        
        logger.info("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop the agent
        await code_agent.stop()
        logger.info("Code agent stopped")

if __name__ == "__main__":
    asyncio.run(test_code_execution())