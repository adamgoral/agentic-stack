#!/bin/bash
# Test script for MCP Python Executor Server

echo "Testing MCP Python Executor Server..."
echo "======================================="

# Base URL (change to http://mcp-python-executor:3002 if running in Docker)
BASE_URL="http://localhost:3002"

# Test 1: Health check
echo -e "\n1. Testing health endpoint..."
curl -s "$BASE_URL/health" | python3 -m json.tool

# Test 2: Root endpoint
echo -e "\n2. Testing root endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool

# Test 3: Validate Python code
echo -e "\n3. Testing code validation..."
curl -s -X POST "$BASE_URL/tools/validate_python" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")\nx = 5 + 3\nprint(x)"
  }' | python3 -m json.tool

# Test 4: Validate invalid Python code
echo -e "\n4. Testing invalid code validation..."
curl -s -X POST "$BASE_URL/tools/validate_python" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def broken(\n    print(\"Missing parenthesis\")"
  }' | python3 -m json.tool

# Test 5: Execute Python code
echo -e "\n5. Testing code execution..."
curl -s -X POST "$BASE_URL/tools/execute_python" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from MCP!\")\nfor i in range(3):\n    print(f\"Count: {i}\")\nresult = 10 * 5\nprint(f\"Result: {result}\")"
  }' | python3 -m json.tool

# Test 6: Execute code with error
echo -e "\n6. Testing code execution with error..."
curl -s -X POST "$BASE_URL/tools/execute_python" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"This works\")\nundefined_variable\nprint(\"This will not print\")"
  }' | python3 -m json.tool

# Test 7: Analyze code
echo -e "\n7. Testing code analysis..."
curl -s -X POST "$BASE_URL/tools/analyze_code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import math\n\nclass Calculator:\n    def add(self, a, b):\n        return a + b\n\n    def multiply(self, a, b):\n        return a * b\n\ncalc = Calculator()\nprint(calc.add(5, 3))"
  }' | python3 -m json.tool

echo -e "\n======================================="
echo "Tests completed!"