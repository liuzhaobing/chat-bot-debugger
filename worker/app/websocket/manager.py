"""
WebSocket 连接管理器
负责管理所有 WebSocket 连接的生命周期
"""
import asyncio
import logging
import time
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
import json

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """连接信息"""
    websocket: WebSocket
    session_id: str
    user_id: Optional[str] = None
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def connection_duration(self) -> float:
        """连接持续时间（秒）"""
        return time.time() - self.connected_at
    
    @property
    def is_alive(self) -> bool:
        """连接是否存活（基于心跳）"""
        return (time.time() - self.last_heartbeat) < settings.ws_heartbeat_timeout


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    功能：
    - 连接注册与注销
    - 消息广播与单播
    - 心跳检测
    - 连接统计
    """
    
    def __init__(self):
        # 活跃连接：session_id -> ConnectionInfo
        self.active_connections: Dict[str, ConnectionInfo] = {}
        
        # 用户连接映射：user_id -> Set[session_id]
        self.user_connections: Dict[str, Set[str]] = {}
        
        # 连接锁
        self._lock = asyncio.Lock()
        
        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        logger.info("ConnectionManager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册新连接
        
        Args:
            websocket: WebSocket 实例
            session_id: 会话ID
            user_id: 用户ID（可选）
            metadata: 元数据（可选）
        """
        async with self._lock:
            # 检查连接数限制
            if len(self.active_connections) >= settings.ws_max_connections:
                logger.warning(
                    f"Max connections reached: {settings.ws_max_connections}"
                )
                await websocket.close(code=1008, reason="Max connections reached")
                return
            
            # 如果会话已存在，先断开旧连接
            if session_id in self.active_connections:
                logger.warning(f"Session {session_id} already connected, closing old connection")
                old_conn = self.active_connections[session_id]
                try:
                    await old_conn.websocket.close(code=1000, reason="New connection established")
                except Exception as e:
                    logger.error(f"Error closing old connection: {e}")
            
            # 接受连接
            await websocket.accept()
            
            # 创建连接信息
            conn_info = ConnectionInfo(
                websocket=websocket,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # 注册连接
            self.active_connections[session_id] = conn_info
            
            # 注册用户连接映射
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(session_id)
            
            logger.info(
                f"WebSocket connected: session={session_id}, "
                f"user={user_id}, total={len(self.active_connections)}"
            )
            
            # 启动心跳任务（如果还没启动）
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def disconnect(self, session_id: str) -> None:
        """
        注销连接
        
        Args:
            session_id: 会话ID
        """
        async with self._lock:
            if session_id not in self.active_connections:
                return
            
            conn_info = self.active_connections[session_id]
            
            # 移除用户连接映射
            if conn_info.user_id:
                if conn_info.user_id in self.user_connections:
                    self.user_connections[conn_info.user_id].discard(session_id)
                    if not self.user_connections[conn_info.user_id]:
                        del self.user_connections[conn_info.user_id]
            
            # 移除连接
            del self.active_connections[session_id]
            
            logger.info(
                f"WebSocket disconnected: session={session_id}, "
                f"duration={conn_info.connection_duration:.1f}s, "
                f"total={len(self.active_connections)}"
            )
    
    async def send_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        发送消息到指定会话
        
        Args:
            session_id: 会话ID
            message: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        if session_id not in self.active_connections:
            logger.warning(f"Session {session_id} not found")
            return False
        
        conn_info = self.active_connections[session_id]
        
        try:
            # 添加时间戳
            if "timestamp" not in message:
                message["timestamp"] = time.time()
            
            await conn_info.websocket.send_json(message)
            return True
            
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected while sending: {session_id}")
            await self.disconnect(session_id)
            return False
            
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")
            return False
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ) -> int:
        """
        广播消息到所有连接
        
        Args:
            message: 消息内容
            exclude: 排除的会话ID集合
            
        Returns:
            int: 成功发送的数量
        """
        exclude = exclude or set()
        success_count = 0
        
        # 添加时间戳
        if "timestamp" not in message:
            message["timestamp"] = time.time()
        
        # 并发发送
        tasks = []
        for session_id in list(self.active_connections.keys()):
            if session_id not in exclude:
                tasks.append(self.send_message(session_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
        
        logger.debug(f"Broadcast sent to {success_count}/{len(tasks)} connections")
        return success_count
    
    async def send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> int:
        """
        发送消息到指定用户的所有连接
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            int: 成功发送的数量
        """
        if user_id not in self.user_connections:
            logger.warning(f"User {user_id} has no active connections")
            return 0
        
        session_ids = list(self.user_connections[user_id])
        success_count = 0
        
        for session_id in session_ids:
            if await self.send_message(session_id, message):
                success_count += 1
        
        return success_count
    
    async def update_heartbeat(self, session_id: str) -> None:
        """
        更新心跳时间
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].last_heartbeat = time.time()
    
    async def _heartbeat_loop(self) -> None:
        """心跳检测循环"""
        logger.info("Heartbeat loop started")
        
        while True:
            try:
                await asyncio.sleep(settings.ws_heartbeat_interval)
                
                # 检查所有连接
                dead_sessions = []
                
                async with self._lock:
                    for session_id, conn_info in self.active_connections.items():
                        if not conn_info.is_alive:
                            dead_sessions.append(session_id)
                
                # 断开死连接
                for session_id in dead_sessions:
                    logger.warning(
                        f"Connection timeout: {session_id}, "
                        f"last_heartbeat={time.time() - self.active_connections[session_id].last_heartbeat:.1f}s ago"
                    )
                    try:
                        conn_info = self.active_connections[session_id]
                        await conn_info.websocket.close(
                            code=1000,
                            reason="Heartbeat timeout"
                        )
                    except Exception as e:
                        logger.error(f"Error closing dead connection: {e}")
                    finally:
                        await self.disconnect(session_id)
                
                # 发送心跳 ping
                if self.active_connections:
                    await self.broadcast({
                        "type": "ping",
                        "content": "heartbeat"
                    })
                
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    def get_connection_info(self, session_id: str) -> Optional[ConnectionInfo]:
        """获取连接信息"""
        return self.active_connections.get(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "max_connections": settings.ws_max_connections,
            "connections": [
                {
                    "session_id": session_id,
                    "user_id": conn.user_id,
                    "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat(),
                    "duration_seconds": conn.connection_duration,
                    "is_alive": conn.is_alive
                }
                for session_id, conn in self.active_connections.items()
            ]
        }
    
    async def shutdown(self) -> None:
        """关闭所有连接"""
        logger.info("Shutting down ConnectionManager...")
        
        # 取消心跳任务
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 关闭所有连接
        session_ids = list(self.active_connections.keys())
        for session_id in session_ids:
            try:
                conn_info = self.active_connections[session_id]
                await conn_info.websocket.close(code=1001, reason="Server shutdown")
            except Exception as e:
                logger.error(f"Error closing connection {session_id}: {e}")
            finally:
                await self.disconnect(session_id)
        
        logger.info("ConnectionManager shutdown complete")


# 全局连接管理器实例
connection_manager = ConnectionManager()


__all__ = ["ConnectionManager", "ConnectionInfo", "connection_manager"]
