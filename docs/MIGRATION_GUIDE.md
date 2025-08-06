# Backend Reorganization Migration Guide

## Overview

The backend has been reorganized following Domain-Driven Design (DDD) principles, SOLID principles, and clean architecture patterns for better maintainability and scalability.

## New Structure

```
backend/
├── src/                      # Main source code directory
│   ├── domain/              # Core business logic (no external dependencies)
│   │   ├── agents/          # Agent domain models and interfaces
│   │   ├── entities/        # Domain entities (Agent, Task, Conversation, Message)
│   │   ├── events/          # Domain events for event-driven architecture
│   │   └── exceptions/      # Domain-specific exceptions
│   ├── application/         # Application layer (use cases)
│   │   ├── services/        # Application services (orchestration logic)
│   │   ├── commands/        # Command handlers (future: CQRS pattern)
│   │   └── queries/         # Query handlers (future: CQRS pattern)
│   ├── infrastructure/      # External concerns and implementations
│   │   ├── agents/          # Concrete agent implementations
│   │   ├── mcp/            # MCP server integrations
│   │   ├── persistence/     # Database/Redis repository implementations
│   │   └── protocols/       # A2A, AG-UI protocol handlers
│   ├── api/                # API layer
│   │   ├── v1/             # API version 1
│   │   │   ├── endpoints/   # FastAPI route handlers
│   │   │   └── dependencies/ # Dependency injection setup
│   │   └── middleware/      # API middleware
│   ├── core/               # Application configuration
│   │   ├── config.py       # Pydantic settings management
│   │   ├── logging.py      # Logging configuration
│   │   └── monitoring.py   # Monitoring and telemetry setup
│   └── main.py             # Application entry point
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                # Utility and runner scripts
└── main.py                 # Backward compatibility layer
```

## Key Changes

### 1. Domain Layer (`src/domain/`)

- **Pure domain entities** with no external dependencies
- Business logic encapsulated in domain objects
- Domain events for decoupled communication
- Custom exceptions for domain-specific errors

### 2. Application Layer (`src/application/`)

- **Service layer** orchestrates domain objects and infrastructure
- Handles use cases and business workflows
- Prepared for CQRS pattern implementation

### 3. Infrastructure Layer (`src/infrastructure/`)

- **All external integrations** (databases, APIs, protocols)
- Repository pattern for data persistence
- Adapter pattern for external services
- Protocol handlers (A2A, AG-UI, MCP)

### 4. API Layer (`src/api/`)

- **RESTful endpoints** organized by version
- Dependency injection for services
- Clear separation of HTTP concerns
- Middleware for cross-cutting concerns

### 5. Core Configuration (`src/core/`)

- **Centralized configuration** using Pydantic Settings
- Environment-based configuration
- Logging and monitoring setup

## Migration Steps

### For Development

1. **Update imports** in your code:
   ```python
   # Old
   from models.state import ConversationState
   from agents.orchestrator import OrchestratorAgent
   
   # New
   from src.domain.entities import Conversation
   from src.infrastructure.agents.orchestrator import OrchestratorAgent
   ```

2. **Use new service layer** for business logic:
   ```python
   from src.application.services import OrchestratorService
   ```

3. **Access configuration** through settings:
   ```python
   from src.core import get_settings
   settings = get_settings()
   ```

### For Docker/Deployment

The `main.py` in the backend root maintains backward compatibility, so existing Docker configurations should continue to work without changes.

### For Testing

Tests have been reorganized into categories:
- `tests/unit/` - Fast, isolated unit tests
- `tests/integration/` - Integration tests with external services
- `tests/e2e/` - End-to-end workflow tests

Run tests with:
```bash
# All tests
pytest

# Only unit tests
pytest tests/unit/

# Only integration tests
pytest tests/integration/

# With coverage
pytest --cov=src
```

## Benefits of New Structure

1. **Clear Separation of Concerns**: Each layer has a specific responsibility
2. **Testability**: Domain logic can be tested without infrastructure
3. **Maintainability**: Changes are localized to specific layers
4. **Scalability**: Easy to add new features without affecting existing code
5. **Flexibility**: Infrastructure can be swapped without changing domain logic
6. **Type Safety**: Strong typing throughout with Pydantic models
7. **Dependency Inversion**: High-level modules don't depend on low-level modules

## Future Enhancements

1. **Event Sourcing**: Domain events are ready for event sourcing implementation
2. **CQRS Pattern**: Command and query folders prepared for CQRS
3. **Database Migration**: Ready for SQLAlchemy/Alembic integration
4. **API Versioning**: Structure supports multiple API versions
5. **Microservices**: Domain boundaries make service extraction straightforward

## Compatibility Notes

- The root `main.py` provides backward compatibility
- Existing Docker configurations should work unchanged
- Environment variables remain the same
- API endpoints maintain the same structure

## Need Help?

If you encounter issues during migration:
1. Check import paths - most issues are due to changed imports
2. Ensure environment variables are set correctly
3. Run tests to verify functionality
4. Check the example implementations in each layer