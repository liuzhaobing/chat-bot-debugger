"""
Redis 连接管理
用于 Session 存储和缓存
"""
import logging
from typing import Optional
import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# 全局 Redis 连接池
_redis_pool: Optional[aioredis.ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """
    获取 Redis 连接池（单例模式）
    
    Returns:
        Redis 连接池
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            decode_responses=True
        )
        logger.info(f"Redis pool created: {settings.redis_url}")
    
    return _redis_pool


def get_redis_client() -> aioredis.Redis:
    """
    获取 Redis 客户端（单例模式）
    
    Returns:
        Redis 客户端
    """
    global _redis_client
    
    if _redis_client is None:
        pool = get_redis_pool()
        _redis_client = aioredis.Redis(connection_pool=pool)
        logger.info("Redis client created")
    
    return _redis_client


async def init_redis() -> None:
    """
    初始化 Redis 连接
    测试连接并预热连接池
    """
    try:
        client = get_redis_client()
        
        # 测试连接
        await client.ping()
        
        logger.info("Redis connection successful")
        
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        raise


async def close_redis() -> None:
    """
    关闭 Redis 连接
    用于应用关闭时清理资源
    """
    global _redis_client, _redis_pool
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
    
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis pool closed")


async def check_redis_health() -> bool:
    """
    检查 Redis 健康状态
    
    Returns:
        bool: Redis 是否健康
    """
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


__all__ = [
    "get_redis_pool",
    "get_redis_client",
    "init_redis",
    "close_redis",
    "check_redis_health",
]
