# Agentic Tech Stack MVP Design
## Leveraging PydanticAI's A2A, AG-UI, and MCP Protocols

---

## 1. Architecture Overview

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         React/Next.js with CopilotKit UI                 │   │
│  │              (AG-UI Protocol - SSE)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                         AG-UI Protocol
                      (Server-Sent Events)
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Gateway Agent Layer                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Orchestrator Agent (Main Controller)            │   │
│  │         - User interaction via AG-UI                     │   │
│  │         - Task delegation via A2A                        │   │
│  │         - Tool access via MCP                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                         A2A Protocol
                     (Agent-to-Agent)
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Specialized Agent Layer                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐    │
│  │  Research  │  │   Code     │  │      Analytics         │    │
│  │   Agent    │  │  Assistant │  │       Agent            │    │
│  │            │  │   Agent    │  │                        │    │
│  └────────────┘  └────────────┘  └────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                         MCP Protocol
                    (Tool & Service Access)
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Layer (MCP)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐    │
│  │    Web     │  │   Python   │  │    Database            │    │
│  │   Search   │  │  Executor  │  │    Connector           │    │
│  │   Server   │  │   Server   │  │     Server             │    │
│  └────────────┘  └────────────┘  └────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **User → Frontend**: User interacts with React UI
2. **Frontend → Orchestrator**: AG-UI protocol streams events/responses
3. **Orchestrator → Specialized Agents**: A2A protocol for task delegation
4. **Agents → Tools**: MCP protocol for external tool access
5. **Response Flow**: Reverse path with streaming updates

### Protocol Responsibilities

- **AG-UI**: Handles all frontend-backend communication with real-time streaming
- **A2A**: Manages agent collaboration and conversation context
- **MCP**: Provides standardized access to external tools and services

---

## 2. Core Components

### 2.1 Orchestrator Agent (Gateway)
**Responsibilities:**
- Primary user interaction point
- Task decomposition and delegation
- Result aggregation and synthesis
- Context management across sub-agents

**Key Features:**
- Maintains conversation state via AG-UI StateDeps
- Routes tasks to specialized agents via A2A
- Accesses general tools via MCP

### 2.2 Research Agent
**Responsibilities:**
- Web research and information gathering
- Source validation and credibility assessment
- Knowledge synthesis and summarization

**MCP Tools:**
- Web search server (Brave/Google)
- Academic paper retrieval
- Documentation parser

### 2.3 Code Assistant Agent
**Responsibilities:**
- Code generation and analysis
- Debugging and optimization
- Documentation generation

**MCP Tools:**
- Python executor (sandboxed)
- Code formatter
- Static analysis tools

### 2.4 Analytics Agent
**Responsibilities:**
- Data analysis and visualization
- Performance metrics calculation
- Report generation

**MCP Tools:**
- Database connector
- Data visualization server
- Statistical analysis tools

### 2.5 State Management Strategy
```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ConversationState(BaseModel):
    """Shared state across all agents"""
    context_id: str
    user_preferences: Dict[str, Any]
    current_task: Optional[str]
    task_history: List[Dict[str, Any]]
    agent_outputs: Dict[str, Any]
    
class AgentTaskState(BaseModel):
    """Individual agent task state"""
    task_id: str
    agent_name: str
    status: str  # pending, in_progress, completed, failed
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
```

---

## 3. Implementation Plan

### 3.1 Directory Structure
```
agentic-stack/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── AgentStatus.tsx
│   │   │   └── ToolExecutions.tsx
│   │   ├── hooks/
│   │   │   └── useAgentConnection.ts
│   │   └── app/
│   │       └── page.tsx
│   ├── package.json
│   └── next.config.js
│
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── research_agent.py
│   │   ├── code_agent.py
│   │   └── analytics_agent.py
│   │
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── a2a_manager.py
│   │   ├── ag_ui_handler.py
│   │   └── mcp_client.py
│   │
│   ├── mcp_servers/
│   │   ├── web_search/
│   │   │   ├── server.py
│   │   │   └── requirements.txt
│   │   ├── python_executor/
│   │   │   ├── server.py
│   │   │   └── sandbox.py
│   │   └── database_connector/
│   │       ├── server.py
│   │       └── models.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   └── messages.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── task_store.py
│   │   └── context_store.py
│   │
│   ├── main.py
│   └── requirements.txt
│
├── shared/
│   ├── types/
│   │   └── protocol_types.py
│   └── utils/
│       └── validators.py
│
├── docker/
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── Dockerfile.mcp
│
├── config/
│   ├── agents.yaml
│   ├── mcp_servers.yaml
│   └── .env.example
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker-compose.yml
├── README.md
└── pyproject.toml
```

