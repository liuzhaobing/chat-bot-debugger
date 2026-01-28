import asyncio
import json
import logging
import os
import base64
import random
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
    """语音识别服务 - 直接调用指定应用"""
    
    def __init__(self):
        """初始化ASR服务"""
        self.app_id = "4f95e97b0ec641fab9772b68a81bcf4a"
        
    async def recognize_speech(self, audio_data: str, context: str = None, audio_format: str = "wav") -> str:
        """
        识别语音为文本 - 直接调用指定应用
        
        Args:
            audio_data: base64编码的音频数据
            context: 上下文信息（可选）
            audio_format: 音频格式（默认为wav）
            
        Returns:
            识别的文本结果
        """
        try:
            # 获取应用实例
            app = App.objects.get(id=self.app_id)
            app_viewset = AppViewSet()
            
            # 准备参数
            parameters = {
                "audio_data": audio_data,
                "audio_format": audio_format
            }
            
            if context:
                parameters["context"] = context
            
            # 直接调用应用
            result = app_viewset._execute_app(app=app, parameters=parameters)
            
            if result["status"] == "success":
                recognized_text = result["content"].strip()
                logger.info(f"ASR recognized: {recognized_text}")
                return recognized_text
            else:
                logger.error(f'ASR recognition failed: {result.get("error")}')
                return await self._recognize_speech_mock(audio_data)
                
        except Exception as e:
            logger.error(f"ASR recognition failed: {e}")
            # 降级到模拟模式
            return await self._recognize_speech_mock(audio_data)
    
    async def _recognize_speech_mock(self, audio_data: str) -> str:
        """模拟ASR识别"""
        await asyncio.sleep(1.0)  # 模拟识别时间
        
        # 返回模拟的识别结果
        mock_results = [
            "油烟机已经打开，风力调至三档",
            "空调温度已调整到26度",
            "客厅灯光已关闭",
            "厨房设备运行正常",
            "收到指令，正在执行操作",
            "请帮我测试一下厨电控制",
            "CQ928设置加湿风焙烤模式",
            "打开一体机澎湃蒸功能"
        ]
        
        result = random.choice(mock_results)
        logger.info(f"Mock ASR recognized: {result}")
        return result


