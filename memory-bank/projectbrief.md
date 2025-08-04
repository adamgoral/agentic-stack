# Project Brief

## Project Name
Agentic Stack MVP

## Purpose
Build a minimal but comprehensive multi-agent system that demonstrates the full power of PydanticAI's protocol ecosystem (A2A, AG-UI, MCP) working together in a production-ready architecture.

## Core Requirements

### Functional Requirements
1. **Multi-Agent Orchestration**: Implement an orchestrator agent that can decompose tasks and delegate to specialized agents
2. **Protocol Integration**: Fully utilize all three PydanticAI protocols:
   - A2A for agent-to-agent communication
   - AG-UI for frontend streaming interactions
   - MCP for external tool integration
3. **State Management**: Persistent state across agent interactions using Redis
4. **Real-time Updates**: Stream agent progress to frontend via Server-Sent Events
5. **Tool Access**: Connect to external tools (web search, Python execution) via MCP

### Technical Requirements
- FastAPI backend with async/await patterns
- Redis for context storage and state persistence
- Docker Compose for microservices orchestration
- OpenTelemetry for observability
- Type-safe models with Pydantic
- Modular, extensible architecture

## Success Criteria
1. Agents can successfully communicate and delegate tasks via A2A
2. Frontend receives real-time updates from agents via AG-UI
3. Agents can access external tools through MCP servers
4. System handles complex multi-step workflows
5. Architecture is scalable and production-ready

## Constraints
- Keep MVP minimal but functional
- Use only PydanticAI's official protocols
- Ensure all components are containerized
- Maintain clear separation of concerns

## Target Users
- AI/ML engineers building agent systems
- Developers exploring PydanticAI capabilities
- Teams evaluating multi-agent architectures