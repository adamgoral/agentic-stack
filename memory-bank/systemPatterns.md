# System Patterns

## Architecture Overview

### Microservices Pattern
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│    Redis    │
│  (Next.js)  │HTTP │  (FastAPI)   │     │   (State)   │
│ +CopilotKit │     │   AG-UI      │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
        │                   │
        │           ┌───────┴────────┐
        ▼           ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ /api/copilot │  │  MCP Servers │  │  A2A Agents  │
│   (proxy)    │  │   (Tools)    │  │  (Workers)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Key Design Patterns

### 1. Protocol Adapter Pattern
Each protocol (A2A, AG-UI, MCP) has dedicated adapters:
- `backend/protocols/a2a_manager.py`: Manages A2A communication
- `backend/protocols/ag_ui_handler.py`: AG-UI message formatting and validation
- `backend/main.py`: AG-UI endpoint handlers
- `backend/agents/orchestrator.py`: MCP client connections
- `frontend/app/api/copilotkit/route.ts`: CopilotKit to AG-UI proxy
- `frontend/components/providers/CopilotProvider.tsx`: UI integration

### 2. Dependency Injection
- Use of `StateDeps` for AG-UI state management
- Redis client passed as dependency
- MCP servers registered as toolsets

### 3. Event Streaming
- Server-Sent Events for real-time updates
- Async generators for streaming responses
- Message queuing for inter-agent communication

### 4. Context Preservation
- Redis-based context store
- Context IDs for conversation continuity
- Message history management

## Component Relationships

### Orchestrator Agent (Core)
- **Role**: Central coordinator
- **Responsibilities**:
  - Task decomposition
  - Agent delegation
  - Result aggregation
  - State management
- **Protocols Used**: All three (A2A, AG-UI, MCP)

### Specialized Agents
- **Research Agent**: Information gathering via MCP web search
- **Code Agent**: Code generation/validation via MCP Python executor
- **Analytics Agent**: Data analysis using built-in Python capabilities
- **Communication**: A2A protocol with orchestrator
- **Pattern**: All agents follow identical implementation structure for consistency

### MCP Servers
- **Python Executor**: Sandboxed code execution (Port 3002)
- **Web Search**: Information retrieval (Port 3001)
- **Transport**: HTTP/SSE for remote agent connections
- **Implementation**: FastAPI servers with SSE endpoints at `/sse`
- **Tool Execution**: HTTP POST to `/tools/{tool_name}`
- **Health Monitoring**: GET `/health` endpoints

## Critical Implementation Paths

### 1. Request Flow
```python
User (CopilotKit UI) → /api/copilotkit → AgnoAgent → AG-UI Endpoint 
→ Orchestrator.run() → Task Analysis → A2A Delegation → MCP Tool Calls 
→ Result Assembly → AG-UI Response → CopilotKit → User
```

### 2. State Management
```python
StateDeps[AppState] → Redis Storage → Context Persistence
→ Message History → Conversation Continuity
```

### 3. Error Handling
- Try-catch blocks at protocol boundaries
- Graceful degradation for tool failures
- Error events streamed to frontend

## Scaling Patterns

### Horizontal Scaling
- Stateless backend services
- Redis for shared state
- Load balancer ready architecture

### Vertical Scaling
- Async/await for concurrent operations
- Connection pooling for Redis
- Lazy loading of MCP servers

## Security Patterns

### Sandboxing
- MCP Python executor with restricted globals
- Network isolation for tool servers
- Input validation at all boundaries

### Authentication (Future)
- JWT tokens for API access
- Rate limiting per user
- Audit logging for all operations

## Project Structure

