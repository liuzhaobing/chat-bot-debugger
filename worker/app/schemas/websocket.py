"""
WebSocket 消息 Schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """WebSocket 消息基类"""
    type: str = Field(..., description="消息类型")
    content: Optional[str] = Field(None, description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class StartTestMessage(BaseModel):
    """开始测试消息"""
    type: str = Field(default="start_test", const=True)
    query: str = Field(..., description="初始查询")
    iot_config: Optional[Dict[str, str]] = Field(default_factory=dict, description="IoT 配置")


class StopTestMessage(BaseModel):
    """停止测试消息"""
    type: str = Field(default="stop_test", const=True)


class AudioDataMessage(BaseModel):
    """音频数据消息"""
    type: str = Field(default="audio_data", const=True)
    audio: Optional[str] = Field(None, description="Base64 编码的音频数据（旧格式）")
    data: Optional[Dict[str, Any]] = Field(None, description="音频数据对象（新格式）")
    format: str = Field(default="webm", description="音频格式")
    is_complete: bool = Field(default=False, description="是否完整")


class InterventionMessage(BaseModel):
    """人工干预消息"""
    type: str = Field(default="intervention", const=True)
    message: str = Field(..., description="干预消息内容")


class UpdateIoTConfigMessage(BaseModel):
    """更新 IoT 配置消息"""
    type: str = Field(default="update_iot_config", const=True)
    config: Dict[str, str] = Field(..., description="IoT 配置")


class PingMessage(BaseModel):
    """心跳消息"""
    type: str = Field(default="ping", const=True)
