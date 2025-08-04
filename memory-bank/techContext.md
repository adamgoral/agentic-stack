# Tech Context

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language for backend
- **FastAPI**: Web framework for API endpoints
- **PydanticAI**: Agent framework with protocol support
- **Redis**: State storage and caching
- **Docker/Docker Compose**: Containerization and orchestration

### Frontend Stack
- **Next.js 14+**: React framework with App Router
- **TypeScript**: Strict type safety configuration
- **CopilotKit**: AG-UI protocol client (packages installed)
- **Tailwind CSS**: Styling with custom theme and animations
- **React 18.3**: Latest React with concurrent features
- **react-markdown**: Markdown rendering in chat
- **Prism.js**: Syntax highlighting for code blocks

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
# API Keys (REQUIRED)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
BRAVE_API_KEY=          # For web search MCP server

# Database
DB_PASSWORD=agentpass123

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379  # Docker network URL

# Service URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# MCP Servers
MCP_PYTHON_EXECUTOR_URL=http://localhost:3002
MCP_WEB_SEARCH_URL=http://localhost:3001

# Monitoring
LOGFIRE_API_KEY=
OTEL_EXPORTER_OTLP_ENDPOINT=jaeger:4317

# Environment
ENV=development
LOG_LEVEL=INFO
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
    "next": "^14.2.21",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@copilotkit/react-core": "^1.0.0",
    "@copilotkit/react-ui": "^1.0.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0",
    "react-syntax-highlighter": "^15.6.1",
    "lucide-react": "^0.469.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0"
  },
  "devDependencies": {
    "typescript": "^5.7.3",
    "@types/react": "^18.3.18",
    "@types/node": "^22.10.6",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.5.1",
    "eslint": "^8.57.1",
    "eslint-config-next": "^14.2.21"
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
npm run dev         # Development server on port 3000
npm run build       # Production build
npm run type-check  # TypeScript validation
npm run lint        # ESLint checks
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