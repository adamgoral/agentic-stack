# Analytics Agent

## Overview

The Analytics Agent is a specialized AI agent designed for data analysis, statistical calculations, and visualization recommendations. It's part of the Agentic Stack multi-agent system and supports the A2A (Agent-to-Agent) protocol for seamless integration with other agents.

## Features

### Core Capabilities
- **Data Analysis**: Pattern recognition, trend identification, anomaly detection
- **Statistical Analysis**: Mean, median, standard deviation, correlations
- **Metrics Calculation**: KPIs, growth rates, performance metrics
- **Visualization Design**: Chart recommendations with specifications
- **Comparative Analysis**: Period-over-period comparisons, benchmarking
- **Insights Generation**: Actionable insights from data patterns
- **Forecasting**: Basic trend projection and predictions

### Technical Features
- A2A Protocol support for agent-to-agent communication
- Built-in Python analytics (no external MCP server required)
- Async/await for efficient processing
- Comprehensive error handling and logging
- Docker-ready with environment detection

## Usage

### Running Standalone

```bash
# Run directly
python -m agents.analytics_agent --port 8003

# Or use the run script
python agents/run_analytics_agent.py --port 8003

# With custom model
python -m agents.analytics_agent --port 8003 --model "openai:gpt-4o"
```

### Running in Docker

The agent is included in the docker-compose configuration:

```bash
docker-compose up analytics-agent
```

### API Endpoints

- `GET /health` - Health check
- `GET /status` - Agent status and configuration
- `GET /capabilities` - List of agent capabilities
- `POST /a2a/tasks` - Submit analytics task via A2A protocol
- `GET /a2a/tasks/{task_id}` - Get task status

### A2A Task Format

```json
{
  "message": "Analyze sales data: Q1: 100k, Q2: 120k, Q3: 115k, Q4: 140k",
  "context_id": "conversation-123",
  "metadata": {
    "task_id": "task-456",
    "data": {
      "quarters": ["Q1", "Q2", "Q3", "Q4"],
      "sales": [100000, 120000, 115000, 140000]
    }
  }
}
```

### Response Format

```json
{
  "status": "completed",
  "result": {
    "analysis": "Detailed analysis text...",
    "insights": ["Growth trend identified", "Q3 showed slight decline"],
    "metrics": {
      "calculated": {
        "mean": 118750,
        "median": 117500,
        "std_dev": 16520.2
      }
    },
    "visualizations": [
      {
        "type": "line_chart",
        "description": "Quarterly sales trend",
        "x_axis": "Quarter",
        "y_axis": "Sales (k)"
      }
    ],
    "recommendations": [
      "Investigate Q3 decline",
      "Capitalize on Q4 momentum"
    ]
  }
}
```

## Integration with Orchestrator

The Orchestrator Agent automatically delegates analytics tasks when it detects keywords like:
- analyze, analysis
- data, metrics
- visualize, visualization
- report, statistics
- trend, pattern
- compare, correlation

## Testing

```bash
# Unit test
python agents/test_analytics_agent.py

# Integration test
python agents/test_analytics_integration.py
```

## Configuration

Environment variables:
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `REDIS_URL` - Redis connection for context storage
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR)
- `PORT` - Port to run the service on (default: 8003)

## Architecture

The Analytics Agent follows the same architecture as other specialized agents:

1. **PydanticAI Agent Core**: Handles LLM interactions and prompting
2. **A2A Protocol Support**: Enables agent-to-agent communication
3. **Context Store Integration**: Persists task states and results
4. **FastAPI Service**: Provides HTTP endpoints for integration
5. **Built-in Analytics**: Uses Python's statistics library for calculations

## Development

### Adding New Capabilities

1. Update the agent instructions in `__init__`
2. Add extraction methods for new data types
3. Update `get_capabilities()` method
4. Add tests for new features

### Extending Analysis Functions

The agent uses several helper methods for data extraction:
- `_extract_insights()` - Identifies key insights from analysis
- `_extract_metrics()` - Calculates statistical measures
- `_extract_visualization_specs()` - Recommends charts
- `_extract_recommendations()` - Generates action items

## Troubleshooting

### Common Issues

1. **Agent not responding**: Check Redis connection and OpenAI API key
2. **No insights generated**: Ensure input data is properly formatted
3. **Docker networking**: Verify container names in docker-compose

### Logging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python -m agents.analytics_agent
```

## License

Part of the Agentic Stack MVP project.