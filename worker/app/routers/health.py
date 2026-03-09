"""
健康检查路由
提供应用健康状态、数据库连接、Redis 连接等信息
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.database import check_db_health
from app.websocket.manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    summary="健康检查",
    description="检查应用、数据库、Redis 等服务的健康状态",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def health_check():
    """
    健康检查端点
    
    返回:
        - status: 整体健康状态 (healthy/unhealthy)
        - database: 数据库连接状态
        - redis: Redis 连接状态
        - websocket: WebSocket 连接统计
        - version: 应用版本
    """
    health_status = {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }
    
    # 检查数据库
    try:
        db_healthy = await check_db_health()
        health_status["database"] = "connected" if db_healthy else "disconnected"
        
        if not db_healthy:
            health_status["status"] = "unhealthy"
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "error"
        health_status["status"] = "unhealthy"
    
    # 检查 Redis（简化版，实际应实现 Redis 健康检查）
    try:
        # TODO: 实现 Redis 健康检查
        health_status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "error"
        health_status["status"] = "unhealthy"
    
    # WebSocket 连接统计
    try:
        ws_stats = connection_manager.get_stats()
        health_status["websocket"] = {
            "total_connections": ws_stats["total_connections"],
            "max_connections": ws_stats["max_connections"]
        }
    except Exception as e:
        logger.error(f"WebSocket stats failed: {e}")
        health_status["websocket"] = "error"
    
    # 根据健康状态返回不同的 HTTP 状态码
    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(content=health_status, status_code=status_code)


@router.get(
    "/ready",
    summary="就绪检查",
    description="检查应用是否准备好接收流量",
    status_code=status.HTTP_200_OK
)
async def readiness_check():
    """
    就绪检查端点（Kubernetes readiness probe）
    
    检查应用是否准备好处理请求
    """
    try:
        # 检查数据库连接
        db_healthy = await check_db_health()
        
        if not db_healthy:
            return JSONResponse(
                content={"ready": False, "reason": "Database not ready"},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return {"ready": True}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={"ready": False, "reason": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get(
    "/live",
    summary="存活检查",
    description="检查应用是否存活",
    status_code=status.HTTP_200_OK
)
async def liveness_check():
    """
    存活检查端点（Kubernetes liveness probe）
    
    简单检查应用是否还在运行
    """
    return {"alive": True}


__all__ = ["router"]
