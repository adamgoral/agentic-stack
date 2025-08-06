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

### Organization
```
agentic-stack/
├── backend/           # Core backend services
│   ├── agents/       # Agent implementations
│   ├── protocols/    # Protocol adapters
│   ├── storage/      # State management
│   ├── models/       # Data models
│   ├── mcp_servers/  # MCP server implementations
│   ├── tests/        # All test files
│   └── pyproject.toml # Backend package configuration
├── frontend/         # Next.js application
│   ├── app/         # App router pages
│   ├── components/  # React components
│   ├── lib/         # Utilities
│   ├── types/       # TypeScript types
│   └── package.json # Frontend dependencies
├── docs/            # All documentation
│   ├── API_KEYS_SETUP.md
│   ├── MVP_DESIGN.md
│   ├── E2E_TEST_REPORT.md
│   └── ...
├── memory-bank/     # Project memory for Claude
├── docker/          # Docker configurations
└── docker-compose.yml
```

### Development Tools
- **UV**: Fast Python package management (Rust-based)
- **Ruff**: Fast Python linting and formatting (Rust-based)
- **pytest**: Testing with async support and coverage
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning