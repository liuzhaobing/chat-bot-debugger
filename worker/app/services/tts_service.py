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
import hashlib
import time
from typing import Optional, Dict, Tuple, Any

from app.config import settings

logger = logging.getLogger(__name__)


class TTSCache:
    """TTS音频本地内存缓存（后期可替换为Redis）"""

    def __init__(self, default_ttl: int = 3600):
        """
        初始化缓存

        Args:
            default_ttl: 默认过期时间（秒），默认1小时
        """
        self._cache: Dict[str, Tuple[str, float]] = {}  # key -> (value, expire_time)
        self._default_ttl = default_ttl

    def _generate_key(self, text: str, speaker: str, sample_rate: int) -> str:
        """生成缓存key"""
        content = f"{text}|{speaker}|{sample_rate}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get(self, text: str, speaker: str, sample_rate: int) -> Optional[str]:
        """
        获取缓存

        Returns:
            缓存的base64音频数据，不存在或已过期返回None
        """
        key = self._generate_key(text, speaker, sample_rate)
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                logger.info(f"TTS cache hit for text: {text[:50]}...")
                return value
            else:
                # 已过期，删除缓存
                del self._cache[key]
                logger.debug(f"TTS cache expired for key: {key}")
        return None

    def set(self, text: str, speaker: str, sample_rate: int, audio_b64: str, ttl: Optional[int] = None) -> None:
        """
        设置缓存

        Args:
            text: 文本
            speaker: 说话人
            sample_rate: 采样率
            audio_b64: base64编码的音频数据
            ttl: 过期时间（秒），None则使用默认值
        """
        key = self._generate_key(text, speaker, sample_rate)
        expire_time = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._cache[key] = (audio_b64, expire_time)
        logger.info(f"TTS cache set for text: {text[:50]}..., ttl: {ttl or self._default_ttl}s")

    def clear_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存条目数
        """
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired TTS cache entries")
        return len(expired_keys)

    def clear_all(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("All TTS cache cleared")


class TTSService:
    """文本转语音服务"""

    # 类级别的缓存实例，所有TTSService实例共享
    _cache: Optional[TTSCache] = None

    def __init__(self, cache_ttl: int = 3600):
        """
        初始化TTS服务

        Args:
            cache_ttl: 缓存过期时间（秒），默认1小时
        """
        self.base_url = settings.tts_base_url
        self.app_id = settings.tts_app_id
        self.access_key = settings.tts_access_key
        self.resource_id = settings.tts_resource_id
        self.speaker = settings.tts_speaker

        # 初始化缓存（延迟初始化，类级别共享）
        if TTSService._cache is None:
            TTSService._cache = TTSCache(default_ttl=cache_ttl)

        # 检查必要的环境变量
        if not all([self.base_url, self.app_id, self.access_key, self.resource_id, self.speaker]):
            raise RuntimeError(
                f"[MOCK 已删除] TTS 服务未完整配置。"
                f"base_url={'已设置' if self.base_url else '未设置'}, "
                f"app_id={'已设置' if self.app_id else '未设置'}, "
                f"access_key={'已设置' if self.access_key else '未设置'}, "
                f"resource_id={'已设置' if self.resource_id else '未设置'}, "
                f"speaker={'已设置' if self.speaker else '未设置'}"
            )
    
    async def generate_speech(self, text: str, sample_rate: int = 24000, use_cache: bool = True, speaker: Optional[str] = None) -> str:
        """
        生成语音数据

        Args:
            text: 要转换的文本
            sample_rate: 采样率，默认24000
            use_cache: 是否使用缓存，默认True
            speaker: 说话人ID，如果不指定则使用默认音色

        Returns:
            base64编码的音频数据
        """
        # 使用传入的speaker或默认speaker
        actual_speaker = speaker or self.speaker

        # 尝试从缓存获取
        if use_cache and TTSService._cache:
            cached_audio = TTSService._cache.get(text, actual_speaker, sample_rate)
            if cached_audio is not None:
                return cached_audio

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-App-Id": self.app_id,
                "X-Api-Access-Key": self.access_key,
                "X-Api-Resource-Id": self.resource_id,
            }

            payload = {
                "req_params": {
                    "speaker": actual_speaker,
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

                    # 缓存结果
                    if use_cache and TTSService._cache:
                        TTSService._cache.set(text, actual_speaker, sample_rate, audio_b64)

                    return audio_b64

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise RuntimeError(
                f"[MOCK 已删除] TTS 生成失败: {e}。text={text[:50] if text else None}"
            )

    @classmethod
    def clear_cache(cls) -> None:
        """清空所有TTS缓存"""
        if cls._cache:
            cls._cache.clear_all()

    @classmethod
    def clear_expired_cache(cls) -> int:
        """清理过期缓存，返回清理的条目数"""
        if cls._cache:
            return cls._cache.clear_expired()
        return 0

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if cls._cache:
            return {
                "cache_size": len(cls._cache._cache),
                "default_ttl": cls._cache._default_ttl,
            }
        return {"cache_size": 0}
