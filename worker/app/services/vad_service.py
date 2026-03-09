"""
VAD (Voice Activity Detection) 服务
从 backend/agentic_test/services.py 迁移
"""
import asyncio
import logging
import base64
import struct
from typing import Dict, Any

from app.config import settings
from app.utils.audio_utils import AudioConverter, AudioValidator

logger = logging.getLogger(__name__)

# 尝试导入 WebRTC VAD
try:
    from webrtcvad import Vad
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger.warning("webrtcvad not available, using energy-based VAD")


class VADService:
    """语音活动检测服务"""
    
    def __init__(self, vad_level: int = 2):
        """
        初始化VAD服务
        
        Args:
            vad_level: VAD敏感度级别 (0-3)，0最不敏感，3最敏感
        """
        self.vad_level = vad_level
        
        if WEBRTC_AVAILABLE:
            try:
                self.vad = Vad(self.vad_level)
                self._use_webrtc = True
                logger.info(f"WebRTC VAD initialized with level {self.vad_level}")
            except Exception as e:
                logger.error(f"Failed to initialize WebRTC VAD: {e}")
                self._use_webrtc = False
                logger.warning("Falling back to energy-based VAD")
        else:
            self._use_webrtc = False
            logger.info("Using energy-based VAD")
    
    def set_vad_level(self, level: int) -> bool:
        """
        动态设置VAD敏感度级别
        
        Args:
            level: VAD级别 (0-3)
        """
        if not (0 <= level <= 3):
            logger.warning(f"Invalid VAD level {level}, must be 0-3")
            return False
            
        self.vad_level = level
        
        if self._use_webrtc:
            try:
                self.vad.set_mode(level)
                logger.info(f"VAD level updated to {level}")
                return True
            except Exception as e:
                logger.error(f"Failed to update VAD level: {e}")
                return False
        else:
            logger.info(f"VAD level updated to {level} (energy-based)")
            return True
    
    async def detect_speech(self, audio_data: str) -> Dict[str, Any]:
        """
        检测音频中的语音活动
        
        Args:
            audio_data: base64编码的音频数据
            
        Returns:
            VAD检测结果字典
        """
        try:
            # 标准化音频格式
            audio_bytes = AudioConverter.normalize_for_vad(audio_data)
            
            # 验证音频格式
            is_valid, error_msg = AudioValidator.validate_pcm_format(audio_bytes)
            if not is_valid:
                logger.error(f"Invalid audio format for VAD: {error_msg}")
                return {
                    'has_speech': False,
                    'error': f'Invalid audio format: {error_msg}',
                    'confidence': 0.0
                }
            
            # 选择VAD实现
            if self._use_webrtc:
                result = await self._process_audio_with_webrtc(audio_bytes)
            else:
                result = await self._process_audio_with_energy_vad(audio_bytes)
            
            logger.info(f"VAD result: has_speech={result.get('has_speech')}, confidence={result.get('confidence')}")
            return result
            
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            return {
                'has_speech': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    async def _process_audio_with_webrtc(self, audio_bytes: bytes) -> Dict[str, Any]:
        """使用WebRTC处理音频"""
        chunk_size = 320  # 10ms at 16kHz
        voice_chunks = 0
        total_chunks = 0
        speech_segments = []
        current_speech_start = None
        
        min_speech_chunks = 5
        min_speech_ratio = 0.3
        
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            
            if len(chunk) < chunk_size:
                chunk = chunk + b'\x00' * (chunk_size - len(chunk))
            
            try:
                has_voice = self.vad.is_speech(chunk, 16000)
                total_chunks += 1
                current_time = total_chunks * 0.01
                
                if has_voice:
                    voice_chunks += 1
                    if current_speech_start is None:
                        current_speech_start = current_time
                else:
                    if current_speech_start is not None:
                        speech_duration = current_time - current_speech_start
                        if speech_duration >= 0.05:
                            speech_segments.append({
                                'start': current_speech_start,
                                'end': current_time,
                                'duration': speech_duration
                            })
                        current_speech_start = None
                
            except Exception as e:
                logger.debug(f"Error processing chunk {i}: {e}")
                continue
        
        if current_speech_start is not None:
            speech_duration = total_chunks * 0.01 - current_speech_start
            if speech_duration >= 0.05:
                speech_segments.append({
                    'start': current_speech_start,
                    'end': total_chunks * 0.01,
                    'duration': speech_duration
                })
        
        speech_ratio = voice_chunks / total_chunks if total_chunks > 0 else 0
        has_speech = (
            voice_chunks >= min_speech_chunks and 
            speech_ratio >= min_speech_ratio and 
            len(speech_segments) > 0
        )
        
        total_speech_duration = sum(seg['duration'] for seg in speech_segments)
        speech_start = speech_segments[0]['start'] if speech_segments else 0
        speech_end = speech_segments[-1]['end'] if speech_segments else 0

        return {
            'has_speech': has_speech,
            'speech_start': round(speech_start, 2),
            'speech_end': round(speech_end, 2),
            'confidence': round(speech_ratio, 2),
            'voice_chunks': voice_chunks,
            'total_chunks': total_chunks,
            'speech_segments': len(speech_segments),
            'total_speech_duration': round(total_speech_duration, 2),
            'speech_ratio': round(speech_ratio, 2),
            'method': 'webrtc'
        }
    
    async def _process_audio_with_energy_vad(self, audio_bytes: bytes) -> Dict[str, Any]:
        """使用能量检测进行VAD"""
        try:
            samples = []
            for i in range(0, len(audio_bytes) - 1, 2):
                sample = struct.unpack('<h', audio_bytes[i:i+2])[0]
                samples.append(sample)
            
            if not samples:
                return {
                    'has_speech': False,
                    'speech_start': 0,
                    'speech_end': 0,
                    'confidence': 0.0,
                    'method': 'energy_based'
                }
            
            frame_size = 320
            frames = []
            
            for i in range(0, len(samples), frame_size):
                frame = samples[i:i + frame_size]
                if len(frame) < frame_size:
                    frame.extend([0] * (frame_size - len(frame)))
                
                energy = sum(s * s for s in frame) / len(frame)
                rms = (energy ** 0.5)
                frames.append(rms)
            
            if not frames:
                return {
                    'has_speech': False,
                    'speech_start': 0,
                    'speech_end': 0,
                    'confidence': 0.0,
                    'method': 'energy_based'
                }
            
            max_energy = max(frames)
            avg_energy = sum(frames) / len(frames)
            threshold = min(avg_energy * 1.5, max_energy * 0.2)
            min_threshold = 100
            threshold = max(threshold, min_threshold)
            
            voice_frames = 0
            speech_segments = []
            current_speech_start = None
            
            for i, energy in enumerate(frames):
                frame_time = i * 0.02
                
                if energy > threshold:
                    voice_frames += 1
                    if current_speech_start is None:
                        current_speech_start = frame_time
                else:
                    if current_speech_start is not None:
                        speech_duration = frame_time - current_speech_start
                        if speech_duration >= 0.1:
                            speech_segments.append({
                                'start': current_speech_start,
                                'end': frame_time,
                                'duration': speech_duration
                            })
                        current_speech_start = None
            
            if current_speech_start is not None:
                speech_duration = len(frames) * 0.02 - current_speech_start
                if speech_duration >= 0.1:
                    speech_segments.append({
                        'start': current_speech_start,
                        'end': len(frames) * 0.02,
                        'duration': speech_duration
                    })
            
            speech_ratio = voice_frames / len(frames) if frames else 0
            has_speech = (
                voice_frames >= 3 and
                speech_ratio >= 0.1 and
                len(speech_segments) > 0 and
                max_energy > avg_energy * 1.2
            )
            
            total_speech_duration = sum(seg['duration'] for seg in speech_segments)
            speech_start = speech_segments[0]['start'] if speech_segments else 0
            speech_end = speech_segments[-1]['end'] if speech_segments else 0
            
            return {
                'has_speech': has_speech,
                'speech_start': round(speech_start, 2),
                'speech_end': round(speech_end, 2),
                'confidence': round(speech_ratio, 2),
                'voice_chunks': voice_frames,
                'total_chunks': len(frames),
                'speech_segments': len(speech_segments),
                'total_speech_duration': round(total_speech_duration, 2),
                'speech_ratio': round(speech_ratio, 2),
                'method': 'energy_based'
            }
            
        except Exception as e:
            logger.error(f"Energy VAD processing failed: {e}")
            return {
                'has_speech': False,
                'error': str(e),
                'confidence': 0.0,
                'method': 'energy_based'
            }