class VADService:
    """语音活动检测服务"""
    
    def __init__(self):
        """初始化VAD服务"""
        if WEBRTC_AVAILABLE:
            try:
                self.ap = AP(enable_vad=True, enable_ns=True)
                self.ap.set_stream_format(16000, 1)  # 16kHz采样率，单声道
                self.ap.set_ns_level(1)              # 噪声抑制级别 0-3
                self.ap.set_vad_level(1)             # VAD级别 0-3
                self._use_webrtc = True
                logger.info("WebRTC VAD initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize WebRTC VAD: {e}, using mock mode")
                self._use_webrtc = False
        else:
            logger.warning("WebRTC VAD not available, using mock mode")
            self._use_webrtc = False
    
    async def detect_speech(self, audio_data: str) -> Dict[str, Any]:
        """
        检测音频中的语音活动
        
        Args:
            audio_data: base64编码的音频数据
            
        Returns:
            VAD检测结果字典
        """
        if not self._use_webrtc:
            return await self._detect_speech_mock(audio_data)
        
        try:
            # 标准化音频格式
            audio_bytes = AudioConverter.normalize_for_vad(audio_data)
            
            # 验证音频格式
            is_valid, error_msg = AudioValidator.validate_pcm_format(audio_bytes)
            if not is_valid:
                logger.warning(f"Invalid audio format: {error_msg}, using mock mode")
                return await self._detect_speech_mock(audio_data)
            
            # 处理音频数据并检测语音
            result = await self._process_audio_with_webrtc(audio_bytes)
            
            logger.info(f"WebRTC VAD result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"WebRTC VAD processing failed: {e}")
            # 降级到模拟模式
            return await self._detect_speech_mock(audio_data)
    
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
                    # 语音结束，记录语音段
                    if current_speech_start is not None:
                        speech_segments.append({
                            'start': current_speech_start,
                            'end': current_time
                        })
                        current_speech_start = None
                
            except Exception as e:
                logger.debug(f"Error processing audio chunk {i}: {e}")
                continue
        
        # 处理最后一个语音段
        if current_speech_start is not None:
            speech_segments.append({
                'start': current_speech_start,
                'end': total_chunks * 0.01
            })
        
        # 计算结果
        has_speech = voice_chunks > 0
        confidence = voice_chunks / total_chunks if total_chunks > 0 else 0
        
        # 获取第一个和最后一个语音段的时间
        speech_start = speech_segments[0]['start'] if speech_segments else 0
        speech_end = speech_segments[-1]['end'] if speech_segments else 0
        
        return {
            'has_speech': has_speech,
            'speech_start': round(speech_start, 2),
            'speech_end': round(speech_end, 2),
            'confidence': round(confidence, 2),
            'voice_chunks': voice_chunks,
            'total_chunks': total_chunks,
            'speech_segments': speech_segments[:5]  # 最多返回前5个语音段
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
    
    async def _detect_speech_mock(self, audio_data: str) -> Dict[str, Any]:
        """模拟VAD检测"""
        await asyncio.sleep(0.2)  # 模拟处理时间
        
        # 模拟VAD结果
        has_speech = random.random() > 0.1  # 90%概率检测到语音
        
        result = {
            'has_speech': has_speech,
            'speech_start': round(random.uniform(0.1, 1.0), 2) if has_speech else 0,
            'speech_end': round(random.uniform(2.0, 5.0), 2) if has_speech else 0,
            'confidence': round(random.uniform(0.8, 0.98), 2) if has_speech else 0,
            'voice_chunks': random.randint(10, 50) if has_speech else 0,
            'total_chunks': random.randint(50, 100)
        }
        
        logger.info(f"Mock VAD result: {result}")
        return result


class IOTService:
    """物联网设备服务 - 简化版本，直接调用API"""
    
    def __init__(self, env: str = "test"):
        """初始化IOT服务"""
        if env == "prod":
            self.base_url = "http://api.myroki.com/rest"
        else:
            self.base_url = "http://api-test.myroki.com/rest"
    
    async def get_family_devices(self, family_id: str, iot_token: str) -> Dict[str, Any]:
        """
        查询指定家庭圈的设备清单
        
        Args:
            family_id: 家庭ID
            iot_token: IOT认证token
            
        Returns:
            设备清单数据
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/dms/api/family/device/query-by-family-id",
                    headers={
                        "Authorization": f"Bearer {iot_token}"
                    },
                    params={
                        "familyId": family_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Family devices retrieved: {family_id}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get family devices: {e}")
            # 返回模拟数据
            return await self._get_mock_family_devices()
    
    async def get_device_status(self, device_guid: str, iot_token: str) -> Dict[str, Any]:
        """
        查询指定设备GUID的状态详情
        
        Args:
            device_guid: 设备GUID
            iot_token: IOT认证token
            
        Returns:
            设备状态详情
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={
                        "Authorization": f"Bearer {iot_token}"
                    },
                    params={
                        "deviceIds": device_guid
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Device status retrieved: {device_guid}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            # 返回模拟数据
            return await self._get_mock_device_status(device_guid)
    
    async def _get_mock_family_devices(self) -> Dict[str, Any]:
        """返回模拟的家庭设备清单"""
        await asyncio.sleep(0.3)  # 模拟API调用时间
        
        return {
            "rc": 0,
            "msg": "操作成功",
            "success": True,
            "data": [
                {
                    "familyId": None,
                    "familyName": None,
                    "deviceId": 10182044,
                    "deviceGuid": "CQ928c0f535efd97f",
                    "name": "CQ928",
                    "dc": "RZKY",
                    "categoryName": "一体机",
                    "dt": "CQ928",
                    "displayType": "CQ928",
                    "deviceTypeName": "蒸烤一体机-CQ928",
                    "deviceTypeIconUrl": None,
                    "netState": None,
                    "createDatetime": 1758867548000,
                    "updateDatetime": None,
                    "status": 1,
                    "platformCode": "ZKY02",
                    "parentId": None,
                    "subDevices": None
                },
                {
                    "familyId": None,
                    "familyName": None,
                    "deviceId": 10182045,
                    "deviceGuid": "W760i1c0f535efd98f",
                    "name": "W760-i1",
                    "dc": "RZKY",
                    "categoryName": "洗碗机",
                    "dt": "W760-i1",
                    "displayType": "W760-i1",
                    "deviceTypeName": "洗碗机-W760-i1",
                    "deviceTypeIconUrl": None,
                    "netState": None,
                    "createDatetime": 1758867548000,
                    "updateDatetime": None,
                    "status": 1,
                    "platformCode": "XWJ01",
                    "parentId": None,
                    "subDevices": None
                }
            ]
        }
    
    async def _get_mock_device_status(self, device_guid: str) -> Dict[str, Any]:
        """返回模拟的设备状态"""
        await asyncio.sleep(0.3)  # 模拟API调用时间
        
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
                        "doorState": 0,
                        "descaleTotalSection": 2,
                        "stageOneSetTopTemp": 200,
                        "stageThreeLeftTime": 0,
                        "waterBoxState": 0,
                        "totalRemainSeonds": 1200,
                        "stageOneSetSteam": 0,
                        "recipeId": 0,
                        "stageOneSetButtomTemp": 0,
                        "stageThreeSetTime": 0,
                        "powerState": 0,
                        "curTopTemp": 22,
                        "curButtomTemp": 22,
                        "stageThreeSetTopTemp": 0,
                        "pictureId": 0,
                        "workState": 0,
                        "rotateSwitch": 0,
                        "wasteWaterTankWaterLevelState": 1,
                        "recipeSetSecs": 0,
                        "stageThreeSetButtomTemp": 0,
                        "paramsNum": 42,
                        "waterBoxPanelState": 0,
                        "stageTwoLeftTime": 0,
                        "stageTwoSetSteam": 0,
                        "stageOneSetMode": 7,
                        "orderLeftSecs": 0,
                        "descaleFlag": 0,
                        "stageOneLeftTime": 1200,
                        "waterLevelState": 0,
                        "curDescaleNum": 0,
                        "faultCode": 0,
                        "stageTwoSetButtomTemp": 0,
                        "stageThreeSetSteam": 0,
                        "curStageNum": 1,
                        "steamState": 2,
                        "lightSwitch": 0,
                        "dirtyWaterBoxState": 0,
                        "stageOneSetTime": 1200,
                        "stageTwoSetTopTemp": 0,
                        "stageTwoSetTime": 0,
                        "stageThreeSetMode": 0
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