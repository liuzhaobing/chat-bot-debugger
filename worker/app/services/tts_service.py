"""
TTS (Text-to-Speech) 服务
从 backend/agentic_test/services.py 迁移
"""
import asyncio
import logging
import os
import base64
import json
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """文本转语音服务"""
    
    def __init__(self):
        self.base_url = settings.tts_base_url
        self.app_id = settings.tts_app_id
        self.access_key = settings.tts_access_key
        self.resource_id = settings.tts_resource_id
        self.speaker = settings.tts_speaker
        
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
            
            async with httpx.AsyncClient(timeout=settings.tts_timeout) as client:
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
