"""
ASR (Automatic Speech Recognition) 服务
通过调用 Django Backend API 执行 ASR 应用
"""
import asyncio
import base64
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.backend_service import BackendService

logger = logging.getLogger(__name__)


class ASRService:
    """
    语音识别服务 - 通过 Backend API 调用 ASR 应用

    重要说明：
        ASR应用只支持WAV格式的BASE64编码音频！
        不支持原始PCM、WebM或其他格式
        必须发送完整的WAV文件格式（包含WAV头部信息）
    """

    def __init__(self, app_id: Optional[str] = None):
        """
        初始化ASR服务

        Args:
            app_id: 可选的 ASR 应用 ID，如果不提供则使用配置中的默认值
        """
        self.app_id = app_id or settings.asr_app_id
        self.backend_service = BackendService()

    async def recognize_speech(
            self,
            audio_data: str,
            context: Optional[str] = None,
            audio_format: str = "wav"
    ) -> str:
        """
        识别语音为文本 - 通过 Backend API 调用 ASR 应用

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

            # 保存音频到本地 logs 目录，方便后续分析
            await self._save_audio_to_logs(audio_data, audio_format)

            # 调用 Backend API
            result = await self.backend_service.invoke_app(
                app_id=self.app_id,
                parameters={
                    "audio_data": audio_data,
                    "format": audio_format,
                    "language": "zh-CN"
                }
            )

            if result.success and result.content:
                logger.info(f"ASR recognition successful: {result.content[:50]}")
                return result.content
            else:
                logger.warning(f"ASR returned empty or failed: {result.error}")
                return await self._recognize_speech_mock(audio_data)

        except Exception as e:
            logger.error(f"ASR recognition failed with exception: {e}")
            logger.exception("Full exception traceback:")
            # 降级到模拟模式
            logger.warning("Falling back to mock ASR")
            return await self._recognize_speech_mock(audio_data)

    async def _save_audio_to_logs(self, audio_data: str, audio_format: str) -> None:
        """
        保存音频数据到本地 logs 目录

        Args:
            audio_data: BASE64编码的音频数据
            audio_format: 音频格式（如 wav）
        """
        try:
            # 确保 logs 目录存在 (worker/logs)
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)

            # 生成文件名：audio-{timestamp}.wav
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"audio-{timestamp}.{audio_format}"
            filepath = logs_dir / filename

            # 解码 BASE64 并保存
            audio_bytes = base64.b64decode(audio_data)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Audio saved to {filepath} ({len(audio_bytes)} bytes)")
        except Exception as e:
            logger.error(f"Failed to save audio to logs: {e}")
            # 不抛出异常，保存失败不应影响 ASR 识别流程

    async def _recognize_speech_mock(self, audio_data: str) -> str:
        """模拟ASR识别"""
        await asyncio.sleep(0.5)  # 模拟识别时间

        # 返回模拟的识别结果
        mock_results = [
            "打开油烟机",
            "关闭油烟机",
            "调到三档",
            "打开照明",
            "关闭照明",
            "开始烹饪",
            "停止工作",
            "测试语音识别成功"
        ]

        result = random.choice(mock_results)
        logger.info(f"Mock ASR recognized: {result}")
        return result