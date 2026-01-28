"""
音频处理工具类
用于音频格式转换、重采样等操作
"""

import base64
import struct
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class AudioConverter:
    """音频格式转换器"""
    
    @staticmethod
    def base64_to_pcm(audio_b64: str) -> bytes:
        """
        将base64编码的音频转换为PCM字节数据
        
        Args:
            audio_b64: base64编码的音频数据
            
        Returns:
            PCM字节数据
        """
        try:
            return base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            return b''
    
    @staticmethod
    def pcm_to_base64(pcm_data: bytes) -> str:
        """
        将PCM字节数据转换为base64编码
        
        Args:
            pcm_data: PCM字节数据
            
        Returns:
            base64编码的音频数据
        """
        try:
            return base64.b64encode(pcm_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode PCM to base64: {e}")
            return ''
    
    @staticmethod
    def resample_audio(audio_data: bytes, 
                      from_rate: int, 
                      to_rate: int, 
                      channels: int = 1,
                      sample_width: int = 2) -> bytes:
        """
        重采样音频数据 (简单线性插值)
        
        Args:
            audio_data: 原始音频数据
            from_rate: 原始采样率
            to_rate: 目标采样率
            channels: 声道数
            sample_width: 采样位宽（字节）
            
        Returns:
            重采样后的音频数据
        """
        if from_rate == to_rate:
            return audio_data
        
        try:
            # 解析音频样本
            sample_format = '<h' if sample_width == 2 else '<i'
            samples_per_channel = len(audio_data) // (channels * sample_width)
            
            # 解包音频数据
            samples = []
            for i in range(0, len(audio_data), sample_width):
                if i + sample_width <= len(audio_data):
                    sample = struct.unpack(sample_format, audio_data[i:i + sample_width])[0]
                    samples.append(sample)
            
            # 计算重采样比率
            ratio = to_rate / from_rate
            new_length = int(len(samples) * ratio)
            
            # 线性插值重采样
            resampled = []
            for i in range(new_length):
                # 计算原始索引
                orig_index = i / ratio
                left_index = int(orig_index)
                right_index = min(left_index + 1, len(samples) - 1)
                
                # 线性插值
                if left_index < len(samples):
                    left_sample = samples[left_index]
                    right_sample = samples[right_index]
                    weight = orig_index - left_index
                    interpolated = int(left_sample * (1 - weight) + right_sample * weight)
                    resampled.append(interpolated)
            
            # 重新打包音频数据
            resampled_data = b''
            for sample in resampled:
                resampled_data += struct.pack(sample_format, sample)
            
            return resampled_data
            
        except Exception as e:
            logger.error(f"Failed to resample audio: {e}")
            return audio_data
    
    @staticmethod
    def convert_to_mono(audio_data: bytes, 
                       channels: int = 2, 
                       sample_width: int = 2) -> bytes:
        """
        将多声道音频转换为单声道
        
        Args:
            audio_data: 音频数据
            channels: 原始声道数
            sample_width: 采样位宽（字节）
            
        Returns:
            单声道音频数据
        """
        if channels == 1:
            return audio_data
        
        try:
            sample_format = '<h' if sample_width == 2 else '<i'
            samples_per_frame = len(audio_data) // (channels * sample_width)
            
            mono_data = b''
            for i in range(samples_per_frame):
                # 计算每帧的平均值
                frame_sum = 0
                for ch in range(channels):
                    offset = (i * channels + ch) * sample_width
                    if offset + sample_width <= len(audio_data):
                        sample = struct.unpack(sample_format, 
                                             audio_data[offset:offset + sample_width])[0]
                        frame_sum += sample
                
                # 平均值作为单声道样本
                mono_sample = frame_sum // channels
                mono_data += struct.pack(sample_format, mono_sample)
            
            return mono_data
            
        except Exception as e:
            logger.error(f"Failed to convert to mono: {e}")
            return audio_data
    
    @staticmethod
    def normalize_for_vad(audio_b64: str, 
                         target_rate: int = 16000,
                         target_channels: int = 1,
                         target_width: int = 2) -> bytes:
        """
        将音频标准化为VAD所需的格式
        
        Args:
            audio_b64: base64编码的音频数据
            target_rate: 目标采样率
            target_channels: 目标声道数
            target_width: 目标采样位宽
            
        Returns:
            标准化后的PCM数据
        """
        try:
            # 解码base64
            audio_data = AudioConverter.base64_to_pcm(audio_b64)
            
            # 这里假设输入是标准格式，实际应用中可能需要更复杂的格式检测
            # 简单处理：假设输入已经是16kHz, 16bit格式
            
            # 转换为单声道（如果需要）
            if target_channels == 1:
                # 假设输入可能是双声道
                audio_data = AudioConverter.convert_to_mono(audio_data, channels=2)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to normalize audio for VAD: {e}")
            return b''


class AudioValidator:
    """音频数据验证器"""
    
    @staticmethod
    def validate_pcm_format(audio_data: bytes, 
                           expected_rate: int = 16000,
                           expected_channels: int = 1,
                           expected_width: int = 2) -> Tuple[bool, str]:
        """
        验证PCM音频格式
        
        Args:
            audio_data: PCM音频数据
            expected_rate: 期望采样率
            expected_channels: 期望声道数
            expected_width: 期望采样位宽
            
        Returns:
            (是否有效, 错误信息)
        """
        if not audio_data:
            return False, "Audio data is empty"
        
        # 检查数据长度是否符合格式要求
        expected_frame_size = expected_channels * expected_width
        if len(audio_data) % expected_frame_size != 0:
            return False, f"Audio data length not aligned to frame size ({expected_frame_size})"
        
        # 检查最小长度（至少10ms）
        min_samples = expected_rate * expected_channels * expected_width * 0.01  # 10ms
        if len(audio_data) < min_samples:
            return False, f"Audio data too short (minimum {min_samples} bytes required)"
        
        return True, "Valid"
    
    @staticmethod
    def estimate_audio_info(audio_data: bytes) -> Dict[str, Any]:
        """
        估算音频信息
        
        Args:
            audio_data: 音频数据
            
        Returns:
            音频信息字典
        """
        info = {
            'size_bytes': len(audio_data),
            'estimated_duration_16k_mono': len(audio_data) / (16000 * 2),  # 假设16kHz单声道16bit
            'estimated_samples_16k_mono': len(audio_data) // 2,
        }
        
        return info