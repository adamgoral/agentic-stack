# Tech Context

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language for backend
- **FastAPI**: Web framework for API endpoints
- **PydanticAI**: Agent framework with protocol support
- **Redis**: State storage and caching
- **PostgreSQL**: Database with "agent" database created
- **Docker/Docker Compose**: Containerization and orchestration

### Frontend Stack
- **Next.js 14+**: React framework with App Router
- **TypeScript**: Strict type safety configuration
- **CopilotKit**: AG-UI protocol client (fully integrated)
  - @copilotkit/react-core: Provider component
  - @copilotkit/react-ui: Popup UI component
  - @copilotkit/runtime: Backend integration
  - @copilotkit/runtime-client-gql: GraphQL client
  - @ag-ui/agno: AG-UI agent connector
- **Tailwind CSS**: Styling with custom theme and animations
- **React 18.3**: Latest React with concurrent features
- **react-markdown**: Markdown rendering in chat
- **Prism.js**: Syntax highlighting for code blocks

### Protocol Libraries
- **FastA2A**: A2A protocol implementation
- **AG-UI**: Agent-UI protocol (via pydantic-ai-slim[ag-ui])
- **MCP FastMCP**: Model Context Protocol server framework (Note: HTTP/SSE implementation)
- **MCP Protocol**: JSONRPC 2.0 compliant - servers must send proper JSONRPC messages

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
- PostgreSQL (or use Docker)
- UV (for Python package management)
```

### Environment Variables
```env
# API Keys (REQUIRED)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
BRAVE_API_KEY=          # For web search MCP server

# Database
DB_PASSWORD=agentpass123
POSTGRES_USER=agent
POSTGRES_PASSWORD=agentpass123
POSTGRES_DB=agent

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
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/ag-ui  # CopilotKit to AG-UI endpoint

# MCP Servers
MCP_PYTHON_EXECUTOR_URL=http://localhost:3002
MCP_WEB_SEARCH_URL=http://localhost:3001

# Monitoring
LOGFIRE_API_KEY=
OTEL_EXPORTER_OTLP_ENDPOINT=jaeger:4317

# Environment
ENV=development
LOG_LEVEL=INFO
DOCKER_ENV=true  # Set in Docker containers
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
- Non-root Docker containers

## Package Management (PRODUCTION IMPLEMENTATION)

### Backend Package Management - FULLY IMPLEMENTED
The backend uses enterprise-grade modern Python packaging:
- **UV**: Fast Python package installer (Rust-based) - 10-100x faster than pip
- **pyproject.toml**: Standard Python project configuration - FULLY CONFIGURED
- **Ruff**: Fast Python linter and formatter (Rust-based) - PRODUCTION RULES

The backend `pyproject.toml` includes:
- Complete project metadata with proper classifiers
- Comprehensive dependency management with version pinning
- Development tool configurations (ruff, pytest, mypy, bandit)
- Optional dependency groups for development and documentation
- Production-grade linting rules with 200+ checks
- Security scanning integration
- Test configuration with async support
- Type checking configuration with strict mode

### Frontend Package Management
The frontend uses standard Node.js tooling:
- **npm**: Package management
- **package.json**: Dependency configuration
- **TypeScript**: Type checking and compilation
- **ESLint**: Linting
- **Next.js**: Build tooling

## Dependencies

### Python Dependencies (backend/pyproject.toml)
```
# Core Framework
pydantic-ai[all]>=0.4.11
fasta2a>=0.2.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
starlette>=0.37.0

# AI Model Providers
openai>=1.35.0
anthropic>=0.25.0

# MCP Support (Note: prefix parameter removed from client initialization)
# MCP servers must send JSONRPC 2.0 compliant messages
mcp>=0.1.0
httpx>=0.27.0

# Storage & Caching
redis>=5.0.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# State Management
pydantic>=2.7.0
pydantic-settings>=2.3.0

# Monitoring & Observability
opentelemetry-api>=1.24.0
opentelemetry-sdk>=1.24.0
opentelemetry-instrumentation-fastapi>=0.45b0
opentelemetry-instrumentation-httpx>=0.45b0
opentelemetry-instrumentation-redis>=0.45b0
opentelemetry-exporter-otlp>=1.24.0
logfire>=0.30.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
python-multipart>=0.0.9
aiofiles>=23.2.0

# Testing
pytest>=8.2.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
httpx>=0.27.0
faker>=25.0.0
```

