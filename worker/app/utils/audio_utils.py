"""
音频处理工具函数
从 backend/agentic_test/audio_utils.py 迁移
"""
import base64
import logging
import wave
import io
from typing import Tuple

logger = logging.getLogger(__name__)


class AudioConverter:
    """音频格式转换工具"""
    
    @staticmethod
    def normalize_for_vad(audio_data: str) -> bytes:
        """
        标准化音频数据用于VAD处理
        
        Args:
            audio_data: base64编码的音频数据
            
        Returns:
            原始音频字节数据
        """
        try:
            # 解码base64
            audio_bytes = base64.b64decode(audio_data)
            return audio_bytes
        except Exception as e:
            logger.error(f"Failed to normalize audio for VAD: {e}")
            raise
    
    @staticmethod
    def pcm_to_wav_base64(
        pcm_data: bytes,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2
    ) -> str:
        """
        将PCM音频数据转换为WAV格式的BASE64编码
        
        Args:
            pcm_data: 原始PCM音频字节数据
            sample_rate: 采样率，默认16000Hz
            channels: 声道数，默认1（单声道）
            sample_width: 采样位宽，默认2字节（16位）
            
        Returns:
            WAV格式的BASE64编码字符串
        """
        try:
            # 创建内存中的WAV文件
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)
            
            # 获取WAV文件的字节数据
            wav_bytes = wav_buffer.getvalue()
            
            # 转换为BASE64
            wav_base64 = base64.b64encode(wav_bytes).decode('utf-8')
            
            logger.debug(
                f"Converted PCM to WAV: PCM={len(pcm_data)} bytes -> "
                f"WAV={len(wav_bytes)} bytes -> BASE64={len(wav_base64)} chars"
            )
            
            return wav_base64
            
        except Exception as e:
            logger.error(f"Failed to convert PCM to WAV BASE64: {e}")
            # 降级：直接返回PCM的BASE64
            return base64.b64encode(pcm_data).decode('utf-8')


class AudioValidator:
    """音频格式验证工具"""
    
    @staticmethod
    def validate_pcm_format(audio_bytes: bytes) -> Tuple[bool, str]:
        """
        验证PCM音频格式
        
        Args:
            audio_bytes: 音频字节数据
            
        Returns:
            (是否有效, 错误信息)
        """
        if not audio_bytes:
            return False, "Empty audio data"
        
        # 检查数据长度（至少需要320字节，即10ms的16kHz音频）
        if len(audio_bytes) < 320:
            return False, f"Audio data too short: {len(audio_bytes)} bytes"
        
        # 检查数据长度是否为偶数（16位采样）
        if len(audio_bytes) % 2 != 0:
            return False, "Audio data length must be even for 16-bit samples"
        
        return True, ""
