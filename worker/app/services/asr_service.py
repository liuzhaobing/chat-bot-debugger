"""
ASR (Automatic Speech Recognition) 服务
从 backend/agentic_test/services.py 迁移
"""
import asyncio
import logging
import random
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db_context
from app.models.chat import App

logger = logging.getLogger(__name__)


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
        self.app_id = settings.asr_app_id
        
    async def recognize_speech(
        self,
        audio_data: str,
        context: Optional[str] = None,
        audio_format: str = "wav"
    ) -> str:
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
        if settings.dev_mock_external_services:
            return await self._recognize_speech_mock(audio_data)
        
        try:
            logger.info(f"Starting ASR recognition with app_id: {self.app_id}")
            logger.info(f"Audio data length: {len(audio_data) if audio_data else 0}")
            logger.info(f"Audio format: {audio_format}")
            
            # 🔥 格式验证：确保使用WAV格式
            if audio_format != "wav":
                logger.warning(f"ASR app only supports WAV format, but received: {audio_format}")
                logger.warning("This may cause ASR recognition to fail!")
            
            # 使用 SQLAlchemy 查询 App
            async with get_db_context() as db:
                result = await db.execute(
                    select(App).where(App.id == self.app_id)
                )
                app = result.scalar_one_or_none()
                
                if not app:
                    logger.error(f"App not found: {self.app_id}")
                    return await self._recognize_speech_mock(audio_data)
                
                logger.info(f"Found app: {app.name}")
            
            # TODO: 实现实际的 App 调用逻辑
            # 这里需要调用 Django Backend 的 App 执行接口
            # 或者实现独立的 App 执行引擎
            
            # 临时：使用 mock 模式
            logger.warning("App execution not implemented, using mock mode")
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
            "打开油烟机",
            "关闭油烟机",
            "调到三档",
            "打开照明",
            "关闭照明",
            "开始烹饪",
            "停止工作",
            "mock 数据"
        ]
        
        result = random.choice(mock_results)
        logger.info(f"Mock ASR recognized: {result}")
        return result
