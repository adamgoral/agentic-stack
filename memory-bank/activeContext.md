# Active Context

## Current Work Focus
All Docker services are now running successfully. The full stack is operational with frontend accessible at http://localhost:3000. Ready for functionality testing and agent implementation.

## Recent Changes

### Completed
1. **Architecture Design** (MVP_DESIGN.md)
   - Comprehensive 8-section design document
   - Visual diagrams for system architecture
   - Protocol integration specifications

2. **Backend Implementation**
   - FastAPI server with AG-UI endpoints
   - Orchestrator agent with all three protocols
   - A2A manager for agent communication
   - Redis-based context storage
   - Monitoring setup with OpenTelemetry

3. **MCP Servers**
   - Python executor with sandboxed execution
   - Web search server with mock implementation
   - Dockerfiles for both servers

4. **Infrastructure**
   - Docker Compose configuration
   - Multi-service orchestration
   - Environment configuration template

5. **Memory Bank Initialization**
   - CLAUDE.md with Memory Bank structure
   - All core memory files created
   - Project documentation established

6. **Frontend Implementation**
   - Next.js 14+ with App Router setup complete
   - TypeScript configuration with strict typing
   - TailwindCSS with custom theme and animations
   - Complete project structure with components
   - Chat interface and dashboard pages created
   - API/WebSocket clients prepared
   - All dependencies including CopilotKit installed

7. **Docker Infrastructure**
   - Frontend Dockerfile created
   - Environment configuration template (.env)
   - All services configured in docker-compose.yml

8. **CopilotKit Integration** (COMPLETED)
   - API route created at /api/copilotkit/route.ts
   - AgnoAgent configured to connect to AG-UI backend
   - CopilotProvider component created with proper client/server separation
   - Layout updated to wrap app with CopilotKit provider
   - CopilotPopup integrated with custom instructions
   - Environment variables configured for backend URL
   - Full TypeScript support and Next.js 14+ best practices
   - Documentation created for integration

9. **Docker Dependency Fixes** (COMPLETED)
   - Fixed pydantic-ai version constraint from >=0.12.0 to >=0.4.11
   - Replaced mcp-server-fastmcp with correct fastmcp>=2.11.1 package
   - Updated all MCP server requirements files
   - All Docker services now build successfully
   - Memory bank documentation updated

10. **Docker Build and Runtime Fixes** (COMPLETED - Latest Session)
   - Fixed frontend build error: removed undefined `border-border` Tailwind class
   - Replaced with proper border color styling using theme colors
   - Created missing `ag_ui_handler.py` module in protocols directory
   - Added missing OpenTelemetry dependencies:
     - opentelemetry-instrumentation-httpx>=0.45b0
     - opentelemetry-instrumentation-redis>=0.45b0
   - All containers now start successfully and are healthy
   - Full stack operational: Frontend, Backend, Agents, MCP servers, Redis, PostgreSQL

## Next Steps

### Immediate Tasks
1. **Functionality Testing**
   - Test frontend accessibility at http://localhost:3000
   - Verify CopilotKit UI interaction
   - Test AG-UI endpoint connectivity
   - Validate streaming responses

2. **Backend Testing**
   - Verify AG-UI endpoint is accessible at /ag-ui
   - Test CopilotKit connection to backend
   - Validate streaming responses
   - Check Redis connectivity

3. **Agent Implementation**
   - Create research agent with A2A
   - Create code generation agent
   - Test agent delegation flow

4. **Integration Testing**
   - Test A2A communication
   - Verify AG-UI streaming
   - Validate MCP tool calls

### Medium Priority
- Add authentication layer
- Implement real web search API
- Add comprehensive error handling
- Create unit tests

## Active Decisions

### Architecture Choices
- **Redis for State**: Chosen for simplicity and performance
- **FastAPI**: Selected for async support and automatic OpenAPI
- **Docker Compose**: Used for local development ease

### Protocol Implementation
- **AG-UI via SSE**: Using Server-Sent Events for simplicity
- **A2A with Context**: Maintaining conversation threads
- **MCP stdio**: Local servers use stdio transport

## Important Patterns

### Error Handling Strategy
- Graceful degradation when tools unavailable
- Stream errors to frontend as events
- Maintain partial results on failure

### State Management
- StateDeps for AG-UI state synchronization
- Redis for persistent context
- In-memory caching for performance

## Learnings and Insights

### Protocol Integration
- A2A and AG-UI can share the same FastAPI app
- MCP servers are best isolated in containers
- Context IDs are crucial for conversation continuity

### Implementation Challenges
- Docker networking requires careful configuration
- SSE requires proper CORS handling
- Tool timeout management is critical
- Package version mismatches can break builds completely

### Best Practices Discovered
- Keep orchestrator agent lightweight
- Use dedicated agents for specific domains
- Stream early and often for better UX
- Maintain clear protocol boundaries
- Use specialized agents (react-frontend-developer) for complex setups
- Frontend structure should support both chat and monitoring views
- CopilotKit requires proper client/server component separation in Next.js 14+
- AgnoAgent from @ag-ui/agno package provides seamless AG-UI integration
- Environment variables crucial for backend URL configuration
- Always verify package names and versions on PyPI before using in requirements.txt
- pydantic-ai latest version is 0.4.11, not 0.12.0
- Use fastmcp instead of mcp-server-fastmcp for MCP server implementation
- Tailwind CSS classes must be defined in config or CSS layers
- Always create all imported modules before building Docker images
- Include all required OpenTelemetry instrumentation packages in requirements

## Current Blockers
- ~~Docker dependency issues (fixed - pydantic-ai 0.4.11, fastmcp 2.11.1)~~ ✅
- ~~Docker build errors (fixed - Tailwind CSS, missing modules, OTel deps)~~ ✅
- ~~Docker services need to be started and tested~~ ✅ All running
- API keys need to be added to .env file for full functionality
- Backend agents need implementation

## Questions for Consideration
1. Should we add a message queue for better scalability?
2. How should we handle agent versioning?
3. What's the best approach for tool discovery?