"""
Redis configuration and connection management
"""

import os
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


async def create_redis_pool(url: str = None) -> redis.Redis:
    """
    Create an async Redis connection pool
    
    Args:
        url: Redis URL, defaults to environment variable or localhost
        
    Returns:
        Redis client with connection pool
    """
    if not url:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    try:
        # Create connection pool
        pool = redis.ConnectionPool.from_url(
            url,
            max_connections=50,
            decode_responses=True
        )
        
        # Create Redis client
        client = redis.Redis(connection_pool=pool)
        
        # Test connection
        await client.ping()
        logger.info(f"Connected to Redis at {url}")
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_redis_pool(client: redis.Redis):
    """
    Close Redis connection pool
    
    Args:
        client: Redis client to close
    """
    try:
        await client.close()
        await client.connection_pool.disconnect()
        logger.info("Redis connection pool closed")
    except Exception as e:
        logger.error(f"Error closing Redis pool: {e}")