### 3.2 Key Files and Modules

#### backend/main.py
```python
from fastapi import FastAPI
from starlette.responses import StreamingResponse
from pydantic_ai import Agent
from agents.orchestrator import OrchestratorAgent
from protocols.ag_ui_handler import setup_ag_ui_routes
from protocols.a2a_manager import A2AManager

app = FastAPI()

# Initialize orchestrator
orchestrator = OrchestratorAgent()
a2a_manager = A2AManager()

# Setup AG-UI routes
setup_ag_ui_routes(app, orchestrator)

# Setup A2A endpoints
app.mount("/a2a", orchestrator.to_a2a())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### backend/agents/orchestrator.py
```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio, MCPServerSSE
from typing import Optional
from models.state import ConversationState

class OrchestratorAgent:
    def __init__(self):
        # Initialize MCP connections
        self.web_search = MCPServerSSE(
            url="http://localhost:3001/sse",
            prefix="search_"
        )
        
        # Create main agent
        self.agent = Agent(
            'openai:gpt-4o',
            instructions="""You are an orchestrator agent that:
            1. Understands user requests
            2. Delegates tasks to specialized agents
            3. Aggregates and synthesizes results
            4. Maintains conversation context""",
            toolsets=[self.web_search]
        )
        
        # Initialize sub-agents via A2A
        self.research_agent_url = "http://localhost:8001/a2a"
        self.code_agent_url = "http://localhost:8002/a2a"
        self.analytics_agent_url = "http://localhost:8003/a2a"
    
    async def process_request(
        self, 
        message: str, 
        state: ConversationState
    ) -> AsyncGenerator:
        """Process user request with state management"""
        # Implementation details...
        pass
    
    def to_a2a(self):
        """Convert to A2A server"""
        return self.agent.to_a2a()
    
    def to_ag_ui(self):
        """Convert to AG-UI server"""
        return self.agent.to_ag_ui()
```

### 3.3 Dependencies

#### Backend (requirements.txt)
```txt
# Core
pydantic-ai[all]>=0.12.0
fasta2a>=0.2.0
fastapi>=0.100.0
uvicorn[standard]>=0.23.0

# AI Models
openai>=1.0.0
anthropic>=0.25.0

# MCP Support
mcp>=0.1.0

# Storage
redis>=5.0.0
sqlalchemy>=2.0.0
asyncpg>=0.28.0

# Monitoring
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
logfire>=0.30.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
```

#### Frontend (package.json)
```json
{
  "name": "agentic-stack-frontend",
  "version": "1.0.0",
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "@copilotkit/react-core": "^1.0.0",
    "@copilotkit/react-ui": "^1.0.0",
    "eventsource-parser": "^1.0.0",
    "tailwindcss": "^3.3.0"
  }
}
```

### 3.4 Configuration

#### config/agents.yaml
```yaml
agents:
  orchestrator:
    model: "openai:gpt-4o"
    temperature: 0.7
    max_tokens: 2000
    
  research:
    model: "openai:gpt-4o"
    temperature: 0.3
    tools:
      - web_search
      - document_parser
      
  code_assistant:
    model: "anthropic:claude-3-opus"
    temperature: 0.2
    tools:
      - python_executor
      - code_formatter
      
  analytics:
    model: "openai:gpt-4o"
    temperature: 0.4
    tools:
      - database_connector
      - visualization_server
```

---

## 4. Protocol Integration Details

### 4.1 A2A Integration (Agent Collaboration)

```python
# backend/protocols/a2a_manager.py
from fasta2a import FastA2A, Storage, Broker, Worker
from typing import Dict, Any
import httpx