### Clean Architecture Implementation (PRODUCTION READY)
```
agentic-stack/
├── backend/                    # Core backend services
│   ├── src/                   # Clean Architecture layers (IMPLEMENTED)
│   │   ├── domain/            # Domain layer - pure business logic
│   │   │   ├── entities/      # Agent, Task, Conversation, Message entities
│   │   │   ├── events/        # Domain events for CQRS
│   │   │   └── exceptions/    # Domain-specific exceptions
│   │   ├── application/       # Application layer - use cases
│   │   │   ├── services/      # OrchestratorService, AgentService, etc.
│   │   │   ├── commands/      # Command handlers (CQRS ready)
│   │   │   └── queries/       # Query handlers (CQRS ready)
│   │   ├── infrastructure/    # Infrastructure layer - external integrations
│   │   │   ├── agents/        # Agent implementations with task manager
│   │   │   ├── mcp/          # MCP server integrations
│   │   │   ├── persistence/   # Redis repositories with base patterns
│   │   │   └── protocols/     # A2A, AG-UI protocol adapters
│   │   ├── api/               # API layer - REST endpoints
│   │   │   └── v1/           # API version 1 with proper versioning
│   │   │       ├── endpoints/ # FastAPI endpoints by domain
│   │   │       └── dependencies/ # Dependency injection patterns
│   │   └── core/              # Cross-cutting concerns
│   │       ├── config.py      # Pydantic Settings configuration
│   │       ├── logging.py     # Structured logging setup
│   │       └── monitoring.py  # OpenTelemetry observability
│   ├── tests/                 # Comprehensive test organization
│   │   ├── unit/             # Fast, isolated unit tests
│   │   ├── integration/      # Service integration tests
│   │   └── e2e/             # End-to-end system tests
│   ├── run_research_agent.py  # Simplified agent startup scripts
│   ├── run_code_agent.py      # Direct execution from backend root
│   ├── run_analytics_agent.py # No complex paths needed
│   ├── main.py               # Backward compatibility layer
│   └── pyproject.toml        # Modern Python package configuration (UV)
├── frontend/                  # Next.js 14+ application
│   ├── app/                 # App router with TypeScript
│   ├── components/          # React components with proper separation
│   ├── lib/                 # Utilities and client libraries
│   ├── types/               # TypeScript type definitions
│   └── package.json         # Frontend dependencies
├── docs/                     # Centralized documentation
│   ├── API_KEYS_SETUP.md    # Production setup guide
│   ├── MIGRATION_GUIDE.md   # Architecture migration notes
│   ├── E2E_TEST_REPORT.md   # Comprehensive test results
│   └── REORGANIZATION_SUMMARY.md # Clean Architecture details
├── memory-bank/              # Project memory for Claude
├── docker/                   # Docker configurations
└── docker-compose.yml        # 9-service orchestration
```

### Clean Architecture Layers

#### Domain Layer (src/domain/)
- **Purpose**: Core business logic, independent of frameworks
- **Contents**: 
  - Entities (Agent, Task, Conversation, Message)
  - Value objects
  - Domain events
  - Business rules and invariants
- **Dependencies**: None (pure Python)

#### Application Layer (src/application/)
- **Purpose**: Use case orchestration
- **Contents**:
  - Application services (OrchestratorService, AgentService, etc.)
  - DTOs and mappers
  - Command/Query handlers (CQRS pattern ready)
- **Dependencies**: Domain layer only

#### Infrastructure Layer (src/infrastructure/)
- **Purpose**: External system integrations
- **Contents**:
  - Agent implementations
  - MCP server clients
  - Redis repositories
  - Protocol implementations
- **Dependencies**: Application and Domain layers

#### API Layer (src/api/)
- **Purpose**: External interface (REST API)
- **Contents**:
  - FastAPI endpoints
  - Request/Response models
  - API versioning
  - Middleware
- **Dependencies**: All layers

### Development Tools (PRODUCTION READY)
- **UV**: Fast Python package management (Rust-based) - IMPLEMENTED
  - Installed globally in Docker containers at /usr/local/bin
  - Used with `--system` flag for system-wide Python packages
  - 10-100x faster than pip for dependency resolution
  - Full pyproject.toml support with modern standards
- **Ruff**: Fast Python linting and formatting (Rust-based) - CONFIGURED
  - Comprehensive linting rules for production code quality
  - Auto-formatting with consistent style enforcement
  - Security-focused rules and best practice enforcement
- **pytest**: Testing with async support and coverage - ORGANIZED
  - Structured test directories: unit/, integration/, e2e/
  - Async test support for agent and protocol testing
  - Coverage reporting and quality gates
- **mypy**: Static type checking - CONFIGURED
  - Strict type checking for production safety
  - Integration with domain models and entities
- **bandit**: Security vulnerability scanning - INTEGRATED
  - Automated security analysis in development pipeline
  - Production-ready security practices

### Docker Build Process (OPTIMIZED FOR PRODUCTION)
1. Install system dependencies (gcc, g++, curl) for compilation
2. Install UV package manager globally at /usr/local/bin
3. Copy pyproject.toml for Docker layer caching optimization
4. Install dependencies with `uv pip install --system --no-cache .`
5. Copy Clean Architecture source code structure
6. Set proper file permissions and ownership
7. Switch to non-root user for container security
8. Configure health checks for service monitoring
9. All 9 services build successfully with optimized layers