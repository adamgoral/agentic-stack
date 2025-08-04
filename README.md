# Agentic Stack MVP

A comprehensive multi-agent system leveraging PydanticAI's three core protocols: **A2A** (Agent-to-Agent), **AG-UI** (Agent-UI), and **MCP** (Model Context Protocol).

## Overview

This MVP demonstrates a production-ready agentic architecture where:
- **AG-UI Protocol** handles all frontend-backend communication with real-time streaming
- **A2A Protocol** enables seamless agent collaboration with context preservation
- **MCP Protocol** provides standardized access to external tools and services

## Architecture

```
Frontend (React/Next.js) 
    ↓ AG-UI (SSE)
Orchestrator Agent
    ↓ A2A Protocol
Specialized Agents (Research, Code, Analytics)
    ↓ MCP Protocol
External Tools (Web Search, Python Executor, Database)
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Redis (or use Docker)
- API Keys (OpenAI/Anthropic)

### Setup

1. **Clone and Configure**
```bash
cd agentic-stack
cp .env.example .env
# Edit .env with your API keys
```

2. **Start with Docker Compose**
```bash
docker-compose up -d
```

3. **Or Run Locally**
```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

4. **Access the Application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

### Multi-Agent Collaboration
- **Orchestrator Agent**: Coordinates tasks and synthesizes results
- **Research Agent**: Web research and information gathering
- **Code Agent**: Code generation and testing
- **Analytics Agent**: Data analysis and visualization

### Protocol Integration
- **AG-UI**: Real-time streaming UI updates via Server-Sent Events
- **A2A**: Async agent communication with conversation continuity
- **MCP**: Tool access through standardized interfaces

### Production Features
- Redis-based state management
- OpenTelemetry tracing
- Comprehensive error handling
- Docker deployment ready
- Scalable microservices architecture

## Example Usage

Ask the system: *"Research best practices for rate limiting in microservices and generate a Python implementation with Redis"*

The system will:
1. Decompose the task into research and coding subtasks
2. Delegate research to the Research Agent via A2A
3. Use MCP to search the web for information
4. Send requirements to Code Agent via A2A
5. Generate and test code using MCP Python executor
6. Stream results back to UI via AG-UI

## API Endpoints

### Core Endpoints
- `POST /ag-ui/run` - Execute agent with streaming response
- `GET /health` - System health check
- `GET /agents` - List available agents
- `GET /tasks/{task_id}` - Get task status

### A2A Endpoints
- `/a2a/tasks` - A2A task management
- `/a2a/contexts/{id}` - Conversation contexts

## Configuration

Edit `.env` file for:
- API keys (OpenAI, Anthropic, Brave)
- Model preferences
- Performance tuning
- Observability settings

## Monitoring

Optional observability with:
- OpenTelemetry (Jaeger)
- Logfire for PydanticAI
- Structured logging

Enable with:
```bash
docker-compose --profile observability up
```

## Development

### Project Structure
```
agentic-stack/
├── backend/           # Python backend
│   ├── agents/       # Agent implementations
│   ├── protocols/    # A2A, AG-UI, MCP handlers
│   ├── models/       # Pydantic models
│   └── storage/      # Context persistence
├── frontend/         # Next.js frontend
├── docker/          # Docker configurations
└── tests/           # Test suites
```

### Testing
```bash
# Run tests
cd backend
pytest tests/

# With coverage
pytest --cov=. tests/
```

## License

MIT

## Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

## Support

For issues and questions, please use GitHub Issues.