"""Base Redis repository implementation."""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class RedisRepository:
    """Base repository for Redis persistence."""

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "") -> None:
        """Initialize Redis repository."""
        self.redis_url = redis_url
        self.prefix = prefix
        self.client: Optional[redis.Redis] = None
        self._memory_store: Dict[str, Any] = {}

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory storage.")
            self.client = None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None

    def _make_key(self, key: str) -> str:
        """Create a prefixed key."""
        return f"{self.prefix}:{key}" if self.prefix else key

    async def save(
        self,
        key: str,
        value: BaseModel,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Save a model to Redis."""
        full_key = self._make_key(key)
        data = value.model_dump_json()

        if self.client:
            try:
                await self.client.set(full_key, data)
                if ttl_seconds:
                    await self.client.expire(full_key, ttl_seconds)
                return True
            except Exception as e:
                logger.error(f"Failed to save to Redis: {e}")
                return False
        else:
            self._memory_store[full_key] = data
            return True

    async def get(self, key: str, model_class: Type[T]) -> Optional[T]:
        """Get a model from Redis."""
        full_key = self._make_key(key)

        if self.client:
            try:
                data = await self.client.get(full_key)
                if data:
                    return model_class.model_validate_json(data)
            except Exception as e:
                logger.error(f"Failed to get from Redis: {e}")
                return None
        else:
            data = self._memory_store.get(full_key)
            if data:
                return model_class.model_validate_json(data)

        return None

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        full_key = self._make_key(key)

        if self.client:
            try:
                result = await self.client.delete(full_key)
                return result > 0
            except Exception as e:
                logger.error(f"Failed to delete from Redis: {e}")
                return False
        else:
            if full_key in self._memory_store:
                del self._memory_store[full_key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        full_key = self._make_key(key)

        if self.client:
            try:
                return await self.client.exists(full_key) > 0
            except Exception as e:
                logger.error(f"Failed to check existence in Redis: {e}")
                return False
        else:
            return full_key in self._memory_store

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern."""
        full_pattern = self._make_key(pattern)

        if self.client:
            try:
                keys = await self.client.keys(full_pattern)
                # Remove prefix from keys
                prefix_len = len(self.prefix) + 1 if self.prefix else 0
                return [key[prefix_len:] for key in keys]
            except Exception as e:
                logger.error(f"Failed to list keys from Redis: {e}")
                return []
        else:
            # Simple pattern matching for memory store
            import fnmatch
            matching_keys = []
            for key in self._memory_store:
                if fnmatch.fnmatch(key, full_pattern):
                    prefix_len = len(self.prefix) + 1 if self.prefix else 0
                    matching_keys.append(key[prefix_len:])
            return matching_keys