#!/bin/bash

echo "=========================================="
echo "MCP Server Integration Test"
echo "=========================================="

# Test health endpoint
echo -e "\n[1] Testing health endpoint..."
HEALTH=$(curl -s http://localhost:3001/health)
if [[ $? -eq 0 ]]; then
    echo "✓ Health check passed: $HEALTH"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test search_web tool
echo -e "\n[2] Testing search_web tool..."
SEARCH_RESULT=$(curl -s -X POST http://localhost:3001/tools/search_web \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing breakthroughs 2024", "max_results": 3}')

if [[ $? -eq 0 ]]; then
    echo "✓ Search request successful"
    
    # Check if success is true
    SUCCESS=$(echo "$SEARCH_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")
    if [[ "$SUCCESS" == "True" ]]; then
        echo "✓ Search returned success status"
        
        # Count results
        COUNT=$(echo "$SEARCH_RESULT" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['result']['results']))")
        echo "✓ Found $COUNT search results"
        
        # Display results
        echo -e "\nSearch Results:"
        echo "$SEARCH_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, result in enumerate(data['result']['results'], 1):
    print(f\"  {i}. {result['title']}\")
    print(f\"     URL: {result['url']}\")
    print(f\"     Snippet: {result['snippet'][:80]}...\")
    print()
"
    else
        echo "✗ Search returned failure status"
    fi
else
    echo "✗ Search request failed"
fi

# Test with different query types
echo -e "\n[3] Testing different search types..."
QUERIES=("latest AI research papers" "Python vs JavaScript comparison" "microservices best practices")

for query in "${QUERIES[@]}"; do
    echo -e "\n  Testing: $query"
    RESULT=$(curl -s -X POST http://localhost:3001/tools/search_web \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"$query\", \"max_results\": 1}")
    
    SUCCESS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)
    if [[ "$SUCCESS" == "True" ]]; then
        echo "  ✓ Query successful"
    else
        echo "  ✗ Query failed"
    fi
done

echo -e "\n=========================================="
echo "Test Complete!"
echo "=========================================="