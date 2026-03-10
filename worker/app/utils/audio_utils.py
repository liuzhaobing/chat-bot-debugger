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


class AudioBufferProcessor:
    """
    音频缓冲处理器

    用于累积音频数据，在达到阈值时触发处理。
    统一处理 VAD+ASR 的音频缓冲逻辑。

    使用示例:
        processor = AudioBufferProcessor()
        processor.add_audio(audio_bytes)
        if processor.should_process():
            combined_audio = processor.get_combined_audio()
            # ... 进行 VAD+ASR 处理
            processor.clear()
    """

    # 默认缓冲参数
    # 3秒 @ 16kHz, 16bit, mono = 16000 * 2 * 3 = 96000 bytes
    DEFAULT_TARGET_BUFFER_SIZE = 96000
    # 6秒最大缓冲
    DEFAULT_MAX_BUFFER_SIZE = 192000
    # 保留1.5秒数据用于溢出处理
    DEFAULT_KEEP_SIZE = 48000

    def __init__(
        self,
        target_buffer_size: int = None,
        max_buffer_size: int = None,
        keep_size: int = None
    ):
        """
        初始化音频缓冲处理器

        Args:
            target_buffer_size: 目标缓冲区大小（字节），达到此大小触发处理
            max_buffer_size: 最大缓冲区大小（字节），超过此大小强制处理
            keep_size: 溢出时保留的数据大小（字节）
        """
        self.target_buffer_size = target_buffer_size or self.DEFAULT_TARGET_BUFFER_SIZE
        self.max_buffer_size = max_buffer_size or self.DEFAULT_MAX_BUFFER_SIZE
        self.keep_size = keep_size or self.DEFAULT_KEEP_SIZE

        self.buffer: list = []
        self.packet_count: int = 0

        logger.info(
            f"AudioBufferProcessor initialized: "
            f"target={self.target_buffer_size}, max={self.max_buffer_size}, keep={self.keep_size}"
        )

    def add_audio(self, audio_bytes: bytes) -> None:
        """
        添加音频数据到缓冲区

        Args:
            audio_bytes: 音频字节数据
        """
        self.buffer.append(audio_bytes)
        self.packet_count += 1

    def get_combined_audio(self) -> bytes:
        """
        获取合并后的音频数据

        Returns:
            合并后的音频字节数据
        """
        return b''.join(self.buffer)

    def get_buffer_size(self) -> int:
        """获取当前缓冲区大小（字节）"""
        return len(self.get_combined_audio())

    def should_process(self) -> bool:
        """
        检查是否应该处理缓冲区中的音频

        Returns:
            True 如果达到目标缓冲区大小
        """
        return self.get_buffer_size() >= self.target_buffer_size

    def is_overflow(self) -> bool:
        """
        检查缓冲区是否溢出

        Returns:
            True 如果超过最大缓冲区大小
        """
        return self.get_buffer_size() > self.max_buffer_size

    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer.clear()
        self.packet_count = 0

    def clear_with_keep(self) -> None:
        """
        清空缓冲区但保留部分数据

        用于溢出处理时保留最后部分音频数据
        """
        combined_audio = self.get_combined_audio()
        self.buffer.clear()
        self.buffer.append(combined_audio[-self.keep_size:])
        self.packet_count = 1

    def get_audio_duration_seconds(self) -> float:
        """
        获取当前缓冲区音频时长（秒）

        基于 16kHz, 16bit, mono 计算

        Returns:
            音频时长（秒）
        """
        # 16kHz * 2 bytes = 32000 bytes per second
        return self.get_buffer_size() / 32000

    def get_stats(self) -> dict:
        """
        获取缓冲区统计信息

        Returns:
            包含缓冲区状态的字典
        """
        buffer_size = self.get_buffer_size()
        return {
            'buffer_size': buffer_size,
            'packet_count': self.packet_count,
            'audio_duration_s': buffer_size / 32000,
            'target_size': self.target_buffer_size,
            'should_process': self.should_process(),
            'is_overflow': self.is_overflow()
        }
