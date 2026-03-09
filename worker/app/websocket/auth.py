"""
WebSocket 认证模块
"""
import logging
from typing import Optional

from app.core.security import verify_token
from app.config import settings

logger = logging.getLogger(__name__)


async def verify_websocket_token(token: Optional[str]) -> Optional[str]:
    """
    验证 WebSocket 连接的 JWT Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        用户 ID，如果验证失败返回 None
    """
    # 开发模式下跳过认证
    if settings.dev_skip_auth:
        logger.warning("Development mode: skipping authentication")
        return "dev_user"
    
    if not token:
        logger.warning("No token provided")
        return None
    
    try:
        # 验证 Token
        payload = verify_token(token)
        
        if not payload:
            logger.warning("Invalid token")
            return None
        
        # 提取用户 ID
        user_id = payload.get("sub")
        
        if not user_id:
            logger.warning("No user_id in token")
            return None
        
        logger.info(f"Token verified for user: {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


__all__ = ["verify_websocket_token"]
