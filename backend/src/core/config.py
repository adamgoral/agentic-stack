"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Agentic Stack"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True

    # Database
    database_url: Optional[str] = None
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl_seconds: int = 86400  # 24 hours

    # AI Models
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "openai:gpt-4o"

    # Agent Configuration
    agent_timeout_seconds: int = 30
    max_concurrent_agents: int = 5
    agent_retry_attempts: int = 3

    # MCP Servers
    mcp_web_search_url: str = "http://localhost:3001/sse"
    mcp_python_executor_enabled: bool = True

    # Monitoring
    telemetry_enabled: bool = True
    telemetry_endpoint: Optional[str] = None
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None

    # Security
    secret_key: str = Field(default="change-me-in-production", min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    jwt_refresh_expiration_days: int = 7

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = {"development", "staging", "production"}
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def database_url_async(self) -> Optional[str]:
        """Get async database URL."""
        if self.database_url:
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return None

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        return {
            "timeout": self.agent_timeout_seconds,
            "retry_attempts": self.agent_retry_attempts,
            "model": self.default_model,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()