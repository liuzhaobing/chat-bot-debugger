"""
Pydantic Schemas
用于数据验证和序列化
"""
from .websocket import (
    WebSocketMessage,
    StartTestMessage,
    StopTestMessage,
    AudioDataMessage,
    InterventionMessage,
    UpdateIoTConfigMessage,
)
from .audio import AudioData, VADResult, ASRResult
from .device import DeviceStatus, IoTConfig

__all__ = [
    # WebSocket
    "WebSocketMessage",
    "StartTestMessage",
    "StopTestMessage",
    "AudioDataMessage",
    "InterventionMessage",
    "UpdateIoTConfigMessage",
    # Audio
    "AudioData",
    "VADResult",
    "ASRResult",
    # Device
    "DeviceStatus",
    "IoTConfig",
]
