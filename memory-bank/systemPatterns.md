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

### Clean Architecture Organization
```
agentic-stack/
├── backend/                    # Core backend services
│   ├── src/                   # Source code following Clean Architecture
│   │   ├── domain/            # Domain layer (pure business logic)
│   │   │   ├── entities/      # Core business entities
│   │   │   ├── events/        # Domain events
│   │   │   └── exceptions/    # Domain-specific exceptions
│   │   ├── application/       # Application layer (use cases)
│   │   │   ├── services/      # Application services
│   │   │   ├── commands/      # Command handlers (CQRS)
│   │   │   └── queries/       # Query handlers (CQRS)
│   │   ├── infrastructure/    # Infrastructure layer
│   │   │   ├── agents/        # Agent implementations
│   │   │   ├── mcp/          # MCP server integrations
│   │   │   ├── persistence/   # Data persistence (Redis)
│   │   │   └── protocols/     # Protocol adapters (A2A, AG-UI)
│   │   ├── api/               # API layer
│   │   │   └── v1/           # API version 1
│   │   │       ├── endpoints/ # REST endpoints
│   │   │       └── dependencies/ # FastAPI dependencies
│   │   └── core/              # Cross-cutting concerns
│   │       ├── config.py      # Configuration management
│   │       ├── logging.py     # Logging setup
│   │       └── monitoring.py  # Observability
│   ├── tests/                 # Test organization
│   │   ├── unit/             # Fast, isolated tests
│   │   ├── integration/      # Service integration tests
│   │   └── e2e/             # End-to-end tests
│   ├── _legacy_backup/        # Previous implementation backup
│   ├── scripts/              # Utility scripts
│   ├── main.py               # Backward compatibility layer
│   └── pyproject.toml        # Backend package configuration
├── frontend/                  # Next.js application
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   ├── types/               # TypeScript types
│   └── package.json         # Frontend dependencies
├── docs/                     # All documentation
│   ├── API_KEYS_SETUP.md
│   ├── MVP_DESIGN.md
│   ├── E2E_TEST_REPORT.md
│   └── ...
├── memory-bank/              # Project memory for Claude
├── docker/                   # Docker configurations
└── docker-compose.yml
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

### Development Tools
- **UV**: Fast Python package management (Rust-based)
  - Installed globally in Docker containers at /usr/local/bin
  - Used with `--system` flag to install to system Python
  - Replaces pip for faster dependency resolution
- **Ruff**: Fast Python linting and formatting (Rust-based)
- **pytest**: Testing with async support and coverage
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning

### Docker Build Process
1. Install system dependencies (gcc, g++, curl)
2. Install UV package manager globally
3. Copy pyproject.toml for dependency caching
4. Install dependencies with `uv pip install --system --no-cache .`
5. Copy application code
6. Switch to non-root user for security