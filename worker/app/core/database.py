"""
SQLAlchemy 异步数据库配置
与 Django 共享数据库，但使用 SQLAlchemy Async ORM
"""
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 全局引擎实例
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    获取数据库引擎（单例模式）
    
    Returns:
        AsyncEngine: 异步数据库引擎
    """
    global _engine
    
    if _engine is None:
        # 根据数据库类型选择连接池
        if "sqlite" in settings.database_url:
            # SQLite 不支持连接池
            poolclass = NullPool
            pool_kwargs = {}
        else:
            # PostgreSQL 使用连接池
            poolclass = QueuePool
            pool_kwargs = {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_timeout": settings.database_pool_timeout,
                "pool_recycle": settings.database_pool_recycle,
                "pool_pre_ping": True,  # 连接前检查
            }
        
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,  # 开发环境打印SQL
            poolclass=poolclass,
            **pool_kwargs
        )
        
        logger.info(
            f"Database engine created: {settings.database_url.split('@')[-1]}"
        )
    
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    获取 Session 工厂（单例模式）
    
    Returns:
        async_sessionmaker: 异步 Session 工厂
    """
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后不过期对象
            autocommit=False,
            autoflush=False,
        )
        logger.info("Session maker created")
    
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入：获取数据库会话
    
    用法:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: 数据库会话
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    上下文管理器：获取数据库会话
    
    用法:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
    
    Yields:
        AsyncSession: 数据库会话
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database context error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库

    注意：不创建表！表由 Django 管理
    仅用于测试连接和预热连接池
    """
    try:
        engine = get_engine()

        # 测试连接
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database connection successful")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """
    关闭数据库连接
    用于应用关闭时清理资源
    """
    global _engine, _async_session_maker
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connections closed")


# 健康检查
async def check_db_health() -> bool:
    """
    检查数据库健康状态

    Returns:
        bool: 数据库是否健康
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


__all__ = [
    "Base",
    "get_engine",
    "get_session_maker",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    "check_db_health",
]
