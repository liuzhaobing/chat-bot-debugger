import asyncio
import json
import logging
import os
import base64
import random
import wave
import struct
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from .audio_utils import AudioConverter, AudioValidator
from chat.views import AppViewSet
from chat.models import App

try:
    from webrtc_audio_processing import AudioProcessingModule as AP
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

logger = logging.getLogger(__name__)


class TTSService:
    """文本转语音服务"""
    
    def __init__(self):
        self.base_url = os.environ.get("TTS_BASE_URL")
        self.app_id = os.environ.get("TTS_APP_ID")
        self.access_key = os.environ.get("TTS_ACCESS_KEY")
        self.resource_id = os.environ.get("TTS_RESOURCE_ID")
        self.speaker = os.environ.get("TTS_SPEAKER")
        
        # 检查必要的环境变量
        if not all([self.base_url, self.app_id, self.access_key, self.resource_id, self.speaker]):
            logger.warning("TTS service not fully configured, using mock mode")
            self._use_mock = True
        else:
            self._use_mock = False
    
    async def generate_speech(self, text: str, sample_rate: int = 24000) -> str:
        """
        生成语音数据
        
        Args:
            text: 要转换的文本
            sample_rate: 采样率，默认24000
            
        Returns:
            base64编码的音频数据
        """
        if self._use_mock:
            return await self._generate_mock_speech(text)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-App-Id": self.app_id,
                "X-Api-Access-Key": self.access_key,
                "X-Api-Resource-Id": self.resource_id,
            }
            
            payload = {
                "req_params": {
                    "speaker": self.speaker,
                    "text": text,
                    "audio_params": {
                        "format": "wav",
                        "sample_rate": sample_rate,
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    self.base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    audio_base64_list = []
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                # 解析每行JSON数据
                                chunk_data = json.loads(line)
                                if "data" in chunk_data:
                                    data = chunk_data["data"]
                                    if data:
                                        audio_base64_list.append(data)
                            except json.JSONDecodeError:
                                continue
                    
                    # 合并音频数据
                    audio_bytes = b"".join([base64.b64decode(chunk) for chunk in audio_base64_list])
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    
                    logger.info(f"TTS generated for text: {text[:50]}...")
                    return audio_b64
                    
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # 降级到模拟模式
            return await self._generate_mock_speech(text)
    
    async def _generate_mock_speech(self, text: str) -> str:
        """生成模拟语音数据"""
        await asyncio.sleep(0.5)  # 模拟TTS生成时间
        
        # 生成简单的模拟音频数据
        mock_audio_data = f"mock_tts_audio_for_{text[:20]}".encode('utf-8')
        audio_b64 = base64.b64encode(mock_audio_data).decode('utf-8')
        
        logger.info(f"Mock TTS generated for text: {text[:50]}...")
        return audio_b64


class ASRService:
    """
    语音识别服务 - 直接调用指定应用
    
    重要说明：
        ASR应用只支持WAV格式的BASE64编码音频！
        不支持原始PCM、WebM或其他格式
        必须发送完整的WAV文件格式（包含WAV头部信息）
    """
    
    def __init__(self):
        """初始化ASR服务"""
        self.app_id = "4f95e97b0ec641fab9772b68a81bcf4a"
        
    async def recognize_speech(self, audio_data: str, context: str = None, audio_format: str = "wav") -> str:
        """
        识别语音为文本 - 直接调用指定应用
        
        Args:
            audio_data: BASE64编码的音频数据（必须是WAV格式！）
            context: 上下文信息（可选）
            audio_format: 音频格式（必须是"wav"！）
            
        Returns:
            识别的文本结果
            
        重要提醒：
            🔥 ASR应用只接受WAV格式的BASE64编码音频！
            🔥 audio_format参数必须设置为"wav"
            🔥 audio_data必须是完整WAV文件的BASE64编码，不能是原始PCM
        """
        try:
            logger.info(f"Starting ASR recognition with app_id: {self.app_id}")
            logger.info(f"Audio data length: {len(audio_data) if audio_data else 0}")
            logger.info(f"Audio format: {audio_format}")
            
            # 🔥 格式验证：确保使用WAV格式
            if audio_format != "wav":
                logger.warning(f"ASR app only supports WAV format, but received: {audio_format}")
                logger.warning("This may cause ASR recognition to fail!")
            
            # 使用sync_to_async获取应用实例和相关数据
            from channels.db import database_sync_to_async
            
            @database_sync_to_async
            def get_app_with_type():
                app = App.objects.select_related('app_type').get(id=self.app_id)
                return {
                    'app': app,
                    'name': app.name,
                    'app_type_name': app.app_type.name if app.app_type else 'Unknown'
                }
            
            app_data = await get_app_with_type()
            app = app_data['app']
            
            logger.info(f"Found app: {app_data['name']} (type: {app_data['app_type_name']})")
            
            app_viewset = AppViewSet()
            
            # 🔥 重要：ASR应用的参数格式要求
            parameters = {
                "audio_data": audio_data,      # 必须是WAV格式的BASE64
                "audio_format": audio_format   # 必须是"wav"
            }
            
            if context:
                parameters["context"] = context
            
            logger.info(f"Calling ASR app with parameters keys: {list(parameters.keys())}")
            logger.info(f"Audio format being sent to ASR: {audio_format}")
            
            # 使用sync_to_async调用应用
            @database_sync_to_async
            def execute_app():
                return app_viewset._execute_app(app=app, parameters=parameters)
            
            result = await execute_app()
            
            logger.info(f"App execution result: {result}")
            
            if result["status"] == "success":
                recognized_text = result["content"].strip()
                logger.info(f"ASR recognized successfully: {recognized_text}")
                return recognized_text
            else:
                logger.error(f'ASR recognition failed: {result.get("error")}')
                logger.warning("Falling back to mock ASR")
                return await self._recognize_speech_mock(audio_data)
                
        except Exception as e:
            logger.error(f"ASR recognition failed with exception: {e}")
            logger.exception("Full exception traceback:")
            # 降级到模拟模式
            logger.warning("Falling back to mock ASR")
            return await self._recognize_speech_mock(audio_data)
    
    async def _recognize_speech_mock(self, audio_data: str) -> str:
        """模拟ASR识别"""
        await asyncio.sleep(1.0)  # 模拟识别时间
        
        # 返回模拟的识别结果
        mock_results = [
            "mock 数据"
        ]
        
        result = random.choice(mock_results)
        logger.info(f"Mock ASR recognized: {result}")
        return result


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
                self.ap = AP(
                    enable_vad=True,
                    enable_ns=True,
                    # aec_type=1,
                    # agc_type=2,
                )
                """
                aec_type:
                0 = 关闭 AEC
                1 = 启用 AEC（标准模式）
                2 = 启用 AEC（强抑制模式，可能对应 Extended Filter 或 AEC3）
                agc_type:
                0 = 关闭 AGC
                1 = 模拟模式 (Adaptive Analog)
                2 = 数字模式 (Adaptive Digital)
                3 = 固定数字模式 (Fixed Digital)
                """
                self.ap.set_stream_format(16000, 1)  # 16kHz采样率，单声道
                self.ap.set_ns_level(2)              # 噪声抑制级别 0-3
                self.ap.set_vad_level(self.vad_level) # VAD级别 0-3，可动态调整
                # self.ap.set_aec_level(1)             # 回声消除等级 0-2
                # self.ap.set_agc_level(70)            # 增益控制等级 0-100
                self._use_webrtc = True
                logger.info(f"WebRTC VAD initialized successfully with level {self.vad_level}")
            except Exception as e:
                logger.error(f"Failed to initialize WebRTC VAD: {e}")
                self._use_webrtc = False
                logger.warning("Falling back to simple energy-based VAD")
        else:
            logger.warning("WebRTC VAD not available, using simple energy-based VAD")
            self._use_webrtc = False
    
    def set_vad_level(self, level: int):
        """
        动态设置VAD敏感度级别
        
        Args:
            level: VAD级别 (0-3)，0最不敏感，3最敏感
        """
        if not (0 <= level <= 3):
            logger.warning(f"Invalid VAD level {level}, must be 0-3")
            return False
            
        self.vad_level = level
        
        if self._use_webrtc and hasattr(self, 'ap'):
            try:
                self.ap.set_vad_level(level)
                logger.info(f"VAD level updated to {level}")
                return True
            except Exception as e:
                logger.error(f"Failed to update VAD level: {e}")
                return False
        else:
            logger.info(f"VAD level updated to {level} (energy-based VAD)")
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
            # 返回错误而不是mock数据
            return {
                'has_speech': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    async def _process_audio_with_webrtc(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        使用WebRTC处理音频数据
        
        Args:
            audio_bytes: 原始音频字节数据
            
        Returns:
            VAD检测结果
        """
        # WebRTC VAD需要10ms的音频块 (16kHz, 16bit, 1channel = 320 bytes per 10ms)
        chunk_size = 320  # 10ms at 16kHz, 16bit, mono
        voice_chunks = 0
        total_chunks = 0
        speech_segments = []  # 记录语音段
        current_speech_start = None
        
        # 设置更严格的语音检测阈值
        min_speech_chunks = 5  # 至少50ms连续语音才认为是有效语音
        min_speech_ratio = 0.3  # 至少30%的音频块包含语音
        
        # 按10ms块处理音频
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            
            # 确保块大小正确 (10ms)
            if len(chunk) < chunk_size:
                # 用零填充不足的部分
                chunk = chunk + b'\x00' * (chunk_size - len(chunk))
            
            try:
                # 处理音频块
                processed_chunk = self.ap.process_stream(chunk)
                has_voice = self.ap.has_voice()

                total_chunks += 1
                current_time = total_chunks * 0.01  # 每块10ms
                
                if has_voice:
                    voice_chunks += 1
                    if current_speech_start is None:
                        current_speech_start = current_time
                else:
                    # 语音结束，记录语音段（如果足够长）
                    if current_speech_start is not None:
                        speech_duration = current_time - current_speech_start
                        if speech_duration >= 0.05:  # 至少50ms的语音段
                            speech_segments.append({
                                'start': current_speech_start,
                                'end': current_time,
                                'duration': speech_duration
                            })
                        current_speech_start = None
                
            except Exception as e:
                logger.debug(f"Error processing audio chunk {i}: {e}")
                continue
        
        # 处理最后一个语音段
        if current_speech_start is not None:
            speech_duration = total_chunks * 0.01 - current_speech_start
            if speech_duration >= 0.05:  # 至少50ms的语音段
                speech_segments.append({
                    'start': current_speech_start,
                    'end': total_chunks * 0.01,
                    'duration': speech_duration
                })
        
        # 计算结果
        speech_ratio = voice_chunks / total_chunks if total_chunks > 0 else 0
        
        # 更严格的语音检测条件
        has_speech = (
            voice_chunks >= min_speech_chunks and 
            speech_ratio >= min_speech_ratio and 
            len(speech_segments) > 0
        )
        
        # 计算总语音时长
        total_speech_duration = sum(seg['duration'] for seg in speech_segments)
        
        # 获取第一个和最后一个语音段的时间
        speech_start = speech_segments[0]['start'] if speech_segments else 0
        speech_end = speech_segments[-1]['end'] if speech_segments else 0

        result = {
            'has_speech': has_speech,
            'speech_start': round(speech_start, 2),
            'speech_end': round(speech_end, 2),
            'confidence': round(speech_ratio, 2),
            'voice_chunks': voice_chunks,
            'total_chunks': total_chunks,
            'speech_segments': len(speech_segments),
            'total_speech_duration': round(total_speech_duration, 2),
            'speech_ratio': round(speech_ratio, 2)
        }
        
        logger.debug(f"VAD analysis: {voice_chunks}/{total_chunks} voice chunks, "
                    f"{len(speech_segments)} segments, "
                    f"{total_speech_duration:.2f}s speech, "
                    f"has_speech={has_speech}")
        
        return result
    
    async def _process_audio_with_energy_vad(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        使用简单的能量检测进行VAD
        
        Args:
            audio_bytes: 原始音频字节数据
            
        Returns:
            VAD检测结果
        """
        try:
            # 将字节数据转换为16位整数数组
            import struct
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
                    'voice_chunks': 0,
                    'total_chunks': 0,
                    'speech_segments': 0,
                    'total_speech_duration': 0.0,
                    'speech_ratio': 0.0
                }
            
            # 计算音频能量
            frame_size = 320  # 20ms at 16kHz
            frames = []
            
            for i in range(0, len(samples), frame_size):
                frame = samples[i:i + frame_size]
                if len(frame) < frame_size:
                    frame.extend([0] * (frame_size - len(frame)))
                
                # 计算RMS能量
                energy = sum(s * s for s in frame) / len(frame)
                rms = (energy ** 0.5)
                frames.append(rms)
            
            if not frames:
                return {
                    'has_speech': False,
                    'speech_start': 0,
                    'speech_end': 0,
                    'confidence': 0.0,
                    'voice_chunks': 0,
                    'total_chunks': 0,
                    'speech_segments': 0,
                    'total_speech_duration': 0.0,
                    'speech_ratio': 0.0
                }
            
            # 动态阈值计算
            max_energy = max(frames)
            avg_energy = sum(frames) / len(frames)
            
            # 更敏感的阈值设置
            # 阈值设置为平均能量的1.5倍，但不超过最大能量的20%
            threshold = min(avg_energy * 1.5, max_energy * 0.2)
            
            # 如果音频整体能量很低，使用固定的最小阈值
            min_threshold = 100  # 最小阈值
            threshold = max(threshold, min_threshold)
            
            # 检测语音段
            voice_frames = 0
            speech_segments = []
            current_speech_start = None
            
            for i, energy in enumerate(frames):
                frame_time = i * 0.02  # 20ms per frame
                
                if energy > threshold:
                    voice_frames += 1
                    if current_speech_start is None:
                        current_speech_start = frame_time
                else:
                    if current_speech_start is not None:
                        speech_duration = frame_time - current_speech_start
                        if speech_duration >= 0.1:  # 至少100ms的语音段
                            speech_segments.append({
                                'start': current_speech_start,
                                'end': frame_time,
                                'duration': speech_duration
                            })
                        current_speech_start = None
            
            # 处理最后一个语音段
            if current_speech_start is not None:
                speech_duration = len(frames) * 0.02 - current_speech_start
                if speech_duration >= 0.1:
                    speech_segments.append({
                        'start': current_speech_start,
                        'end': len(frames) * 0.02,
                        'duration': speech_duration
                    })
            
            # 计算结果
            speech_ratio = voice_frames / len(frames) if frames else 0
            
            # 更宽松的语音检测条件
            has_speech = (
                voice_frames >= 3 and  # 至少3帧（60ms）
                speech_ratio >= 0.1 and  # 至少10%的帧包含语音
                len(speech_segments) > 0 and
                max_energy > avg_energy * 1.2  # 最大能量适度高于平均值
            )
            
            # 计算总语音时长
            total_speech_duration = sum(seg['duration'] for seg in speech_segments)
            
            # 获取第一个和最后一个语音段的时间
            speech_start = speech_segments[0]['start'] if speech_segments else 0
            speech_end = speech_segments[-1]['end'] if speech_segments else 0
            
            result = {
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
            
            logger.debug(f"Energy VAD analysis: {voice_frames}/{len(frames)} voice frames, "
                        f"{len(speech_segments)} segments, "
                        f"{total_speech_duration:.2f}s speech, "
                        f"threshold={threshold:.1f}, max_energy={max_energy:.1f}, "
                        f"has_speech={has_speech}")
            
            return result
            
        except Exception as e:
            logger.error(f"Energy VAD processing failed: {e}")
            return {
                'has_speech': False,
                'error': str(e),
                'confidence': 0.0,
                'method': 'energy_based'
            }
    
    def _estimate_duration(self, audio_bytes_length: int, sample_rate: int = 16000, 
                          channels: int = 1, sample_width: int = 2) -> float:
        """
        估算音频时长
        
        Args:
            audio_bytes_length: 音频字节长度
            sample_rate: 采样率
            channels: 声道数
            sample_width: 采样位宽（字节）
            
        Returns:
            音频时长（秒）
        """
        return audio_bytes_length / (sample_rate * channels * sample_width)


class IOTService:
    """物联网设备服务 - 简化版本，直接调用API"""
    
    def __init__(self, token: str = "", family_id: str = "", env: str = "test"):
        """初始化IOT服务"""
        self.token = token
        self.family_id = family_id
        self.env = env
        
        if env == "prod":
            self.base_url = "http://api.myroki.com/rest"
        else:
            self.base_url = "http://api-test.myroki.com/rest"
        
        # 设备状态缓存
        self.device_cache = {}
        self.last_update_time = {}
        
        logger.info(f"IOTService initialized: env={env}, base_url={self.base_url}, has_token={bool(token)}, has_family_id={bool(family_id)}")
    
    def update_config(self, token: str = None, family_id: str = None, env: str = None):
        """更新IOT配置"""
        if token is not None:
            self.token = token
        if family_id is not None:
            self.family_id = family_id
        if env is not None:
            self.env = env
            if env == "prod":
                self.base_url = "http://api.myroki.com/rest"
            else:
                self.base_url = "http://api-test.myroki.com/rest"
        
        logger.info(f"IOTService config updated: env={self.env}, base_url={self.base_url}, has_token={bool(self.token)}, has_family_id={bool(self.family_id)}")
    
    async def get_family_devices(self, family_id: str = None, iot_token: str = None) -> Dict[str, Any]:
        """
        查询指定家庭圈的设备清单
        
        Args:
            family_id: 家庭ID，如果不提供则使用初始化时的family_id
            iot_token: IOT认证token，如果不提供则使用初始化时的token
            
        Returns:
            设备清单数据
        """
        # 使用提供的参数或默认配置
        _family_id = family_id or self.family_id
        _iot_token = iot_token or self.token
        
        if not _family_id or not _iot_token:
            logger.warning("Missing family_id or iot_token for get_family_devices")
            return await self._get_mock_family_devices()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/dms/api/family/device/query-by-family-id",
                    headers={
                        "Authorization": f"Bearer {_iot_token}"
                    },
                    params={
                        "familyId": _family_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Family devices retrieved: {_family_id}, count: {len(result.get('data', []))}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get family devices: {e}")
            # 返回模拟数据
            return await self._get_mock_family_devices()
    
    async def get_device_status(self, device_guid: str, iot_token: str = None) -> Dict[str, Any]:
        """
        查询指定设备GUID的状态详情
        
        Args:
            device_guid: 设备GUID
            iot_token: IOT认证token，如果不提供则使用初始化时的token
            
        Returns:
            设备状态详情
        """
        # 使用提供的参数或默认配置
        _iot_token = iot_token or self.token
        
        if not _iot_token:
            logger.warning("Missing iot_token for get_device_status")
            return await self._get_mock_device_status(device_guid)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={
                        "Authorization": f"Bearer {_iot_token}"
                    },
                    params={
                        "deviceIds": device_guid
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 更新缓存
                self.device_cache[device_guid] = result
                self.last_update_time[device_guid] = asyncio.get_event_loop().time()
                
                logger.info(f"Device status retrieved: {device_guid}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            # 返回模拟数据
            return await self._get_mock_device_status(device_guid)
    
    async def get_multiple_device_status(self, device_guids: list, iot_token: str = None) -> Dict[str, Any]:
        """
        批量查询多个设备的状态
        
        Args:
            device_guids: 设备GUID列表
            iot_token: IOT认证token，如果不提供则使用初始化时的token
            
        Returns:
            多个设备的状态数据
        """
        # 使用提供的参数或默认配置
        _iot_token = iot_token or self.token
        
        results = {}
        
        # 并发查询多个设备状态
        tasks = []
        for device_guid in device_guids:
            task = self.get_device_status(device_guid, _iot_token)
            tasks.append((device_guid, task))
        
        # 等待所有任务完成
        for device_guid, task in tasks:
            try:
                result = await task
                results[device_guid] = result
            except Exception as e:
                logger.error(f"Failed to get status for device {device_guid}: {e}")
                results[device_guid] = await self._get_mock_device_status(device_guid)
        
        return results
    
    def get_cached_device_status(self, device_guid: str, max_age: float = 60.0) -> Optional[Dict[str, Any]]:
        """
        获取缓存的设备状态
        
        Args:
            device_guid: 设备GUID
            max_age: 最大缓存时间（秒）
            
        Returns:
            缓存的设备状态，如果过期或不存在则返回None
        """
        if device_guid not in self.device_cache:
            return None
        
        last_update = self.last_update_time.get(device_guid, 0)
        current_time = asyncio.get_event_loop().time()
        
        if current_time - last_update > max_age:
            # 缓存过期
            return None
        
        return self.device_cache[device_guid]
    
    async def _get_mock_family_devices(self) -> Dict[str, Any]:
        """返回模拟的家庭设备清单"""
        await asyncio.sleep(0.3)  # 模拟API调用时间
        
        return {
            "rc": 0,
            "msg": "操作成功",
            "success": True,
            "data": [
                {
                    "familyId": "test_family_001",
                    "familyName": "测试家庭",
                    "deviceId": 10182044,
                    "deviceGuid": "CQ928c0f535efd97f",
                    "name": "CQ928蒸烤一体机",
                    "dc": "RZKY",
                    "categoryName": "一体机",
                    "dt": "CQ928",
                    "displayType": "CQ928",
                    "deviceTypeName": "蒸烤一体机-CQ928",
                    "deviceTypeIconUrl": None,
                    "netState": 1,
                    "createDatetime": 1758867548000,
                    "updateDatetime": None,
                    "status": 1,
                    "platformCode": "ZKY02",
                    "parentId": None,
                    "subDevices": None
                },
                {
                    "familyId": "test_family_001",
                    "familyName": "测试家庭",
                    "deviceId": 10182045,
                    "deviceGuid": "W760i1c0f535efd98f",
                    "name": "W760-i1洗碗机",
                    "dc": "RZKY",
                    "categoryName": "洗碗机",
                    "dt": "W760-i1",
                    "displayType": "W760-i1",
                    "deviceTypeName": "洗碗机-W760-i1",
                    "deviceTypeIconUrl": None,
                    "netState": 1,
                    "createDatetime": 1758867548000,
                    "updateDatetime": None,
                    "status": 1,
                    "platformCode": "XWJ01",
                    "parentId": None,
                    "subDevices": None
                },
                {
                    "familyId": "test_family_001",
                    "familyName": "测试家庭",
                    "deviceId": 10182046,
                    "deviceGuid": "YYJ001c0f535efd99f",
                    "name": "智能油烟机",
                    "dc": "RZKY",
                    "categoryName": "油烟机",
                    "dt": "YYJ001",
                    "displayType": "YYJ001",
                    "deviceTypeName": "油烟机-YYJ001",
                    "deviceTypeIconUrl": None,
                    "netState": 1,
                    "createDatetime": 1758867548000,
                    "updateDatetime": None,
                    "status": 1,
                    "platformCode": "YYJ01",
                    "parentId": None,
                    "subDevices": None
                }
            ]
        }
    
    async def _get_mock_device_status(self, device_guid: str) -> Dict[str, Any]:
        """返回模拟的设备状态"""
        await asyncio.sleep(0.3)  # 模拟API调用时间
        
        # 根据设备GUID生成不同的模拟数据
        if "CQ928" in device_guid:
            # 蒸烤一体机状态
            return {
                "rc": 0,
                "msg": "操作成功",
                "success": True,
                "data": [
                    {
                        "deviceId": device_guid,
                        "status": 1,
                        "properties": {
                            "stageTotalNum": 1,
                            "doorState": 0,  # 门状态：0-关闭，1-打开
                            "powerState": random.choice([0, 1]),  # 电源状态：0-关闭，1-打开
                            "workState": random.choice([0, 1, 2]),  # 工作状态：0-待机，1-工作，2-暂停
                            "curTopTemp": random.randint(20, 200),  # 当前上管温度
                            "curButtomTemp": random.randint(20, 200),  # 当前下管温度
                            "stageOneSetTopTemp": 200,  # 设定上管温度
                            "stageOneSetButtomTemp": 180,  # 设定下管温度
                            "totalRemainSeonds": random.randint(0, 3600),  # 剩余时间（秒）
                            "stageOneSetTime": 1200,  # 设定时间
                            "stageOneSetMode": random.choice([1, 2, 3, 4, 5, 6, 7]),  # 工作模式
                            "lightSwitch": random.choice([0, 1]),  # 照明开关
                            "rotateSwitch": random.choice([0, 1]),  # 旋转开关
                            "steamState": random.choice([0, 1, 2]),  # 蒸汽状态
                            "waterLevelState": random.choice([0, 1, 2]),  # 水位状态
                            "faultCode": 0,  # 故障代码
                            "timestamp": int(asyncio.get_event_loop().time())
                        }
                    }
                ]
            }
        elif "W760" in device_guid:
            # 洗碗机状态
            return {
                "rc": 0,
                "msg": "操作成功",
                "success": True,
                "data": [
                    {
                        "deviceId": device_guid,
                        "status": 1,
                        "properties": {
                            "powerState": random.choice([0, 1]),  # 电源状态
                            "workState": random.choice([0, 1, 2, 3]),  # 工作状态：0-待机，1-洗涤，2-漂洗，3-烘干
                            "doorState": random.choice([0, 1]),  # 门状态
                            "waterTemp": random.randint(30, 70),  # 水温
                            "remainTime": random.randint(0, 7200),  # 剩余时间
                            "washMode": random.choice([1, 2, 3, 4]),  # 洗涤模式
                            "detergentLevel": random.choice([0, 1, 2, 3]),  # 洗涤剂液位
                            "saltLevel": random.choice([0, 1, 2, 3]),  # 盐液位
                            "faultCode": 0,
                            "timestamp": int(asyncio.get_event_loop().time())
                        }
                    }
                ]
            }
        elif "YYJ" in device_guid:
            # 油烟机状态
            return {
                "rc": 0,
                "msg": "操作成功",
                "success": True,
                "data": [
                    {
                        "deviceId": device_guid,
                        "status": 1,
                        "properties": {
                            "powerState": random.choice([0, 1]),  # 电源状态
                            "fanSpeed": random.choice([0, 1, 2, 3, 4]),  # 风速档位：0-关闭，1-4档
                            "lightState": random.choice([0, 1]),  # 照明状态
                            "oilBoxState": random.choice([0, 1, 2]),  # 油盒状态：0-正常，1-将满，2-已满
                            "filterState": random.choice([0, 1, 2]),  # 滤网状态：0-正常，1-需清洗，2-需更换
                            "workTime": random.randint(0, 86400),  # 累计工作时间
                            "airQuality": random.randint(50, 300),  # 空气质量指数
                            "faultCode": 0,
                            "timestamp": int(asyncio.get_event_loop().time())
                        }
                    }
                ]
            }
        else:
            # 通用设备状态
            return {
                "rc": 0,
                "msg": "操作成功",
                "success": True,
                "data": [
                    {
                        "deviceId": device_guid,
                        "status": 1,
                        "properties": {
                            "powerState": random.choice([0, 1]),
                            "workState": random.choice([0, 1, 2]),
                            "faultCode": 0,
                            "timestamp": int(asyncio.get_event_loop().time())
                        }
                    }
                ]
            }


class AudioProcessingService:
    """音频处理服务"""
    
    @staticmethod
    def extract_audio_features(audio_data: str) -> Dict[str, float]:
        """提取音频特征用于可视化"""
        # TODO: 实现实际的音频特征提取 (如音调、音量等)
        
        features = {
            'pitch': random.uniform(80, 300),  # 音调 (Hz)
            'volume': random.uniform(0.1, 1.0),  # 音量
            'energy': random.uniform(0.2, 0.9),  # 能量
            'spectral_centroid': random.uniform(1000, 4000)  # 频谱重心
        }
        
        logger.debug(f"Audio features extracted: {features}")
        return features


async def process_audio_for_asr(audio_bytes: bytes, app_id: str, save_audio: bool = True) -> Optional[Dict[str, Any]]:
    """
    处理音频数据进行ASR识别
    
    Args:
        audio_bytes: 原始音频字节数据（PCM格式，16kHz, 16bit, 单声道）
        app_id: 应用ID
        save_audio: 是否保存音频文件用于调试
        
    Returns:
        ASR识别结果字典，包含text、confidence、is_partial等字段
        
    注意：
        ASR应用只支持WAV格式的BASE64编码音频！
        必须将PCM数据转换为完整的WAV文件格式再进行BASE64编码
    """
    try:
        wav_file_path = None
        
        # 根据参数决定是否保存音频文件
        if save_audio:
            wav_file_path = await save_audio_as_wav(audio_bytes, app_id)
            logger.info(f"Audio saved to: {wav_file_path}")
        
        # 🔥 关键修复：将PCM数据转换为WAV格式的BASE64
        # ASR应用只接受WAV格式，不能直接发送PCM数据！
        wav_audio_b64 = convert_pcm_to_wav_base64(audio_bytes)
        
        # 初始化ASR服务
        asr_service = ASRService()
        
        # 🔥 重要：发送WAV格式音频，格式参数设置为"wav"
        recognized_text = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")
        
        if recognized_text and recognized_text.strip():
            # ASR本身不返回置信度，移除模拟的置信度
            # 模拟部分结果和最终结果
            is_partial = len(recognized_text) < 10 or random.random() < 0.3
            
            result = {
                'text': recognized_text,
                'is_partial': is_partial,
                'app_id': app_id,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # 只有保存了音频文件时才添加路径
            if wav_file_path:
                result['audio_file'] = wav_file_path
            
            logger.info(f"ASR result for app {app_id}: {result}")
            return result
        else:
            logger.debug(f"No speech recognized for app {app_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing audio for ASR with app {app_id}: {e}")
        return None


def convert_pcm_to_wav_base64(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> str:
    """
    将PCM音频数据转换为WAV格式的BASE64编码
    
    Args:
        pcm_data: 原始PCM音频字节数据
        sample_rate: 采样率，默认16000Hz
        channels: 声道数，默认1（单声道）
        sample_width: 采样位宽，默认2字节（16位）
        
    Returns:
        WAV格式的BASE64编码字符串
        
    注意：
        这是为了兼容ASR应用的格式要求！
        ASR应用只支持完整的WAV文件格式，不支持原始PCM数据
    """
    try:
        import io
        import wave
        
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
        
        logger.debug(f"Converted PCM to WAV: PCM={len(pcm_data)} bytes -> WAV={len(wav_bytes)} bytes -> BASE64={len(wav_base64)} chars")
        
        return wav_base64
        
    except Exception as e:
        logger.error(f"Failed to convert PCM to WAV BASE64: {e}")
        # 降级：直接返回PCM的BASE64（可能不工作，但至少不会崩溃）
        return base64.b64encode(pcm_data).decode('utf-8')


async def save_audio_as_wav(audio_bytes: bytes, app_id: str, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> str:
    """
    将音频字节数据保存为WAV文件
    
    Args:
        audio_bytes: 原始音频字节数据
        app_id: 应用ID
        sample_rate: 采样率，默认16000Hz
        channels: 声道数，默认1（单声道）
        sample_width: 采样位宽，默认2字节（16位）
        
    Returns:
        保存的WAV文件路径
    """
    try:
        # 创建音频保存目录
        audio_dir = os.path.join(os.path.dirname(__file__), '..', 'media', 'debug_audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        # 生成文件名：包含时间戳和app_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        filename = f"asr_debug_{app_id}_{timestamp}.wav"
        file_path = os.path.join(audio_dir, filename)
        
        # 写入WAV文件
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        
        # 记录文件信息
        file_size = len(audio_bytes)
        duration_seconds = file_size / (sample_rate * channels * sample_width)
        
        logger.info(f"Audio saved as WAV: {file_path}")
        logger.info(f"Audio info: size={file_size} bytes, duration={duration_seconds:.2f}s, rate={sample_rate}Hz, channels={channels}")
        
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save audio as WAV: {e}")
        return f"error_saving_audio_{app_id}_{timestamp}.wav"


async def process_audio_with_vad_asr(audio_bytes: bytes, app_id: str) -> Dict[str, Any]:
    """
    使用VAD+ASR处理音频数据
    
    Args:
        audio_bytes: 原始音频字节数据
        app_id: 应用ID
        
    Returns:
        处理结果字典，包含VAD和ASR结果
    """
    try:
        # 将音频数据转换为base64用于VAD
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # 初始化服务
        vad_service = VADService()
        
        # 进行VAD检测
        vad_result = await vad_service.detect_speech(audio_b64)
        
        result = {
            'vad': vad_result,
            'asr': None,
            'app_id': app_id,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # 只有检测到语音时才进行ASR识别和保存音频
        if vad_result.get('has_speech', False):
            logger.info(f"VAD detected speech, proceeding with ASR for app {app_id}")

            # 保存音频文件（只保存有语音的音频）
            wav_file_path = await save_audio_as_wav(audio_bytes, app_id)
            result['audio_file'] = wav_file_path
            
            # 进行ASR识别
            asr_result = await process_audio_for_asr(audio_bytes, app_id, save_audio=False)  # 不重复保存
            result['asr'] = asr_result
        else:
            logger.debug(f"VAD detected no speech for app {app_id}, skipping ASR")
        
        logger.info(f"VAD+ASR result for app {app_id}: VAD={vad_result.get('has_speech')}, ASR={bool(result['asr'])}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio with VAD+ASR for app {app_id}: {e}")
        return {
            'vad': {'has_speech': False, 'error': str(e)},
            'asr': None,
            'app_id': app_id,
            'timestamp': asyncio.get_event_loop().time()
        }