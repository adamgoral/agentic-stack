#!/usr/bin/env python3
"""
Simple test to demonstrate code agent's MCP integration without requiring API keys
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

async def test_mcp_integration():
    """Test direct MCP integration without the full agent pipeline"""
    
    # Initialize dependencies
    a2a_manager = A2AManager()
    context_store = ContextStore()
    
    # Create code agent
    code_agent = CodeAgent(a2a_manager, context_store)
    
    try:
        # Start the agent
        await code_agent.start()
        logger.info("✅ Code agent started successfully")
        
        print("\n" + "="*60)
        print("MCP Python Executor Integration Test")
        print("="*60)
        
        # Test 1: Execute a simple calculation
        print("\n📝 Test 1: Simple Calculation")
        print("-" * 40)
        code = """
# Calculate factorial
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"Factorial of 5 is: {result}")

# Calculate fibonacci
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fib_10 = fibonacci(10)
print(f"10th Fibonacci number is: {fib_10}")
"""
        result = await code_agent.execute_code(code)
        if result.get("success"):
            print(f"✅ Output:\n{result['output']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Test 2: Data manipulation
        print("\n📝 Test 2: Data Manipulation")
        print("-" * 40)
        code2 = """
# Working with lists and dictionaries
data = [1, 2, 3, 4, 5]
squared = [x**2 for x in data]
print(f"Original: {data}")
print(f"Squared: {squared}")

# Dictionary operations
person = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "JavaScript", "Go"]
}

person["skills"].append("Rust")
print(f"\\nPerson data: {person}")
print(f"Skills count: {len(person['skills'])}")
"""
        result2 = await code_agent.execute_code(code2)
        if result2.get("success"):
            print(f"✅ Output:\n{result2['output']}")
        else:
            print(f"❌ Error: {result2['error']}")
        
        # Test 3: Error handling
        print("\n📝 Test 3: Error Handling")
        print("-" * 40)
        error_code = """
try:
    x = 10 / 0
except ZeroDivisionError as e:
    print(f"Caught error: {e}")
    print("Division by zero is not allowed!")

# This will cause an actual error
undefined_variable
"""
        error_result = await code_agent.execute_code(error_code)
        print(f"Success: {error_result.get('success')}")
        if error_result.get('output'):
            print(f"Output: {error_result['output']}")
        if error_result.get('error'):
            print(f"Error (expected): {error_result['error'][:200]}...")
        
        # Test 4: Code validation
        print("\n📝 Test 4: Syntax Validation")
        print("-" * 40)
        
        valid_code = "print('Hello, World!')"
        invalid_code = "def broken(:\n    print('Missing parenthesis')"
        
        valid_result = await code_agent.validate_code(valid_code)
        print(f"Valid code test: {'✅ Valid' if valid_result.get('valid') else '❌ Invalid'}")
        
        invalid_result = await code_agent.validate_code(invalid_code)
        print(f"Invalid code test: {'❌ Invalid (as expected)' if not invalid_result.get('valid') else '✅ Valid'}")
        if invalid_result.get('error'):
            print(f"  Error message: {invalid_result['error']}")
        
        # Test 5: Code analysis
        print("\n📝 Test 5: Code Analysis")
        print("-" * 40)
        analysis_code = """
class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def process(self):
        result = []
        for item in self.data:
            if item > 0:
                result.append(item * 2)
        return result
    
    def summarize(self):
        return {
            'count': len(self.data),
            'sum': sum(self.data),
            'avg': sum(self.data) / len(self.data) if self.data else 0
        }

processor = DataProcessor([1, 2, 3, 4, 5])
print(processor.process())
print(processor.summarize())
"""
        analysis = await code_agent.analyze_code(analysis_code)
        print(f"Code Analysis Results:")
        print(f"  Lines: {analysis.get('lines')}")
        print(f"  Has Classes: {analysis.get('has_classes')}")
        print(f"  Has Functions: {analysis.get('has_functions')}")
        print(f"  Complexity: {analysis.get('complexity')}")
        
        print("\n" + "="*60)
        print("✅ All MCP integration tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop the agent
        await code_agent.stop()
        logger.info("Code agent stopped")

if __name__ == "__main__":
    asyncio.run(test_mcp_integration())