### MCP Server Dependencies
```
# MCP Python Executor & Web Search
fastmcp>=2.11.1
httpx>=0.25.0
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
    "@copilotkit/runtime": "^1.0.0",
    "@copilotkit/runtime-client-gql": "^1.0.0",
    "@ag-ui/agno": "^0.1.0",
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

### Docker Commands (PRODUCTION READY)
```bash
# Build and run all 9 services (UV-based build) - FULLY FUNCTIONAL
docker compose up --build -d

# View logs for any service
docker compose logs -f backend
docker compose logs -f research-agent
docker compose logs -f code-agent
docker compose logs -f analytics-agent
docker compose logs -f mcp-web-search
docker compose logs -f mcp-python-executor

# Rebuild specific services after changes
docker compose build backend
docker compose up -d backend

# Check status of all services
docker compose ps

# Database access
docker exec -it postgres psql -U agent -d agent

# Stop and clean up
docker compose down

# Note: All builds use UV package manager with pyproject.toml
# UV provides 10-100x faster dependency resolution than pip
# All import paths fixed and working in Docker environment
# PostgreSQL "agent" database created automatically
```

### Development Commands (CLEAN ARCHITECTURE)
```bash
# Backend development with UV and Clean Architecture
cd backend
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
# Install dependencies with development extras
uv pip install -e ".[dev]"
# Run the main orchestrator backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run individual agents with organized startup scripts
python scripts/run_research_agent.py    # Research agent on port 8001
python scripts/run_code_agent.py        # Code agent on port 8002  
python scripts/run_analytics_agent.py   # Analytics agent on port 8003

# Code quality tools (CONFIGURED FOR PRODUCTION)
ruff format .       # Format with production rules
ruff check .        # Lint with 200+ production rules
ruff check --fix .  # Auto-fix linting issues
pytest tests/       # Run organized test suite (unit/integration/e2e)
mypy src/           # Type checking on Clean Architecture source
bandit -r src/      # Security scanning on source code

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
# Run all tests from backend directory
cd backend
pytest tests/

# Run specific test file
pytest tests/test_e2e_comprehensive.py

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Integration tests
docker-compose -f docker-compose.test.yml up

# API testing
curl http://localhost:8000/health

# MCP server testing
bash tests/test_mcp_curl.sh
bash tests/test_mcp_python_executor.sh
```

## Configuration Management

### Service Discovery
- Environment variables for service URLs
- Docker networking for internal communication
- Health check endpoints for monitoring

### Service Initialization
- All services in main.py initialized with repository dependencies
- OrchestratorService, AgentService, TaskService, ConversationService operational
- Dependency injection pattern with RedisRepository

### MCP Client Configuration
- **Important**: Do not use unsupported parameters like `prefix`
- Proper initialization: `mcp_client = MCPClient(server_params=...)`
- Both web search and Python executor servers accessible via HTTP/SSE
- **JSONRPC Compliance**: Servers must send JSONRPC 2.0 messages with proper format
- **Message Structure**: Initial response with protocol version, tools list with inputSchema

### Database Configuration
- PostgreSQL "agent" database created automatically
- Connection string: `postgresql://agent:agentpass123@postgres:5432/agent`
- Async connection pooling with asyncpg

### Feature Flags (Future)
- Environment-based configuration
- Runtime feature toggles
- A/B testing support