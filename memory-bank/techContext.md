# Tech Context

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language for backend
- **FastAPI**: Web framework for API endpoints
- **PydanticAI**: Agent framework with protocol support
- **Redis**: State storage and caching
- **Docker/Docker Compose**: Containerization and orchestration

### Frontend Stack
- **Next.js 14**: React framework
- **TypeScript**: Type safety for frontend
- **CopilotKit**: AG-UI protocol client
- **Tailwind CSS**: Styling framework

### Protocol Libraries
- **FastA2A**: A2A protocol implementation
- **AG-UI**: Agent-UI protocol (via pydantic-ai-slim[ag-ui])
- **MCP FastMCP**: Model Context Protocol server framework

### Observability
- **OpenTelemetry**: Distributed tracing
- **Logfire**: PydanticAI-specific monitoring
- **Structured Logging**: JSON-formatted logs

## Development Setup

### Prerequisites
```bash
# Required tools
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Redis (or use Docker)
```

### Environment Variables
```env
# API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Service URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# MCP Servers
MCP_PYTHON_EXECUTOR_URL=http://localhost:8001
MCP_WEB_SEARCH_URL=http://localhost:8002

# Monitoring
LOGFIRE_API_KEY=
OTEL_EXPORTER_OTLP_ENDPOINT=
```

## Technical Constraints

### Performance
- Response streaming required for real-time feedback
- Sub-second latency for agent delegation
- Connection pooling for Redis operations

### Scalability
- Stateless backend design
- Horizontal scaling capability
- Message queue ready architecture

### Security
- Sandboxed code execution
- Input sanitization
- Rate limiting on endpoints

## Dependencies

### Python Dependencies (backend/requirements.txt)
```
pydantic-ai-slim[a2a,ag-ui]>=0.1.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
redis>=5.0.0
httpx>=0.25.0
python-dotenv>=1.0.0
opentelemetry-api>=1.29.0
opentelemetry-sdk>=1.29.0
opentelemetry-instrumentation-fastapi>=0.51b0
logfire>=2.0.0
mcp-server-fastmcp>=0.1.0
```

### Node Dependencies (frontend/package.json)
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "@copilotkit/react-core": "latest",
    "@copilotkit/react-ui": "latest"
  }
}
```

## Tool Usage Patterns

### Docker Commands
```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after changes
docker-compose build backend
docker-compose up -d backend
```

### Development Commands
```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm install
npm run dev
```

### Testing Patterns
```bash
# Unit tests (future)
pytest tests/

# Integration tests
docker-compose -f docker-compose.test.yml up

# API testing
curl http://localhost:8000/health
```

## Configuration Management

### Service Discovery
- Environment variables for service URLs
- Docker networking for internal communication
- Health check endpoints for monitoring

### Feature Flags (Future)
- Environment-based configuration
- Runtime feature toggles
- A/B testing support