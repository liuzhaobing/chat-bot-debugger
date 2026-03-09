"""
音频相关 Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AudioData(BaseModel):
    """音频数据"""
    audio_data: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field(default="pcm", description="音频格式")
    sample_rate: int = Field(default=16000, description="采样率")
    channels: int = Field(default=1, description="声道数")
    size: Optional[int] = Field(None, description="数据大小（字节）")


class VADResult(BaseModel):
    """VAD 检测结果"""
    has_speech: bool = Field(..., description="是否检测到语音")
    speech_start: float = Field(default=0.0, description="语音开始时间（秒）")
    speech_end: float = Field(default=0.0, description="语音结束时间（秒）")
    confidence: float = Field(default=0.0, description="置信度")
    voice_chunks: int = Field(default=0, description="语音块数量")
    total_chunks: int = Field(default=0, description="总块数量")
    speech_segments: int = Field(default=0, description="语音段数量")
    total_speech_duration: float = Field(default=0.0, description="总语音时长（秒）")
    speech_ratio: float = Field(default=0.0, description="语音比例")
    method: Optional[str] = Field(None, description="检测方法")
    error: Optional[str] = Field(None, description="错误信息")


class ASRResult(BaseModel):
    """ASR 识别结果"""
    text: str = Field(..., description="识别文本")
    confidence: Optional[float] = Field(None, description="置信度")
    is_partial: bool = Field(default=False, description="是否为部分结果")
    audio_duration_s: Optional[float] = Field(None, description="音频时长（秒）")