class A2AManager:
    def __init__(self):
        self.storage = RedisStorage()
        self.broker = RedisBroker()
        self.clients: Dict[str, httpx.AsyncClient] = {}
    
    async def send_task_to_agent(
        self,
        agent_url: str,
        message: str,
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send task to another agent via A2A"""
        if agent_url not in self.clients:
            self.clients[agent_url] = httpx.AsyncClient()
        
        payload = {
            "message": message,
            "context_id": context_id
        }
        
        response = await self.clients[agent_url].post(
            f"{agent_url}/tasks",
            json=payload
        )
        
        return response.json()
    
    async def get_task_result(
        self,
        agent_url: str,
        task_id: str
    ) -> Dict[str, Any]:
        """Get task result from agent"""
        response = await self.clients[agent_url].get(
            f"{agent_url}/tasks/{task_id}"
        )
        return response.json()
```

### 4.2 AG-UI Integration (Frontend Communication)

```python
# backend/protocols/ag_ui_handler.py
from pydantic_ai import Agent
from pydantic_ai.ag_ui import StateDeps
from starlette.responses import StreamingResponse
from models.state import ConversationState
import json

def setup_ag_ui_routes(app, orchestrator: OrchestratorAgent):
    """Setup AG-UI routes for frontend communication"""
    
    @app.post("/ag-ui/run")
    async def run_agent(request: Request):
        """Handle AG-UI requests with SSE streaming"""
        data = await request.json()
        
        # Create state dependencies
        state = ConversationState(
            context_id=data.get("context_id"),
            user_preferences=data.get("preferences", {}),
            current_task=data.get("message")
        )
        
        async def event_generator():
            async with orchestrator.agent as agent:
                # Stream AG-UI events
                async for event in agent.run_ag_ui(
                    data["message"],
                    state_deps=StateDeps(state=state)
                ):
                    yield f"data: {json.dumps(event)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
```

### 4.3 MCP Integration (Tool Access)

```python
# backend/protocols/mcp_client.py
from pydantic_ai.mcp import MCPServerStdio, MCPServerSSE
from typing import List, Dict, Any

class MCPToolManager:
    def __init__(self):
        self.servers = {}
        
    def register_stdio_server(
        self,
        name: str,
        command: str,
        args: List[str]
    ):
        """Register stdio-based MCP server"""
        self.servers[name] = MCPServerStdio(
            command,
            args=args,
            prefix=f"{name}_"
        )
    
    def register_sse_server(
        self,
        name: str,
        url: str
    ):
        """Register SSE-based MCP server"""
        self.servers[name] = MCPServerSSE(
            url=url,
            prefix=f"{name}_"
        )
    
    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        args: Dict[str, Any]
    ):
        """Execute tool on MCP server"""
        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server {server_name} not found")
        
        async with server:
            result = await server.call_tool(tool_name, args)
            return result
```

---

## 5. Example Use Case: Research & Code Generation Workflow

### Scenario
User requests: "Research the latest best practices for implementing rate limiting in microservices and generate a Python implementation with Redis"

### Step-by-Step Flow

#### Step 1: User Input (Frontend → Orchestrator via AG-UI)
```typescript
// Frontend component
const response = await fetch('/ag-ui/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Research rate limiting best practices...",
    context_id: session.context_id
  })
});

const reader = response.body.getReader();
// Process SSE stream...
```

#### Step 2: Task Decomposition (Orchestrator)
```python
# Orchestrator decomposes task
subtasks = [
    {
        "agent": "research",
        "task": "Find latest rate limiting patterns and algorithms"
    },
    {
        "agent": "research", 
        "task": "Identify Redis-based implementations"
    },
    {
        "agent": "code_assistant",
        "task": "Generate Python rate limiter with Redis"
    }
]
```

#### Step 3: Research Phase (Orchestrator → Research Agent via A2A)
```python
# Send to research agent
research_result = await a2a_manager.send_task_to_agent(
    agent_url="http://localhost:8001/a2a",
    message="Research rate limiting patterns",
    context_id=context_id
)
```

#### Step 4: Tool Execution (Research Agent → MCP Web Search)
```python
# Research agent uses MCP for web search
async with web_search_server:
    search_results = await web_search_server.call_tool(
        "search",
        {"query": "microservices rate limiting 2025"}
    )
```

#### Step 5: Code Generation (Orchestrator → Code Agent via A2A)
```python
# Send requirements to code agent
code_result = await a2a_manager.send_task_to_agent(
    agent_url="http://localhost:8002/a2a",
    message=f"Generate rate limiter based on: {research_findings}",
    context_id=context_id
)
```

#### Step 6: Code Execution (Code Agent → MCP Python Executor)
```python
# Code agent tests implementation
async with python_executor:
    test_result = await python_executor.call_tool(
        "execute",
        {"code": generated_code, "test": True}
    )
```

#### Step 7: Response Synthesis (Orchestrator → Frontend via AG-UI)
```python
# Stream results back to frontend
yield {
    "type": "text_message",
    "content": "Here's your rate limiting implementation..."
}
yield {
    "type": "code_block",
    "language": "python",
    "content": final_code
}
yield {
    "type": "state_update",
    "state": {"task_complete": True}
}
```

### Expected Output
```python
# Generated rate_limiter.py
import redis
import time
from typing import Optional

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation using Redis
    Based on latest microservices best practices
    """
    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "rate_limit",
        max_tokens: int = 100,
        refill_rate: int = 10,
        refill_interval: int = 1
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.refill_interval = refill_interval
    
    async def allow_request(
        self,
        identifier: str,
        tokens_requested: int = 1
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limit
        Returns (allowed, retry_after_seconds)
        """
        # Implementation...
        pass
```

---

## 6. Deployment Strategy

### 6.1 Local Development Setup

#### Prerequisites
```bash
# System requirements
- Python 3.10+
- Node.js 18+
- Redis server
- Docker & Docker Compose

# Environment setup
cp config/.env.example .env
# Edit .env with your API keys
```

#### Start Services
```bash
# 1. Start infrastructure
docker-compose up -d redis postgres

# 2. Start MCP servers
cd backend/mcp_servers/web_search && python server.py --port 3001 &
cd backend/mcp_servers/python_executor && python server.py --port 3002 &

# 3. Start agent servers
cd backend && python -m agents.research_agent --port 8001 &
cd backend && python -m agents.code_agent --port 8002 &
cd backend && python -m agents.analytics_agent --port 8003 &

# 4. Start orchestrator
cd backend && python main.py

# 5. Start frontend
cd frontend && npm run dev
```

### 6.2 Docker Deployment

#### docker-compose.yml
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agentic_stack
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  orchestrator:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://agent:${DB_PASSWORD}@postgres:5432/agentic_stack
    depends_on:
      - redis
      - postgres

  research_agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python -m agents.research_agent --port 8001
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  code_agent:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python -m agents.code_agent --port 8002
    ports:
      - "8002:8002"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  mcp_web_search:
    build:
      context: ./backend/mcp_servers/web_search
    ports:
      - "3001:3001"
    environment:
      - BRAVE_API_KEY=${BRAVE_API_KEY}

  mcp_python_executor:
    build:
      context: ./backend/mcp_servers/python_executor
    ports:
      - "3002:3002"
    security_opt:
      - seccomp:unconfined
    cap_add:
      - SYS_ADMIN

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://orchestrator:8000

volumes:
  redis_data:
  postgres_data:
```

### 6.3 Port Allocations

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| Frontend | 3000 | HTTP | Next.js UI |
| Orchestrator | 8000 | HTTP/SSE | Main API + AG-UI |
| Research Agent | 8001 | HTTP | A2A endpoint |
| Code Agent | 8002 | HTTP | A2A endpoint |
| Analytics Agent | 8003 | HTTP | A2A endpoint |
| MCP Web Search | 3001 | SSE | Search tools |
| MCP Python Exec | 3002 | SSE | Code execution |
| Redis | 6379 | TCP | Cache & broker |
| PostgreSQL | 5432 | TCP | Persistent storage |

### 6.4 Environment Variables

#### .env.example
```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
BRAVE_API_KEY=BSA...

# Database
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://agent:${DB_PASSWORD}@localhost:5432/agentic_stack

# Redis
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOGFIRE_TOKEN=...

# Agent Config
AGENT_TIMEOUT=30
MAX_RETRIES=3
TEMPERATURE=0.7
```

---

## 7. Monitoring & Observability

### OpenTelemetry Integration
```python
# backend/monitoring.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc import trace_exporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        trace_exporter.OTLPSpanExporter(
            endpoint="http://localhost:4317"
        )
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
```

### Logfire Integration
```python
import logfire

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()
```

---

## 8. Testing Strategy

### Unit Tests
```python
# tests/unit/test_orchestrator.py
import pytest
from agents.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_task_decomposition():
    orchestrator = OrchestratorAgent()
    tasks = await orchestrator.decompose_task(
        "Research and implement rate limiting"
    )
    assert len(tasks) > 0
    assert any("research" in t["agent"] for t in tasks)
```

### Integration Tests
```python
# tests/integration/test_a2a_flow.py
@pytest.mark.asyncio
async def test_agent_communication():
    # Test A2A protocol between agents
    pass
```

### E2E Tests
```python
# tests/e2e/test_full_workflow.py
@pytest.mark.asyncio
async def test_research_and_code_generation():
    # Test complete user flow
    pass
```

---

## Summary

This MVP design demonstrates a comprehensive agentic stack that:

1. **Leverages all three protocols**:
   - AG-UI for seamless frontend integration with streaming
   - A2A for multi-agent collaboration with context preservation
   - MCP for standardized tool access

2. **Provides clear separation of concerns**:
   - Orchestrator handles user interaction and coordination
   - Specialized agents focus on specific domains
   - MCP servers provide isolated tool functionality

3. **Supports production requirements**:
   - Scalable architecture with microservices approach
   - Comprehensive monitoring and observability
   - Robust error handling and state management

4. **Enables rapid development**:
   - Clear directory structure and modular design
   - Standard protocols reduce integration complexity
   - Docker deployment for consistent environments

The system is designed to be minimal enough to build quickly while showcasing the full power of the PydanticAI protocol ecosystem working in harmony.