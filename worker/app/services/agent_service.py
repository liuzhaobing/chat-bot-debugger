"""
Agentic Test Agent 服务
从 backend/agentic_test/agent_loop.py 迁移
核心业务逻辑

架构说明:
- 音频输入层 (Audio Input Layer): 处理音频缓冲、VAD检测、ASR识别
- 云端大脑处理层 (Brain Layer): NLP处理、业务逻辑、决策生成
- 音频输出层 (Audio Output Layer): TTS生成、扬声器播报
"""
import asyncio
import json
import logging
import base64
import time
from typing import Optional, Callable, Dict, Any, Tuple, List
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from app.core.database import get_db_context
from app.models.session import AgenticTestSession
from app.models.log import AgenticTestLog
from app.models.chat import App
from app.services.tts_service import TTSService
from app.services.asr_service import ASRService
from app.services.vad_service import VADService
from app.services.iot_service import IOTService
from app.services.audio_processor import AudioProcessingService
from app.services.backend_service import BackendService
from app.utils.audio_utils import AudioConverter
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类定义 - 用于各层之间的数据传递
# ============================================================================

@dataclass
class AudioInputResult:
    """音频输入处理结果"""
    success: bool
    audio_bytes: Optional[bytes] = None
    audio_duration_s: float = 0.0
    error_message: Optional[str] = None


@dataclass
class VADASRResult:
    """VAD和ASR处理结果"""
    success: bool
    has_speech: bool = False
    asr_text: str = ""
    speech_ratio: float = 0.0
    confidence: float = 0.8
    error_message: Optional[str] = None


@dataclass
class BrainProcessResult:
    """云端大脑处理结果"""
    success: bool
    next_query: str = ""
    should_continue: bool = True
    ai_response: str = ""
    analysis: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class AudioOutputResult:
    """音频输出处理结果"""
    success: bool
    audio_data: Optional[bytes] = None
    text: str = ""
    error_message: Optional[str] = None


class AgenticTestAgent:
    """Agentic Test 智能体主循环"""

    # App IDs
    JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"
    QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

    # 音频处理模式
    AUDIO_MODE_VAD = 'vad'  # VAD 方案：音频缓冲 -> VAD检测 -> ASR识别
    AUDIO_MODE_FIXED_DURATION = 'fixed_duration'  # 固定时长方案：直接进行 ASR 识别

    def __init__(
            self,
            session_id: str,
            send_callback: Callable,
            iot_config: Optional[Dict[str, str]] = None,
            audio_mode: str = 'vad'  # 默认使用 VAD 方案
    ):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self.current_query = ""
        self.current_asr_result = "<noise>"
        self.current_asr_true_result = ""
        self.real_voice_active_time = 0.0  # 记录上一次语音结束的时间点

        # 音频处理模式：'vad' 或 'fixed_duration'
        self.audio_mode = audio_mode

        self.loop_step = 0
        self.max_loop_steps = 1000

        # IOT配置
        self.iot_config = iot_config or {
            'token': '',
            'familyId': '',
            'env': 'test'
        }

        # 初始化服务
        self.tts_service = TTSService()
        self.asr_service = ASRService()
        self.vad_service = VADService()
        self.iot_service = IOTService(
            token=self.iot_config.get('token', ''),
            family_id=self.iot_config.get('familyId', ''),
            env=self.iot_config.get('env', 'test')
        )
        self.audio_service = AudioProcessingService()
        self.backend_service = BackendService()

        # 设备状态缓存
        self.family_devices: Dict = {}
        self.previous_device_status: Dict = {}
        self.current_device_status: Dict = {}

        # 音频缓冲处理器（用于 VAD 方案）
        from app.utils.audio_utils import AudioBufferProcessor
        self.audio_buffer = AudioBufferProcessor()

        # 固定时长音频缓冲区（用于固定时长方案）
        self.fixed_duration_audio_buffer: List[bytes] = []
        self.fixed_duration_audio_size = 0  # 当前缓冲区大小（字节）

        # 音频输入等待事件
        self._audio_input_event = asyncio.Event()

        # 对话历史管理（最多保留最近20轮）
        self.conversation_history: List[Dict[str, str]] = []
        self.max_conversation_history_length = 20

        logger.info(
            f"AgenticTestAgent initialized for session {session_id} with IOT config: "
            f"env={self.iot_config.get('env')}, has_token={bool(self.iot_config.get('token'))}, "
            f"audio_mode={self.audio_mode}"
        )

    async def start_loop(self, initial_query: str, iot_config: Optional[Dict[str, str]] = None):
        """启动智能体循环"""
        self.is_running = True
        self.current_query = initial_query
        self.loop_step = 0

        if iot_config:
            self.iot_config.update(iot_config)

        # 记录初始用户查询
        self._add_to_conversation_history('user', initial_query)

        await self.log_event('user_query', initial_query)
        await self.send_callback('log', f'开始处理查询: {initial_query}')
        await self.send_callback('status', '智能体循环已启动')

        try:
            # 初始化设备状态
            await self.initialize_device_status()

            # 固定时长模式：先播放初始 TTS，然后等待前端发送音频
            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                await self.send_callback('status', '固定时长模式：播放初始 TTS...')
                await self.execute_full_loop()
                # execute_full_loop 返回 False，主循环会等待音频输入

            # 开始主循环
            while self.is_running and self.loop_step < self.max_loop_steps:
                try:
                    self.loop_step += 1
                    await self.send_callback('status', f'执行循环步骤 {self.loop_step}')

                    # VAD 模式：执行完整的Agent循环
                    # 固定时长模式：等待前端发送音频（由 process_audio 触发）
                    if self.audio_mode == self.AUDIO_MODE_VAD:
                        should_continue = await self.execute_full_loop()

                        if not should_continue:
                            # 等待音频输入，保持 is_running 为 True
                            await self.send_callback('status', '等待新的音频输入...')
                            # 清除事件标志，等待 process_audio 触发
                            self._audio_input_event.clear()
                            # 等待音频输入事件，最多等待 300 秒
                            try:
                                await asyncio.wait_for(self._audio_input_event.wait(), timeout=300.0)
                                await self.send_callback('status', '收到音频输入，继续处理...')
                            except asyncio.TimeoutError:
                                await self.send_callback('status', '等待音频超时，继续监听...')
                                continue
                    else:
                        # 固定时长模式：等待前端发送音频
                        await self.send_callback('status', '固定时长模式：等待前端发送音频...')
                        self._audio_input_event.clear()
                        try:
                            await asyncio.wait_for(self._audio_input_event.wait(), timeout=300.0)
                            await self.send_callback('status', '收到音频输入，处理中...')
                        except asyncio.TimeoutError:
                            await self.send_callback('status', '等待音频超时，继续等待...')
                            continue

                    await asyncio.sleep(1.0)

                except asyncio.CancelledError:
                    logger.info("Agent loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Agent loop step error: {e}", exc_info=True)
                    await self.send_callback('error', f'循环步骤 {self.loop_step} 执行错误: {str(e)}')

                    if self.loop_step < self.max_loop_steps:
                        await asyncio.sleep(2.0)
                        continue
                    else:
                        break

            if self.loop_step >= self.max_loop_steps:
                await self.send_callback('warning', f'已达到最大循环步骤数 ({self.max_loop_steps})')

        except Exception as e:
            logger.error(f"Agent loop fatal error: {e}", exc_info=True)
            await self.send_callback('error', f'循环发生致命错误: {str(e)}')
        finally:
            self.is_running = False
            await self.send_callback('status', '智能体循环已结束')

    async def initialize_device_status(self):
        """初始化设备状态"""
        try:
            if not self.iot_config.get('token') or not self.iot_config.get('familyId'):
                await self.send_callback('warning', 'IOT配置不完整，使用模拟数据')
                return

            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['familyId'],
                self.iot_config['token']
            )

            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])
                await self.send_callback('log', f'发现 {len(devices)} 个设备')

                self.family_devices = {}
                for device in devices:
                    device_guid = device.get('deviceGuid')
                    category_name = device.get('categoryName')
                    nick_name = device.get('name')
                    display_type = device.get('displayType')
                    device_status = device.get('device_status')
                    self.family_devices[device_guid] = {
                        'device_guid': device_guid,
                        'category_name': category_name,
                        'nick_name': nick_name,
                        'display_type': display_type,
                        'device_status': device_status
                    }
                    if device_guid:
                        status_result = await self.iot_service.get_device_status(
                            device_guid,
                            self.iot_config['token']
                        )
                        if status_result.get('success', False) or status_result.get('rc') == 0:
                            self.previous_device_status[device_guid] = status_result.get('data', [])

                await self.log_event('iot_query', f'初始化了 {len(self.previous_device_status)} 个设备状态')

        except Exception as e:
            logger.error(f"Failed to initialize device status: {e}")
            await self.send_callback('warning', f'设备状态初始化失败: {str(e)}')

    # ========================================================================
    # 音频输入层 (Audio Input Layer)
    # 负责: 音频缓冲管理、VAD检测、ASR识别
    # ========================================================================

    async def process_audio_input_buffer(
            self,
            audio_data: str,
            audio_format: str = 'webm'
    ) -> AudioInputResult:
        """
        处理音频输入缓冲

        将接收到的音频数据进行缓冲、累积，当达到处理阈值时返回合并后的音频数据。

        Args:
            audio_data: Base64编码的音频数据
            audio_format: 音频格式，默认webm

        Returns:
            AudioInputResult: 包含音频字节数据和时长的结果对象
                - success=True 且 audio_bytes 不为空时表示数据已准备好进行下一步处理
                - success=True 且 audio_bytes 为空时表示缓冲未满，需继续累积
                - success=False 表示处理出错
        """
        try:
            # 解码Base64音频数据
            audio_bytes = base64.b64decode(audio_data)

            await self.log_event('mic_capture', '接收到音频数据', {
                'data_length': len(audio_data),
                'format': audio_format,
                'loop_step': self.loop_step
            })

            # 添加到缓冲区
            self.audio_buffer.add_audio(audio_bytes)

            # 检查是否达到处理阈值
            if not self.audio_buffer.should_process():
                buffer_stats = self.audio_buffer.get_stats()
                logger.debug(
                    f"Audio buffer not ready: {buffer_stats['buffer_size']}/{buffer_stats['target_size']} bytes"
                )
                return AudioInputResult(
                    success=True,
                    audio_bytes=None,
                    audio_duration_s=0.0
                )

            # 触发音频输入事件，通知主循环
            self._audio_input_event.set()

            # 取出数据并清空缓冲区，避免并发竞争
            combined_audio = self.audio_buffer.get_combined_audio()
            audio_duration_s = len(combined_audio) / 32000  # 假设32kHz采样率
            self.audio_buffer.clear()

            logger.info(f"Audio buffer ready: {len(combined_audio)} bytes, duration: {audio_duration_s:.2f}s")

            return AudioInputResult(
                success=True,
                audio_bytes=combined_audio,
                audio_duration_s=audio_duration_s
            )

        except Exception as e:
            logger.error(f"Error processing audio input buffer: {e}", exc_info=True)
            return AudioInputResult(
                success=False,
                error_message=str(e)
            )

    async def perform_vad_and_asr(
            self,
            audio_bytes: bytes,
            audio_duration_s: float
    ) -> VADASRResult:
        """
        执行VAD检测和ASR识别

        对音频数据进行语音活动检测(VAD)和自动语音识别(ASR)处理。
        这是音频输入处理的核心步骤，将音频转换为文本。

        Args:
            audio_bytes: PCM格式的音频字节数据
            audio_duration_s: 音频时长(秒)，用于日志和状态报告

        Returns:
            VADASRResult: 包含VAD和ASR处理结果
                - has_speech: 是否检测到语音
                - asr_text: ASR识别出的文本
                - speech_ratio: 语音占比
                - confidence: 置信度
        """
        try:
            # VAD检测
            await self.send_callback('status', '正在进行语音活动检测...')
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            vad_result = await self.vad_service.detect_speech(audio_b64)
            await self.send_callback('vad_result', vad_result)

            # 发送VAD状态
            await self.send_callback('vad_status',
                                     "detected" if vad_result.get('has_speech') else "no_speech",
                                     {
                                         "has_speech": vad_result.get("has_speech", False),
                                         "speech_ratio": vad_result.get("speech_ratio", 0.0),
                                         "audio_duration_s": audio_duration_s
                                     })

            if not vad_result.get('has_speech'):
                await self.send_callback('status', '未检测到语音')
                return VADASRResult(
                    success=True,
                    has_speech=False,
                    speech_ratio=vad_result.get('speech_ratio', 0.0)
                )

            # ASR识别
            await self.send_callback('status', '正在识别语音...')
            wav_audio_b64 = AudioConverter.pcm_to_wav_base64(audio_bytes)

            asr_result = await self.asr_service.recognize_speech(wav_audio_b64, audio_format="wav")
            await self.send_callback('transcript_final', asr_result, {
                'confidence': vad_result.get('confidence', 0.8),
                'loop_step': self.loop_step,
                'audio_duration_s': audio_duration_s
            })

            asr_text = asr_result.strip()
            if not asr_text:
                await self.send_callback('status', '语音识别结果为空')
                return VADASRResult(
                    success=True,
                    has_speech=True,
                    asr_text="",
                    speech_ratio=vad_result.get('speech_ratio', 0.0)
                )

            # 更新ASR结果记录
            self.current_asr_result = asr_text
            if asr_text != '<noise>':
                self.current_asr_true_result = asr_text
                self.real_voice_active_time = time.perf_counter()

            logger.info(f"ASR result: '{asr_text}'")

            return VADASRResult(
                success=True,
                has_speech=True,
                asr_text=asr_text,
                speech_ratio=vad_result.get('speech_ratio', 0.0),
                confidence=vad_result.get('confidence', 0.8)
            )

        except Exception as e:
            logger.error(f"Error in VAD/ASR processing: {e}", exc_info=True)
            await self.send_callback('error', f'VAD/ASR处理失败: {str(e)}')
            return VADASRResult(
                success=False,
                error_message=str(e)
            )

    async def process_fixed_duration_audio(
            self,
            audio_data: str,
            audio_format: str = 'pcm'
    ) -> VADASRResult:
        """
        处理固定时长音频数据

        这是固定时长方案的核心方法，直接对音频进行 ASR 识别，跳过 VAD 检测。
        适用于前端已经录制好固定时长音频的场景。

        Args:
            audio_data: Base64编码的音频数据
            audio_format: 音频格式，默认 pcm

        Returns:
            VADASRResult: 包含 ASR 识别结果
        """
        try:
            # 解码 Base64 音频数据
            audio_bytes = base64.b64decode(audio_data)

            await self.log_event('mic_capture', '接收到固定时长音频数据', {
                'data_length': len(audio_data),
                'audio_bytes': len(audio_bytes),
                'format': audio_format,
                'loop_step': self.loop_step
            })

            # 计算音频时长（假设 16kHz, 16bit, mono）
            audio_duration_s = len(audio_bytes) / 32000

            await self.send_callback('status', f'处理固定时长音频: {audio_duration_s:.2f}秒')

            # 直接进行 ASR 识别（跳过 VAD）
            await self.send_callback('status', '正在进行语音识别...')

            # 转换为 WAV 格式用于 ASR
            wav_audio_b64 = AudioConverter.pcm_to_wav_base64(audio_bytes)

            # ASR 识别
            asr_result = await self.asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

            await self.send_callback('transcript_final', asr_result, {
                'confidence': 0.9,  # 固定时长方案默认置信度
                'loop_step': self.loop_step,
                'audio_duration_s': audio_duration_s,
                'audio_mode': 'fixed_duration'
            })

            asr_text = asr_result.strip()

            if not asr_text:
                await self.send_callback('status', '语音识别结果为空')
                return VADASRResult(
                    success=True,
                    has_speech=False,
                    asr_text="",
                    speech_ratio=0.0
                )

            # 更新 ASR 结果记录
            self.current_asr_result = asr_text
            if asr_text != '<noise>':
                self.current_asr_true_result = asr_text
                self.real_voice_active_time = time.perf_counter()

            logger.info(f"Fixed duration ASR result: '{asr_text}'")

            return VADASRResult(
                success=True,
                has_speech=True,
                asr_text=asr_text,
                speech_ratio=1.0,  # 固定时长方案默认语音占比为 100%
                confidence=0.9
            )

        except Exception as e:
            logger.error(f"Error processing fixed duration audio: {e}", exc_info=True)
            await self.send_callback('error', f'固定时长音频处理失败: {str(e)}')
            return VADASRResult(
                success=False,
                error_message=str(e)
            )

    # ========================================================================
    # 云端大脑处理层 (Brain Layer)
    # 负责: NLP处理、业务逻辑、决策生成
    # 此层的函数可独立测试和调试
    # ========================================================================

    async def process_brain(
            self,
            asr_text: str,
            context: Optional[Dict[str, Any]] = None
    ) -> BrainProcessResult:
        """
        云端大脑处理核心函数

        这是系统的核心处理单元，类似于传统架构中的NLP层。
        接收ASR识别的文本，进行业务逻辑处理，生成下一步行动。

        此函数设计为可独立测试:
        - 可以直接调用此函数传入模拟的ASR文本进行调试
        - 返回结构化的结果对象，便于断言和验证
        - 不依赖外部音频输入，纯文本处理

        Args:
            asr_text: ASR识别出的文本
            context: 可选的上下文信息，包含:
                - current_query: 当前查询
                - loop_step: 当前循环步数
                - device_status: 设备状态

        Returns:
            BrainProcessResult: 云端大脑处理结果
                - next_query: 生成的下一个查询
                - should_continue: 是否应该继续对话
                - ai_response: AI响应文本
                - analysis: 分析结果详情
        """
        try:
            context = context or {}
            await self.send_callback('status', '云端大脑正在处理...')
            await self.send_callback('brain_input', asr_text)

            # 检查noise或空结果，不记录到对话历史
            if asr_text == '<noise>' or not asr_text or not asr_text.strip():
                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response="检测到噪音或空输入，请重新说话",
                    analysis={'type': 'noise_or_empty_detected'}
                )

            # 记录用户输入（ASR识别的文本）
            self._add_to_conversation_history('user', asr_text)

            # 更新设备状态(可选)
            # await self.update_device_status()

            # 调用判断App分析结果
            # judge_result = await self.call_judge_app(
            #     asr_text,
            #     self.current_device_status,
            #     self.previous_device_status
            # )
            # await self.log_event('app_call', json.dumps(judge_result), {'app_id': self.JUDGE_APP_ID})

            judge_result = {'should_continue': True, }
            # 生成下一个查询
            next_query = await self.generate_next_query(judge_result, asr_text)

            if next_query and next_query.strip():
                self.current_query = next_query
                # 记录AI响应
                self._add_to_conversation_history('assistant', next_query)
                await self.send_callback('log', f'生成新查询: {self.current_query}')
                await self.send_callback('ai_response', self.current_query)
                await self.send_callback('query_generated', {
                    'next_query': next_query,
                    'should_continue': True
                })

                await self.log_event('brain_process', f'ASR: {asr_text} -> Query: {next_query}', {
                    'asr_text': asr_text,
                    'next_query': next_query,
                    'loop_step': self.loop_step,
                    'conversation_history_length': len(self.conversation_history)
                })

                return BrainProcessResult(
                    success=True,
                    next_query=next_query,
                    should_continue=True,
                    ai_response=next_query,
                    analysis={
                        'asr_text': asr_text,
                        'generated_query': next_query
                    }
                )
            else:
                await self.send_callback('status', '对话完成，等待新的音频输入...')
                await self.send_callback('ai_response', '好的，我已经了解了当前情况。')
                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response='好的，我已经了解了当前情况。'
                )

        except Exception as e:
            logger.error(f"Error in brain processing: {e}", exc_info=True)
            await self.send_callback('error', f'云端大脑处理失败: {str(e)}')
            return BrainProcessResult(
                success=False,
                error_message=str(e)
            )

    async def process_brain_with_device_context(
            self,
            asr_text: str
    ) -> BrainProcessResult:
        """
        带设备上下文的云端大脑处理

        便捷方法，自动包含设备状态上下文调用云端大脑处理。

        Args:
            asr_text: ASR识别出的文本

        Returns:
            BrainProcessResult: 云端大脑处理结果
        """
        context = {
            'current_query': self.current_query,
            'loop_step': self.loop_step,
            'device_status': {
                'current': self.current_device_status,
                'previous': self.previous_device_status
            }
        }
        return await self.process_brain(asr_text, context)

    # ========================================================================
    # 音频输出层 (Audio Output Layer)
    # 负责: TTS生成、扬声器播报
    # ========================================================================

    async def generate_and_play_audio(
            self,
            text: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> AudioOutputResult:
        """
        生成TTS音频并发送到前端播放

        将文本转换为语音(TTS)，并通过回调发送到前端进行播放。
        这是音频输出处理的核心步骤。

        Args:
            text: 要转换为语音的文本
            metadata: 可选的元数据，会随音频一起发送

        Returns:
            AudioOutputResult: 音频输出处理结果
                - audio_data: 生成的TTS音频数据
                - text: 原始文本
        """
        try:
            if not text or not text.strip():
                await self.send_callback('status', '文本为空，跳过TTS')
                return AudioOutputResult(
                    success=True,
                    text=""
                )

            # Step 1: 生成TTS音频
            await self.send_callback('status', '正在生成语音...')
            tts_result = await self.tts_service.generate_speech(text)
            self.real_voice_active_time = time.perf_counter()

            await self.log_event('tts_generated', text, {
                'audio_length': len(tts_result),
                'loop_step': self.loop_step
            })

            # Step 2: 发送音频到前端播放
            playback_metadata = metadata or {}
            playback_metadata.update({
                'type': 'tts',
                'text': text,
                'loop_step': self.loop_step
            })

            await self.send_callback('audio_play', tts_result, playback_metadata)

            logger.info(f"TTS generated and sent: {len(tts_result)} bytes for text '{text[:50]}...'")

            return AudioOutputResult(
                success=True,
                audio_data=tts_result,
                text=text
            )

        except Exception as e:
            logger.error(f"Error generating and playing audio: {e}", exc_info=True)
            await self.send_callback('error', f'TTS生成失败: {str(e)}')
            return AudioOutputResult(
                success=False,
                text=text,
                error_message=str(e)
            )

    async def wait_for_speaker_response(
            self,
            wait_time: float = 3.0
    ) -> bool:
        """
        等待智能音响响应

        在发送TTS后等待智能音响处理和响应。

        Args:
            wait_time: 等待时间(秒)

        Returns:
            bool: 等待是否完成
        """
        try:
            await self.send_callback('status', '等待智能音响回应...')
            await asyncio.sleep(wait_time)
            return True
        except asyncio.CancelledError:
            logger.info("Speaker wait cancelled")
            return False
        except Exception as e:
            logger.error(f"Error waiting for speaker: {e}")
            return False

    # ========================================================================
    # 主循环和协调方法
    # ========================================================================

    async def execute_full_loop(self) -> bool:
        """
        执行完整的Agent循环步骤

        协调音频输出流程，使用音频输出层函数完成TTS生成和播放。
        此方法现在是音频输出的协调器，职责清晰。

        Returns:
            bool: 是否应该继续循环
                - VAD 模式: True 表示继续执行循环，False 表示等待音频输入
                - 固定时长模式: 总是返回 False，等待前端发送下一轮音频
        """
        try:
            # VAD 模式：检查 noise 结果快速返回
            if self.audio_mode == self.AUDIO_MODE_VAD:
                if self.current_asr_result == '<noise>' and time.perf_counter() - self.real_voice_active_time < 15:
                    return True

            # 使用音频输出层: 生成TTS并发送到前端播放
            audio_output_result = await self.generate_and_play_audio(self.current_query)

            if not audio_output_result.success:
                logger.error(f"Audio output failed: {audio_output_result.error_message}")
                return False

            # 等待智能音响响应
            await self.wait_for_speaker_response(wait_time=3.0)

            # 根据音频模式决定是否继续循环
            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                # 固定时长模式：播放 TTS 后等待前端发送下一轮音频
                # 前端收到 TTS 后会开始录制 30 秒，然后发送音频
                await self.send_callback('status', '等待前端发送下一轮音频...')
                return False  # 返回 False，让主循环等待音频输入
            else:
                # VAD 模式：继续循环，持续处理音频
                await self.send_callback('status', '等待音频输入...')
                return True

        except Exception as e:
            logger.error(f"Error in execute_full_loop: {e}", exc_info=True)
            await self.send_callback('error', f'循环执行失败: {str(e)}')
            return False

    async def process_audio(self, audio_data: str, audio_format: str = 'webm', audio_mode: str = None):
        """
        处理接收到的音频数据

        根据 audio_mode 选择不同的处理方式：
        - 'vad'（默认）: VAD 方案，音频缓冲 -> VAD检测 -> ASR识别
        - 'fixed_duration': 固定时长方案，直接进行 ASR 识别

        Args:
            audio_data: Base64编码的音频数据
            audio_format: 音频格式，默认 webm
            audio_mode: 音频处理模式，如果为 None 则使用实例的 audio_mode
        """
        if not self.is_running:
            return

        # 确定使用哪种音频处理模式
        mode = audio_mode or self.audio_mode

        try:
            if mode == self.AUDIO_MODE_FIXED_DURATION:
                # ===== 固定时长方案: 直接进行 ASR 识别 =====
                await self.send_callback('status', '使用固定时长方案处理音频...')

                vad_asr_result = await self.process_fixed_duration_audio(audio_data, audio_format)

                if not vad_asr_result.success:
                    await self.send_callback('error', f'固定时长音频处理失败: {vad_asr_result.error_message}')
                    return

                # 未检测到语音或结果为空
                if not vad_asr_result.has_speech or not vad_asr_result.asr_text:
                    await self.send_callback('status', '语音识别结果为空，等待下一次输入...')
                    return

                # 检测到 noise
                if vad_asr_result.asr_text == '<noise>':
                    await self.send_callback('status', '语音识别结果为<noise>')
                    return

            else:
                # ===== VAD 方案: 音频缓冲 -> VAD检测 -> ASR识别 =====
                # 音频输入层: 缓冲处理
                input_result = await self.process_audio_input_buffer(audio_data, audio_format)

                if not input_result.success:
                    await self.send_callback('error', f'音频输入处理失败: {input_result.error_message}')
                    return

                # 缓冲区未满，等待更多数据
                if input_result.audio_bytes is None:
                    return

                # 音频输入层: VAD和ASR处理
                vad_asr_result = await self.perform_vad_and_asr(
                    input_result.audio_bytes,
                    input_result.audio_duration_s
                )

                if not vad_asr_result.success:
                    await self.send_callback('error', f'VAD/ASR处理失败: {vad_asr_result.error_message}')
                    return

                # 未检测到语音或结果为空
                if not vad_asr_result.has_speech or not vad_asr_result.asr_text:
                    return

                # 检测到 noise
                if vad_asr_result.asr_text == '<noise>':
                    await self.send_callback('status', '语音识别结果为<noise>')
                    return

            # ===== 云端大脑处理层: NLP处理和决策（两种方案共用） =====
            brain_result = await self.process_brain_with_device_context(vad_asr_result.asr_text)

            if not brain_result.success:
                await self.send_callback('error', f'云端大脑处理失败: {brain_result.error_message}')
                return

            # 根据云端大脑决策执行下一步
            if brain_result.should_continue and brain_result.next_query:
                await asyncio.sleep(1.0)
                await self.execute_full_loop()

                # 固定时长模式：触发事件让主循环继续等待下一轮音频
                if mode == self.AUDIO_MODE_FIXED_DURATION:
                    self._audio_input_event.set()
            else:
                await self.send_callback('status', '对话完成，等待新的音频输入...')

        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            await self.send_callback('error', f'音频处理失败: {str(e)}')

    async def update_device_status(self):
        """更新设备状态"""
        try:
            if not self.iot_config.get('token') or not self.iot_config.get('familyId'):
                return

            self.previous_device_status = self.current_device_status.copy()
            self.current_device_status = {}

            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['familyId'],
                self.iot_config['token']
            )

            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])

                for device in devices[:3]:
                    device_guid = device.get('deviceGuid')
                    if device_guid:
                        status_result = await self.iot_service.get_device_status(
                            device_guid,
                            self.iot_config['token']
                        )
                        if status_result.get('success', False) or status_result.get('rc') == 0:
                            self.current_device_status[device_guid] = status_result.get('data', [])

                await self.send_callback('device_status_update', {
                    'current': self.current_device_status,
                    'previous': self.previous_device_status,
                    'changes': self.detect_device_changes()
                })

        except Exception as e:
            logger.error(f"Failed to update device status: {e}")

    def detect_device_changes(self) -> Dict[str, Any]:
        """检测设备状态变化"""
        changes = {}
        for device_guid in self.current_device_status:
            current = self.current_device_status.get(device_guid, [])
            previous = self.previous_device_status.get(device_guid, [])

            if current != previous:
                changes[device_guid] = {
                    'has_change': True,
                    'current': current,
                    'previous': previous
                }
            else:
                changes[device_guid] = {'has_change': False}

        return changes

    async def call_judge_app(
            self,
            asr_text: str,
            current_status: Dict,
            previous_status: Dict
    ) -> Dict[str, Any]:
        """
        调用判断App分析ASR结果和设备状态变化

        Args:
            asr_text: ASR识别出的文本
            current_status: 当前设备状态
            previous_status: 之前的设备状态

        Returns:
            分析结果字典，包含:
            - analysis: 分析描述
            - confidence: 置信度
            - should_continue: 是否应继续对话
            - suggested_action: 建议的行动
            - detected_intent: 检测到的意图
        """
        try:
            # 检查是否使用 mock 模式
            if settings.dev_mock_external_services:
                return await self._get_mock_judge_result(asr_text)

            # 使用 BackendService 调用 Judge App
            result = await self.backend_service.invoke_app(
                app_id=self.JUDGE_APP_ID,
                message=f"分析用户语音: {asr_text}",
                parameters={
                    "asr_text": asr_text,
                    "current_device_status": current_status or {},
                    "previous_device_status": previous_status or {}
                }
            )

            if result.success and result.content:
                try:
                    # 尝试解析 JSON 结果
                    parsed_result = json.loads(result.content)
                    await self.log_event('app_call', json.dumps(parsed_result, ensure_ascii=False), {
                        'app_id': self.JUDGE_APP_ID,
                        'latency_ms': result.latency_ms
                    })
                    return parsed_result
                except json.JSONDecodeError:
                    logger.warning(f"Judge app returned non-JSON content: {result.content[:100]}")
                    return await self._get_mock_judge_result(asr_text)
            else:
                logger.warning(f"Judge app call failed: {result.error}")
                return await self._get_mock_judge_result(asr_text)

        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return await self._get_mock_judge_result(asr_text)

    async def call_query_generator_app(
            self,
            message: Any,
    ) -> Dict[str, Any]:
        """
        调用DeviceControlGenerator APP生成下一轮测试query

        Args:
            message: 输入信息

        Returns:
            查询生成结果字典，包含:
             - user_input: 用户输入文本（下一个测试查询）
             - device_guid: 目标设备 GUID
             - device_type: 目标设备类型名称
             - expected_response_semantic: 预期的响应语义
             - should_continue: 是否应继续测试
        """
        try:
            # 使用 BackendService 调用 QueryGenerator App
            result = await self.backend_service.invoke_app(
                app_id=self.QUERY_GENERATOR_APP_ID,
                message=message,
            )

            if result.success and result.content:
                try:
                    # 尝试解析 JSON 结果
                    parsed_result = json.loads(result.content)
                    await self.log_event('app_call', json.dumps(parsed_result, ensure_ascii=False), {
                        'app_id': self.QUERY_GENERATOR_APP_ID,
                        'latency_ms': result.latency_ms
                    })
                    return parsed_result
                except json.JSONDecodeError:
                    logger.warning(f"QueryGenerator app returned non-JSON content: {result.content[:100]}")
                    return await self._get_mock_query_result(message)
            else:
                logger.warning(f"QueryGenerator app call failed: {result.error}")
                return await self._get_mock_query_result(message)

        except Exception as e:
            logger.error(f"Query generator app call failed: {e}")
            return await self._get_mock_query_result(message)

    async def generate_next_query(self, judge_result: Dict[str, Any], asr_text: str) -> str:
        """根据判断结果生成下一个查询"""
        try:
            if not judge_result.get('should_continue', True):
                return ""

            suggested_action = judge_result.get('suggested_action', '')
            if suggested_action == 'end_conversation':
                return ""

            # 使用全局对话历史
            conversation_history_context = self._get_conversation_history_context()

            test_scenario = """
打开烟机
打开烟机灯光
烟机调到最大档
烟机风量最小
调到中等风量
烟机风力最弱
烟机风量/风力调大/调高
减弱烟机风量/风力
烟机风量再小一点
把烟机调到弱档/强档/爆炒档
关烟机风量
关闭烟机灯
帮我把烟机关了
            """.strip()
            query_result = await self.call_query_generator_app(
                message=f"""**测试场景**：\n\n{test_scenario}\n\n**家庭设备列表**：\n\n{self.family_devices}\n\n**对话历史**：\n\n{conversation_history_context}\n\n**当前设备状态**：\n\n[]""".strip(),
            )

            await self.log_event('query_generated', json.dumps(query_result, ensure_ascii=False), {
                'app_id': self.QUERY_GENERATOR_APP_ID,
                'loop_step': self.loop_step
            })

            await self.send_callback('query_generated', query_result)

            if not query_result.get('should_continue', True):
                return ""

            next_query = query_result.get('user_input', '')
            if next_query:
                await self.send_callback('log', f'生成测试意图: {query_result.get("test_intent", "N/A")}')

            return next_query

        except Exception as e:
            logger.error(f"Error generating next query: {e}")
            return "让我继续为您检查设备状态"

    async def _get_mock_judge_result(self, asr_text: str) -> Dict[str, Any]:
        """生成模拟的判断结果"""
        return {
            'analysis': f'分析用户语音: {asr_text}',
            'confidence': 0.75,
            'should_continue': True,
            'suggested_action': 'continue_conversation',
            'detected_intent': 'device_query',
            'device_mentioned': True
        }

    async def _get_mock_query_result(self, test_scenario: str) -> Dict[str, Any]:
        """生成模拟的query生成结果"""
        return {
            'next_query': '打开油烟机',
            'target_device_guid': 'mock_device_guid',
            'target_device_name': '油烟机',
            'expected_device_changes': {
                'workStatus': '1',
                'workStatus_text': '开机'
            },
            'expected_response_keywords': ['已打开', '油烟机', '开启'],
            'expected_response_semantic': '确认油烟机已经打开',
            'test_intent': '测试油烟机开机功能',
            'should_continue': True,
            'reasoning': '使用模拟数据生成测试query'
        }

    # ========================================================================
    # 对话历史管理
    # ========================================================================

    def _add_to_conversation_history(self, role: str, content: str):
        """
        添加一条消息到对话历史，并限制历史长度

        Args:
            role: 消息角色 ('user' 或 'assistant')
            content: 消息内容
        """
        if not content or not content.strip():
            return

        self.conversation_history.append({
            'role': role,
            'content': content.strip()
        })

        # 保持对话历史不超过最大长度
        if len(self.conversation_history) > self.max_conversation_history_length:
            # 移除最早的消息对（保持成对移除）
            excess = len(self.conversation_history) - self.max_conversation_history_length
            self.conversation_history = self.conversation_history[excess:]

        logger.debug(f"Conversation history updated: {len(self.conversation_history)} messages")

    def _get_conversation_history_context(self) -> str:
        """
        获取对话历史的文本格式，用于传递给LLM

        Returns:
            格式化的对话历史文本
        """
        if not self.conversation_history:
            return "无历史对话"

        lines = []
        for msg in self.conversation_history:
            role_name = "用户" if msg['role'] == 'user' else "助手"
            lines.append(f"{role_name}: {msg['content']}")

        return "\n".join(lines)

    def _clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info(f"Conversation history cleared for session {self.session_id}")

    async def handle_intervention(self, message: str):
        """处理人工干预"""
        try:
            await self.log_event('user_query', f'人工干预: {message}')
            await self.send_callback('log', f'接收到干预指令: {message}')

            message_lower = message.lower()

            if any(cmd in message_lower for cmd in ['停止', 'stop', '暂停']):
                await self.stop()
                return

            if any(cmd in message_lower for cmd in ['继续', 'continue', '恢复']):
                if not self.is_running:
                    self.is_running = True
                    await self.send_callback('status', '已恢复运行')
                    await self.execute_full_loop()
                return

            if any(cmd in message_lower for cmd in ['跳过', 'skip', '下一个']):
                await self.send_callback('status', '跳过当前步骤')
                self.current_query = "继续下一个测试"
                await self.execute_full_loop()
                return

            # 记录人工干预消息
            self._add_to_conversation_history('user', message)

            self.current_query = message
            self.loop_step = 0

            if self.is_running:
                await self.execute_full_loop()
            else:
                self.is_running = True
                await self.start_loop(message, self.iot_config)

        except Exception as e:
            logger.error(f"Error handling intervention: {e}", exc_info=True)
            await self.send_callback('error', f'处理干预失败: {str(e)}')

    async def stop(self):
        """停止智能体"""
        self.is_running = False

        # 触发事件，解除可能的等待
        if hasattr(self, '_audio_input_event'):
            self._audio_input_event.set()

        await self.send_callback('status', '智能体已停止')

        self.previous_device_status = {}
        self.current_device_status = {}
        self.loop_step = 0

        # 清空音频缓冲区
        if hasattr(self, 'audio_buffer'):
            self.audio_buffer.clear()

        # 清空对话历史
        self._clear_conversation_history()

        logger.info(f"Agent stopped for session {self.session_id}")

    async def update_iot_config(self, config: Dict[str, str]):
        """更新IOT配置"""
        self.iot_config.update(config)

        if self.iot_service:
            self.iot_service.update_config(
                token=config.get('token', ''),
                family_id=config.get('familyId', ''),
                env=config.get('env', 'test')
            )

        await self.send_callback('log', 'IOT配置已更新')
        await self.log_event('system_status', 'IOT配置已更新', {
            'env': config.get('env', 'test'),
            'has_token': bool(config.get('token')),
            'has_family_id': bool(config.get('familyId'))
        })

    async def log_event(self, log_type: str, content: str, metadata: Optional[dict] = None):
        """记录事件日志"""
        try:
            if len(self.session_id) < 32:
                logger.debug(f"Skipping DB log for test session: {log_type} - {content}")
                return

            async with get_db_context() as db:
                result = await db.execute(
                    select(AgenticTestSession).where(AgenticTestSession.id == self.session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    logger.warning(f"Session not found: {self.session_id}")
                    return

                log = AgenticTestLog(
                    session_id=self.session_id,
                    log_type=log_type,
                    content=content,
                    meta_data=metadata or {}
                )
                db.add(log)
                await db.commit()

        except Exception as e:
            logger.debug(f"Failed to log event: {e}")
