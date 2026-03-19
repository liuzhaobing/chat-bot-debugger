"""
Agentic Test Agent 服务
从 backend/agentic_test/agent_loop.py 迁移
核心业务逻辑

架构说明:
- 音频输入层 (Audio Input Layer): 处理音频缓冲、VAD检测、ASR识别
- 云端大脑处理层 (Brain Layer): NLP处理、业务逻辑、决策生成
- 音频输出层 (Audio Output Layer): TTS生成、扬声器播报
- 测试工程师层 (Tester Layer): 测试用例管理、执行、评判、报告

重构说明:
- 测试相关功能已剥离到 TesterService
- AgenticTestAgent 负责音频处理和智能体循环
- TesterService 负责测试用例的完整生命周期
"""
import asyncio
import copy
import json
import logging
import base64
import time
import uuid
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

try:
    import jsondiff
    HAS_JSONDIFF = True
except ImportError:
    HAS_JSONDIFF = False
    logging.warning("jsondiff not available, using basic comparison")

from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import set_job_instance_id
from app.models.session import AgenticTestSession
from app.models.log import AgenticTestLog
from app.models.chat import App
from app.services.tts_service import TTSService
from app.services.asr_service import ASRService
from app.services.vad_service import VADService
from app.services.iot_service import IOTService
from app.services.audio_processor import AudioProcessingService
from app.services.backend_service import BackendService
from app.services.tester_service import TesterService
from app.services.tester.models import NextAction, TestCase
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
    """Agentic Test 智能体主循环

    固定时长音频采集方案：
    - 前端持续发送音频数据给后端
    - 后端在发送 TTS 时开始积累音频 buffer
    - 积累固定时长（默认20秒）后进行 ASR 识别
    - 实现一人一轮的交互模式

    架构说明:
    - 本类负责音频处理和智能体循环控制
    - TesterService 负责测试用例管理、执行、评判、报告
    """

    # 音频处理模式常量
    AUDIO_MODE_VAD = 'vad'                    # VAD 模式：缓冲满即处理
    AUDIO_MODE_FIXED_DURATION = 'fixed_duration'  # 固定时长模式：等待固定时长

    # 固定时长配置（秒）
    DEFAULT_FIXED_DURATION = 20

    def __init__(
            self,
            session_id: str,
            send_callback: Callable,
            iot_config: Optional[Dict[str, str]] = None,
            tester_config: Optional[Dict[str, Any]] = None,
            fixed_duration: float = None,
            audio_mode: str = None,
            job_instance_id: Optional[str] = None
    ):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self._test_completed = False  # 标记测试是否已正常完成
        self.current_query = ""
        self.current_asr_result = ""
        self.real_voice_active_time = 0.0

        # 任务标识：优先使用传入的 job_instance_id，其次从 tester_config 获取，最后使用 session_id
        if job_instance_id:
            self.job_instance_id = job_instance_id
        elif tester_config and tester_config.get('job_instance_id'):
            self.job_instance_id = tester_config.get('job_instance_id')
        else:
            self.job_instance_id = session_id

        # 设置日志上下文
        set_job_instance_id(self.job_instance_id)

        # 音频处理模式（默认使用固定时长模式）
        self.audio_mode = audio_mode or self.AUDIO_MODE_FIXED_DURATION

        # 固定时长配置
        self.fixed_duration = fixed_duration or self.DEFAULT_FIXED_DURATION

        self.loop_step = 0
        self.max_loop_steps = 1000

        # IOT配置
        self.iot_config = iot_config or {
            'token': '',
            'familyId': '',
            'env': 'test'
        }

        # 测试配置
        self.tester_config = tester_config or {}

        # TTS音色（优先使用数字员工的音色，否则使用默认音色）
        self.tts_voice_id = tester_config.get('tts_voice_id') if tester_config else None
        if self.tts_voice_id:
            logger.info(f"Using custom TTS voice: {self.tts_voice_id}")
        else:
            logger.info("Using default TTS voice")

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

        # 测试工程师服务 - 管理测试相关功能
        self.tester_service = TesterService(
            backend_service=self.backend_service,
            send_callback=self.send_callback,
            log_event_callback=self.log_event
        )

        # 设备状态缓存
        self.family_devices: Dict = {}
        # A0: TTS 播放后的设备状态（query 发送后的状态）
        self.device_status_after_tts: Dict = {}
        # A1: ASR 识别后的设备状态
        self.device_status_after_asr: Dict = {}

        # 固定时长音频缓冲区
        self.audio_buffer: List[bytes] = []
        self.buffer_start_time: Optional[float] = None
        self.is_buffering: bool = False
        self.buffer_lock = asyncio.Lock()

        # 音频输入等待事件
        self._audio_input_event = asyncio.Event()

        logger.info(
            f"AgenticTestAgent initialized for session {session_id}, "
            f"job_instance_id={self.job_instance_id}, "
            f"IOT config: env={self.iot_config.get('env')}, has_token={bool(self.iot_config.get('token'))}, "
            f"fixed_duration={self.fixed_duration}s"
        )

    @staticmethod
    def _generate_job_instance_id() -> str:
        """生成任务实例ID

        格式: TEST_YYYYMMDDHHMMSS_RANDOM
        用于日志追踪和报告关联
        """
        import os
        import base64
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = base64.b32encode(os.urandom(5)).decode("ascii").lower()
        return f"TEST_{timestamp}_{random_suffix}"

    async def initialize_and_generate_cases(self, iot_config: Optional[Dict[str, str]] = None):
        """初始化服务并生成测试用例（流式）

        第一阶段：准备测试用例，等待用户确认

        Args:
            iot_config: IOT 配置
        """
        self.is_running = True
        self.loop_step = 0

        if iot_config:
            self.iot_config.update(iot_config)

        # 初始化测试工程师服务，传入 tester_config
        await self.tester_service.initialize(
            self.session_id,
            self.iot_config,
            tester_config=self.tester_config
        )

        # 更新任务的 job_instance_id（如果有 task_id）
        await self._update_task_job_info()

        try:
            # 初始化设备信息 - 必须在生成测试用例之前执行
            await self.refresh_device_status(stage='init')

            # 设置测试工程师服务的家庭设备
            self.tester_service.set_family_devices(self.family_devices)

            # 初始化设备协议（用于参数键含义说明）
            await self.tester_service.initialize_judge_protocols()

            # 如果有 PRD 内容，生成测试用例
            prd_content = self.tester_config.get('prd_content') if self.tester_config else None
            if prd_content and prd_content != '测试':
                await self.send_callback('status', '正在根据PRD生成测试用例...')
                devices_md = self._format_devices_to_markdown()  # 将家庭设备信息转换为 Markdown 格式，用于生成测试用例
                cases = await self.tester_service.generate_test_cases_from_config(devices_md)
                if cases:
                    await self.send_callback('log', f'成功生成 {len(cases)} 个测试用例')
                else:
                    await self.send_callback('log', '生成测试用例为空，使用默认测试用例')
            # 后门：当 prd_content == '测试' 时，跳过生成，直接使用默认用例
            elif prd_content == '测试':
                await self.send_callback('log', '检测到测试标记，使用默认测试用例')
                # 发送测试用例设计流程消息，让前端表格正确响应
                await self.send_callback('test_case_generation_started', {
                    'prd_length': len(prd_content),
                })
                # 获取默认测试用例
                default_cases = self.tester_service.get_test_cases()
                # 发送生成完成消息
                await self.send_callback('test_cases_generated', {
                    'test_cases': [tc.to_dict() for tc in default_cases],
                    'count': len(default_cases)
                })
                await self.send_callback('log', f'使用默认测试用例 {len(default_cases)} 个')

            # 通知前端测试用例已准备就绪，等待确认
            all_cases = self.tester_service.get_test_cases()
            await self.send_callback('test_cases_ready_for_confirm', {
                'count': len(all_cases),
                'test_cases': [tc.to_dict() for tc in all_cases]
            })
            await self.send_callback('status', f'测试用例准备就绪，共 {len(all_cases)} 个用例，等待确认...')

        except Exception as e:
            logger.error(f"Error in initialize_and_generate_cases: {e}", exc_info=True)
            await self.send_callback('error', f'初始化或生成测试用例失败: {str(e)}')
            self.is_running = False

    async def start_main_loop(self):
        """启动主测试循环

        第二阶段：用户确认后执行音频处理
        """
        try:
            # 获取初始查询：优先使用外部传入的，否则从测试用例生成
            self.current_query = await self.tester_service.generate_test_query() or ""

            if not self.current_query:
                await self.send_callback('status', '没有可执行的测试用例')
                return

            # 记录初始用户查询
            self.tester_service.add_to_conversation_history('user', self.current_query)

            await self.log_event('user_query', self.current_query)
            await self.send_callback('ai_response', self.current_query)
            await self.send_callback('log', f'开始执行测试查询: {self.current_query}')
            await self.send_callback('status', '智能体循环已启动')

            # 固定时长模式：先播放初始 TTS，然后开始积累音频
            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                await self.send_callback('status', '固定时长模式：播放初始 TTS...')
                await self.execute_full_loop()

            # 开始主循环
            while self.is_running and self.loop_step < self.max_loop_steps:
                try:
                    # 检查测试是否完成（两阶段判断）
                    completion_result = await self.tester_service.check_testing_completion()
                    if completion_result.completed:
                        await self.send_callback('status', '所有测试用例已完成')
                        if completion_result.verified_by_llm:
                            await self.send_callback('status', f'LLM验证完成: {completion_result.llm_analysis}')
                        break

                    if completion_result.unexecuted_indices:
                        logger.info(f"未执行用例索引: {completion_result.unexecuted_indices}")

                    self.loop_step += 1
                    await self.send_callback('status', f'执行循环步骤 {self.loop_step}')

                    if self.audio_mode == self.AUDIO_MODE_VAD:
                        # VAD 模式：执行完整的Agent循环
                        should_continue = await self.execute_full_loop()

                        if not should_continue:
                            await self.send_callback('status', '等待新的音频输入...')
                            self._audio_input_event.clear()
                            try:
                                await asyncio.wait_for(self._audio_input_event.wait(), timeout=200.0)
                                await self.send_callback('status', '收到音频输入，继续处理...')
                            except asyncio.TimeoutError:
                                await self.send_callback('status', '等待音频超时，继续监听...')
                                continue
                    else:
                        # 固定时长模式：等待前端持续发送音频
                        await self.send_callback('status', f'固定时长模式：等待音频输入（目标 {self.fixed_duration} 秒）...')
                        self._audio_input_event.clear()
                        try:
                            await asyncio.wait_for(self._audio_input_event.wait(), timeout=600.0)
                        except asyncio.TimeoutError:
                            if self.is_running:
                                await self.send_callback('status', '等待音频超时，继续等待...')
                                continue
                            else:
                                break

                    await asyncio.sleep(1.0)

                except asyncio.CancelledError:
                    logger.info("Agent loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Agent loop step error: {e}", exc_info=True)
                    await self.send_callback('error', f'循环步骤 {self.loop_step} 执行错误: {str(e)}')

                    if self.loop_step < self.max_loop_steps:
                        await asyncio.sleep(1.0)
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
            self._stop_buffering()
            await self.send_callback('status', '智能体循环已结束')

    async def start_loop(self, initial_query: str = None, iot_config: Optional[Dict[str, str]] = None):
        """启动智能体循环（向后兼容）

        保持向后兼容，内部调用新的两阶段方法

        Args:
            initial_query: 初始查询（可选，如果不提供则从测试用例生成）
            iot_config: IOT 配置
        """
        await self.initialize_and_generate_cases(iot_config)
        await self.start_main_loop()

    async def refresh_device_status(self, stage: str = 'after_asr', device_guids: List[str] = None):
        """刷新设备状态

        Args:
            stage: 查询阶段
                - 'init': 初始化模式，初始化 family_devices，不存储状态
                - 'after_tts': TTS 播放后查询，状态存入 device_status_after_tts (A0)
                - 'after_asr': ASR 识别后查询，状态存入 device_status_after_asr (A1)
            device_guids: 指定设备GUID列表，当有值时跳过 get_family_devices 调用，直接查询这些设备状态
        """
        try:
            if not self.iot_config.get('token'):
                if stage == 'init':
                    await self.send_callback('warning', 'IOT配置不完整，使用模拟数据')
                return

            # 确定目标存储变量
            if stage == 'after_tts':
                target_status = self.device_status_after_tts
                # 清空 A0 准备接收新状态
                self.device_status_after_tts = {}
                target_dict = self.device_status_after_tts
            elif stage == 'after_asr':
                target_status = self.device_status_after_asr
                # 清空 A1 准备接收新状态
                self.device_status_after_asr = {}
                target_dict = self.device_status_after_asr
            else:
                # init 模式不需要存储
                target_dict = {}

            # 如果指定了 device_guids，直接查询这些设备
            if device_guids:
                status_result = await self.iot_service.get_device_status(
                    device_guids,
                    self.iot_config['token']
                )
                if status_result.get('success', False) or status_result.get('rc') == 0:
                    data = status_result.get('data', [])
                    for item in data:
                        device_guid = item.get('deviceId')
                        properties = item.get('properties', {})
                        if device_guid and target_dict is not None:
                            target_dict[device_guid] = properties

                if stage == 'after_tts':
                    # A0: TTS 播放后发送设备状态
                    await self.send_callback('log', {
                        'content': '[A0_TTS] 设备状态',
                        'details': self.device_status_after_tts,
                        'category': 'iot'
                    })
                    await self.send_callback('device_status_update', {
                        'stage': 'after_tts',
                        'a0_tts': self.device_status_after_tts,
                        'timestamp': time.time()
                    })
                elif stage == 'after_asr':
                    # A1: ASR 识别后发送设备状态及变化
                    await self.send_callback('log', {
                        'content': '[A1_ASR] 设备状态',
                        'details': self.device_status_after_asr,
                        'category': 'iot'
                    })
                    # A1: ASR 识别后发送设备状态及变化
                    await self.send_callback('log', {
                        'content': '[A0_A1] 状态变更',
                        'details': self.detect_device_changes(),
                        'category': 'iot'
                    })
                    await self.send_callback('device_status_update', {
                        'stage': 'after_asr',
                        'a0_tts': self.device_status_after_tts,
                        'a1_asr': self.device_status_after_asr,
                        'changes': self.detect_device_changes(),
                        'timestamp': time.time()
                    })
                return

            # 未指定 device_guids，查询家庭所有设备
            if not self.iot_config.get('familyId'):
                if stage == 'init':
                    await self.send_callback('warning', 'IOT配置不完整，使用模拟数据')
                return

            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['familyId'],
                self.iot_config['token']
            )

            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])

                if stage == 'init':
                    await self.send_callback('log', f'发现 {len(devices)} 个设备')

                # 初始化模式：更新 family_devices
                if stage == 'init':
                    self.family_devices = {}
                    for device in devices:
                        device_guid = device.get('deviceGuid')
                        self.family_devices[device_guid] = {
                            'device_guid': device_guid,
                            'category_name': device.get('categoryName'),
                            'nick_name': device.get('name'),
                            'display_type': device.get('displayType'),
                            'device_status': device.get('status')
                        }

                # 批量查询设备状态
                device_guids_to_query = [d.get('deviceGuid') for d in devices if d.get('deviceGuid')]
                if device_guids_to_query:
                    status_result = await self.iot_service.get_device_status(
                        device_guids_to_query,
                        self.iot_config['token']
                    )
                    if status_result.get('success', False) or status_result.get('rc') == 0:
                        data = status_result.get('data', [])
                        for item in data:
                            device_guid = item.get('deviceId')
                            properties = item.get('properties', {})
                            if device_guid and target_dict is not None:
                                target_dict[device_guid] = properties

                if stage == 'init':
                    await self.log_event('iot_query', f'初始化了 {len(self.family_devices)} 个设备信息')
                elif stage == 'after_tts':
                    # A0: TTS 播放后发送设备状态
                    await self.send_callback('log', {
                        'content': '[A0_TTS] 设备状态',
                        'details': self.device_status_after_tts,
                        'category': 'iot'
                    })
                    await self.send_callback('device_status_update', {
                        'stage': 'after_tts',
                        'a0_tts': self.device_status_after_tts,
                        'timestamp': time.time()
                    })
                elif stage == 'after_asr':
                    # A1: ASR 识别后发送设备状态
                    await self.send_callback('log', {
                        'content': '[A1_ASR] 设备状态',
                        'details': self.device_status_after_asr,
                        'category': 'iot'
                    })
                    # A1: ASR 识别后发送状态变更
                    await self.send_callback('log', {
                        'content': '[A0_A1] 状态变更',
                        'details': self.detect_device_changes(),
                        'category': 'iot'
                    })
                    await self.send_callback('device_status_update', {
                        'stage': 'after_asr',
                        'a0_tts': self.device_status_after_tts,
                        'a1_asr': self.device_status_after_asr,
                        'changes': self.detect_device_changes(),
                        'timestamp': time.time()
                    })

        except Exception as e:
            logger.error(f"Failed to refresh device status: {e}")
            if stage == 'init':
                await self.send_callback('warning', f'设备状态初始化失败: {str(e)}')

    def _format_devices_to_markdown(self) -> Optional[str]:
        """将家庭设备信息转换为 Markdown 格式

        Returns:
            设备信息的 Markdown 字符串，如果没有设备则返回 None
        """
        if not self.family_devices:
            return None

        md_lines = ["| 设备类型 | 设备型号| 设备昵称 | 设备GUID |",
                    "|--------|--------|--------|--------|"]

        for device_guid, device_info in self.family_devices.items():
            nick_name = device_info.get('nick_name') or ' '
            category_name = device_info.get('category_name')
            display_type = device_info.get('display_type')

            if category_name == 'AI智能眼镜':
                continue
            md_lines.append(f"| {category_name} | {display_type}| {nick_name}  | {device_guid} |")

        return "\n".join(md_lines)

    # ========================================================================
    # 音频输入层 (Audio Input Layer)
    # ========================================================================

    async def process_audio_input_buffer(
            self,
            audio_data: str,
            audio_format: str = 'webm'
    ) -> AudioInputResult:
        """处理音频输入缓冲"""
        try:
            audio_bytes = base64.b64decode(audio_data)

            await self.log_event('mic_capture', '接收到音频数据', {
                'data_length': len(audio_data),
                'format': audio_format,
                'loop_step': self.loop_step
            })

            self.audio_buffer.add_audio(audio_bytes)

            if not self.audio_buffer.should_process():
                buffer_stats = self.audio_buffer.get_stats()
                logger.debug(f"Audio buffer not ready: {buffer_stats['buffer_size']}/{buffer_stats['target_size']} bytes")
                return AudioInputResult(success=True, audio_bytes=None, audio_duration_s=0.0)

            self._audio_input_event.set()

            combined_audio = self.audio_buffer.get_combined_audio()
            audio_duration_s = len(combined_audio) / 32000
            self.audio_buffer.clear()

            logger.info(f"Audio buffer ready: {len(combined_audio)} bytes, duration: {audio_duration_s:.2f}s")

            return AudioInputResult(success=True, audio_bytes=combined_audio, audio_duration_s=audio_duration_s)

        except Exception as e:
            logger.error(f"Error processing audio input buffer: {e}", exc_info=True)
            return AudioInputResult(success=False, error_message=str(e))

    async def perform_vad_and_asr(
            self,
            audio_bytes: bytes,
            audio_duration_s: float
    ) -> VADASRResult:
        """执行VAD检测和ASR识别"""
        try:
            await self.send_callback('status', '正在进行语音活动检测...')
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            vad_result = await self.vad_service.detect_speech(audio_b64)
            await self.send_callback('vad_result', vad_result)

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
            return VADASRResult(success=False, error_message=str(e))

    # ========================================================================
    # 云端大脑处理层 (Brain Layer)
    # ========================================================================

    async def process_brain(
            self,
            asr_text: str,
            context: Optional[Dict[str, Any]] = None
    ) -> BrainProcessResult:
        """云端大脑处理核心函数

        完整流程：
        1. 处理特殊情况（noise、skip 等）
        2. 记录用户输入到对话历史
        3. 更新设备状态（获取执行后的状态）
        4. 调用 evaluate_round_result 进行评判和推进
        5. 生成下一个测试查询

        Args:
            asr_text: ASR 识别的文本
            context: 上下文信息

        Returns:
            BrainProcessResult: 处理结果
        """
        try:
            context = context or {}
            await self.send_callback('status', '云端大脑正在处理...')
            await self.send_callback('brain_input', asr_text)

            # 特殊标记：噪音重试耗尽后跳过当前轮次
            SKIP_TO_NEXT_QUERY = "<skip_to_next_query>"

            if asr_text == SKIP_TO_NEXT_QUERY:
                await self.send_callback('status', '噪音重试耗尽，生成下一个测试...')
                next_query = await self.tester_service.generate_test_query()
                if next_query and next_query.strip():
                    self.current_query = next_query
                    self.tester_service.add_to_conversation_history('user', next_query)
                    await self.send_callback('ai_response', next_query)
                    return BrainProcessResult(
                        success=True,
                        next_query=next_query,
                        should_continue=True,
                        ai_response=next_query
                    )
                else:
                    return BrainProcessResult(
                        success=True,
                        next_query="",
                        should_continue=False,
                        ai_response="对话完成"
                    )

            if asr_text == '<noise>' or not asr_text or not asr_text.strip():
                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response="检测到噪音或空输入，请重新说话"
                )

            # 1. 记录用户输入到对话历史
            self.tester_service.add_to_conversation_history('assistant', asr_text)

            # 2. ASR 后查询设备状态 (A1)，然后比较 A0 vs A1
            # A0: TTS 播放时已查询的状态 (device_status_after_tts)
            # --> 浏览器播放query以控制设备 -->
            # A1: ASR 识别后查询的状态 (device_status_after_asr)
            device_status_a0 = copy.deepcopy(self.device_status_after_tts)
            await self.refresh_device_status(stage='after_asr')
            device_status_a1 = copy.deepcopy(self.device_status_after_asr)

            # 3. 调用 evaluate_round_result 进行评判和推进
            progress = await self.tester_service.evaluate_round_result(
                asr_text=asr_text,
                device_status_before=device_status_a0,
                device_status_after=device_status_a1
            )

            await self.send_callback('log', f'评判结果: action={progress.action.value}, message={progress.message}')

            # 4. 检查是否需要停止
            if progress.action == NextAction.STOP:
                await self.send_callback('status', '所有测试用例已完成')
                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response="测试完成"
                )

            # 检查是否需要推进到下一个用例
            if progress.action == NextAction.NEXT_CASE:
                await self.send_callback('status', '当前用例已完成，推进到下一个测试用例...')
                # current_index 已在 _execute_progression 中设为 -1
                # generate_test_query 会定位到下一个未执行的用例

            # 5. 生成下一个测试查询
            next_query = await self.tester_service.generate_test_query()

            if next_query and next_query.strip():
                self.current_query = next_query
                self.tester_service.add_to_conversation_history('user', next_query)
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
                })

                return BrainProcessResult(
                    success=True,
                    next_query=next_query,
                    should_continue=True,
                    ai_response=next_query
                )
            else:
                # QueryGenerator 没有生成查询，可能是当前用例已完成
                # 检查评判结果：如果评判认为还需要继续，但查询生成器无法生成查询
                # 这时应该强制将当前用例标记为完成，然后推进到下一个用例
                if progress.action == NextAction.WAIT:
                    # 评判认为需要继续，但查询生成器无法生成新查询
                    # 强制标记当前用例为完成，但需要根据实际步骤结果判断最终状态
                    await self.send_callback('status', '查询生成器无法生成新查询，强制推进到下一个用例...')
                    current_case = self.tester_service.case_manager.get_current_case()
                    if current_case:
                        from app.services.tester.models import TestResultStatus
                        # 根据实际步骤结果判断最终状态
                        all_passed = current_case.is_all_steps_passed()
                        test_status = TestResultStatus.PASS if all_passed else TestResultStatus.FAIL
                        logger.info(f"查询生成器无法生成新查询，用例 {current_case.id} 最终状态: {test_status.value}, "
                                   f"step_pass_results={current_case.step_pass_results}")
                        self.tester_service.case_manager.update_case_result(
                            current_case.id,
                            test_status,
                            current_case.actual_results or ['自动标记为' + ('通过' if all_passed else '失败')],
                            None
                        )
                    # 重置 current_index 以便定位下一个用例
                    self.tester_service.case_manager.current_index = -1
                    # 再次尝试获取下一个用例的查询
                    next_query = await self.tester_service.generate_test_query()
                    if next_query and next_query.strip():
                        self.current_query = next_query
                        self.tester_service.add_to_conversation_history('user', next_query)
                        await self.send_callback('ai_response', next_query)
                        return BrainProcessResult(
                            success=True,
                            next_query=next_query,
                            should_continue=True,
                            ai_response=next_query
                        )
                    else:
                        # 没有更多用例，所有测试已完成
                        await self.send_callback('status', '所有测试用例已完成')
                        return BrainProcessResult(
                            success=True,
                            next_query="",
                            should_continue=False,
                            ai_response='所有测试用例已完成'
                        )

                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response='所有测试已完成'
                )

        except Exception as e:
            logger.error(f"Error in brain processing: {e}", exc_info=True)
            await self.send_callback('error', f'云端大脑处理失败: {str(e)}')
            return BrainProcessResult(success=False, error_message=str(e))

    async def process_brain_with_device_context(self, asr_text: str) -> BrainProcessResult:
        """带设备上下文的云端大脑处理"""
        context = {
            'current_query': self.current_query,
            'loop_step': self.loop_step,
            'device_status': {
                'a0_tts': self.device_status_after_tts,
                'a1_asr': self.device_status_after_asr
            }
        }
        return await self.process_brain(asr_text, context)

    # ========================================================================
    # 音频输出层 (Audio Output Layer)
    # ========================================================================

    async def generate_and_play_audio(
            self,
            text: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> AudioOutputResult:
        """生成TTS音频并发送到前端播放"""
        try:
            if not text or not text.strip():
                await self.send_callback('status', '文本为空，跳过TTS')
                return AudioOutputResult(success=True, text="")

            await self.send_callback('status', '正在生成语音...')
            tts_result = await self.tts_service.generate_speech(text, speaker=self.tts_voice_id)
            self.real_voice_active_time = time.perf_counter()

            await self.log_event('tts_generated', text, {
                'audio_length': len(tts_result),
                'loop_step': self.loop_step
            })

            playback_metadata = metadata or {}
            playback_metadata.update({
                'type': 'tts',
                'text': text,
                'loop_step': self.loop_step
            })

            await self.send_callback('audio_play', tts_result, playback_metadata)

            logger.info(f"TTS generated and sent: {len(tts_result)} bytes for text '{text[:50]}...'")

            return AudioOutputResult(success=True, audio_data=tts_result, text=text)

        except Exception as e:
            logger.error(f"Error generating and playing audio: {e}", exc_info=True)
            await self.send_callback('error', f'TTS生成失败: {str(e)}')
            return AudioOutputResult(success=False, text=text, error_message=str(e))

    async def wait_for_speaker_response(self, wait_time: float = 3.0) -> bool:
        """等待智能音响响应"""
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
        """执行完整的Agent循环步骤"""
        try:
            if self.audio_mode == self.AUDIO_MODE_VAD:
                if self.current_asr_result == '<noise>' and time.perf_counter() - self.real_voice_active_time < 15:
                    return True

            audio_output_result = await self.generate_and_play_audio(self.current_query)

            if not audio_output_result.success:
                logger.error(f"Audio output failed: {audio_output_result.error_message}")
                return False

            # TTS 播放后查询设备状态 (A0) - query 发送后的状态
            await self.refresh_device_status(stage='after_tts')

            await self.wait_for_speaker_response(wait_time=0.0)

            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                await self.send_callback('status', f'TTS播放完成，开始积累 {self.fixed_duration} 秒音频...')
                self._start_buffering()
                return False
            else:
                await self.send_callback('status', '等待音频输入...')
                return True

        except Exception as e:
            logger.error(f"Error in execute_full_loop: {e}", exc_info=True)
            await self.send_callback('error', f'循环执行失败: {str(e)}')
            return False

    async def process_audio(self, audio_data: str, audio_format: str = 'pcm', audio_mode: str = None):
        """处理接收到的音频数据"""
        if not self.is_running:
            return

        mode = audio_mode or self.audio_mode

        try:
            if mode == self.AUDIO_MODE_FIXED_DURATION:
                vad_asr_result = await self._process_fixed_duration_with_buffer(audio_data, audio_format)

                if vad_asr_result is None:
                    return

                if not vad_asr_result.success:
                    await self.send_callback('error', f'固定时长音频处理失败: {vad_asr_result.error_message}')
                    return

                if not vad_asr_result.has_speech or not vad_asr_result.asr_text:
                    await self.send_callback('status', '语音识别结果为空，准备下一轮...')
                    self._start_buffering()
                    return

                # 检测到 noise - 使用测试工程师服务的重试逻辑
                if vad_asr_result.asr_text == '<noise>':
                    next_action = await self.tester_service.on_noise_detected()

                    if next_action == NextAction.RETRY:
                        await self.send_callback('status', '重新播放提示音，请再次说话...')
                        await asyncio.sleep(0.5)

                        audio_output_result = await self.generate_and_play_audio(self.current_query)
                        if audio_output_result.success:
                            # noise 重试时不重置 noise 计数，保留重试状态
                            self._start_buffering(reset_noise_count=False)
                        else:
                            # TTS 播放失败，重置计数器并开始新一轮
                            self.tester_service.reset_noise_retry()
                            self._start_buffering(reset_noise_count=True)
                    else:
                        # 跳过当前用例
                        await self.send_callback('status', '多次检测到噪音，跳过当前轮次...')
                        self.tester_service.reset_noise_retry()

                        # 直接进入下一轮 Brain 处理
                        brain_result = await self.process_brain_with_device_context("<skip_to_next_query>")
                        if brain_result.success and brain_result.next_query:
                            await asyncio.sleep(1.0)
                            await self.execute_full_loop()
                            self._audio_input_event.set()
                        else:
                            await self.send_callback('status', '对话完成，等待新的音频输入...')
                    return

            else:
                # VAD 模式
                input_result = await self.process_audio_input_buffer(audio_data, audio_format)

                if not input_result.success:
                    await self.send_callback('error', f'音频输入处理失败: {input_result.error_message}')
                    return

                if input_result.audio_bytes is None:
                    return

                vad_asr_result = await self.perform_vad_and_asr(
                    input_result.audio_bytes,
                    input_result.audio_duration_s
                )

                if not vad_asr_result.success:
                    await self.send_callback('error', f'VAD/ASR处理失败: {vad_asr_result.error_message}')
                    return

                if not vad_asr_result.has_speech or not vad_asr_result.asr_text:
                    return

                if vad_asr_result.asr_text == '<noise>':
                    await self.send_callback('status', '语音识别结果为<noise>')
                    return

            # 云端大脑处理层
            brain_result = await self.process_brain_with_device_context(vad_asr_result.asr_text)

            if not brain_result.success:
                await self.send_callback('error', f'云端大脑处理失败: {brain_result.error_message}')
                return

            if brain_result.should_continue and brain_result.next_query:
                await asyncio.sleep(1.0)
                await self.execute_full_loop()
                if mode == self.AUDIO_MODE_FIXED_DURATION:
                    self._audio_input_event.set()
            else:
                # 测试完成或对话结束，检查是否所有测试都已完成
                completion_result = await self.tester_service.check_testing_completion()
                if completion_result.completed:
                    # 所有测试完成，生成报告并退出
                    await self.send_callback('status', '所有测试用例已完成')
                    if completion_result.verified_by_llm:
                        await self.send_callback('status', f'LLM验证完成: {completion_result.llm_analysis}')

                    # 生成测试报告
                    report = await self.tester_service.finalize()
                    await self.send_callback('test_report', report.to_dict())
                    await self.send_callback('log', f'测试报告已生成，共 {report.case_statistics.total} 个用例')

                    # 保存报告到数据库
                    await self._save_report_to_database(report)

                    # 标记测试已完成（避免 stop() 时覆盖状态）
                    self._test_completed = True

                    # 发送测试完成通知，前端收到后应关闭连接
                    await self.send_callback('test_completed', {
                        'session_id': self.session_id,
                        'total_cases': report.case_statistics.total,
                        'passed': report.case_statistics.passed,
                        'failed': report.case_statistics.failed,
                        'pass_rate': report.case_statistics.pass_rate
                    })

                    # 停止主循环
                    self.is_running = False
                    self._audio_input_event.set()  # 唤醒主循环以退出
                else:
                    await self.send_callback('status', '对话完成，等待新的音频输入...')

        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            await self.send_callback('error', f'音频处理失败: {str(e)}')

    def _start_buffering(self, reset_noise_count: bool = True):
        """开始积累音频 buffer"""
        self.audio_buffer = []
        self.buffer_start_time = time.perf_counter()
        self.is_buffering = True
        if reset_noise_count:
            self.tester_service.reset_noise_retry()
        logger.info(f"Started buffering audio, duration target: {self.fixed_duration}s")

    def _stop_buffering(self):
        """停止积累音频 buffer"""
        self.is_buffering = False
        logger.info("Stopped buffering audio")

    async def _process_fixed_duration_with_buffer(self, audio_data: str, audio_format: str = 'pcm') -> Optional[VADASRResult]:
        """固定时长模式：后端控制 buffer 积累和处理"""
        try:
            if not self.is_buffering:
                # logger.debug("Not in buffering state, ignoring audio data")
                return None

            audio_bytes = base64.b64decode(audio_data)

            async with self.buffer_lock:
                self.audio_buffer.append(audio_bytes)
                total_bytes = sum(len(chunk) for chunk in self.audio_buffer)

            current_duration = total_bytes / 32000

            await self.send_callback('buffer_status', {
                'current_duration': round(current_duration, 2),
                'target_duration': self.fixed_duration,
                'is_buffering': True
            })

            # logger.debug(f"Buffer: {current_duration:.2f}s / {self.fixed_duration}s")

            if current_duration < self.fixed_duration:
                return None

            self._stop_buffering()

            await self.send_callback('status', f'音频积累完成: {current_duration:.2f}秒，开始识别...')

            async with self.buffer_lock:
                combined_audio = b''.join(self.audio_buffer)
                self.audio_buffer = []

            await self.log_event('mic_capture', '固定时长音频积累完成', {
                'audio_bytes': len(combined_audio),
                'duration_s': current_duration,
                'format': audio_format,
                'loop_step': self.loop_step
            })

            wav_audio_b64 = AudioConverter.pcm_to_wav_base64(combined_audio)
            asr_result = await self.asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

            await self.send_callback('transcript_final', asr_result, {
                'confidence': 0.9,
                'loop_step': self.loop_step,
                'audio_duration_s': current_duration,
                'audio_mode': 'fixed_duration'
            })

            asr_text = asr_result.strip()

            if not asr_text:
                return VADASRResult(success=True, has_speech=False, asr_text="", speech_ratio=0.0)

            self.current_asr_result = asr_text
            if asr_text != '<noise>':
                self.current_asr_true_result = asr_text
                self.real_voice_active_time = time.perf_counter()

            logger.info(f"Fixed duration ASR result: '{asr_text}'")

            return VADASRResult(
                success=True,
                has_speech=True,
                asr_text=asr_text,
                speech_ratio=1.0,
                confidence=0.9
            )

        except Exception as e:
            logger.error(f"Error processing fixed duration audio with buffer: {e}", exc_info=True)
            await self.send_callback('error', f'固定时长音频处理失败: {str(e)}')
            return VADASRResult(success=False, error_message=str(e))

    def detect_device_changes(self) -> Dict[str, Any]:
        """检测设备状态变化

        使用 jsondiff 对比 A0 (TTS后) 和 A1 (ASR后) 的设备属性变化。
        """
        changes = {}
        for device_guid in self.device_status_after_asr:
            a1_props = self.device_status_after_asr.get(device_guid, {})
            a0_props = self.device_status_after_tts.get(device_guid, {})

            if a1_props != a0_props:
                # 使用 jsondiff 计算详细差异
                diff = None
                if HAS_JSONDIFF:
                    diff = jsondiff.diff(a0_props, a1_props)

                changes[device_guid] = {
                    'has_change': True,
                    'a1_asr': a1_props,
                    'a0_tts': a0_props,
                    'diff': diff
                }
            else:
                changes[device_guid] = {'has_change': False}

        return changes

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

            self.tester_service.add_to_conversation_history('user', message)

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

        if hasattr(self, '_audio_input_event'):
            self._audio_input_event.set()

        await self.send_callback('status', '智能体已停止')

        self.device_status_after_tts = {}
        self.device_status_after_asr = {}
        self.loop_step = 0

        if hasattr(self, 'audio_buffer'):
            self.audio_buffer.clear()

        # 停止测试工程师服务
        await self.tester_service.stop()

        # 更新数据库任务状态为 stopped（仅当测试未正常完成时）
        # 如果测试已正常完成（状态为 completed），不应覆盖为 stopped
        if not self._test_completed:
            await self._update_task_status_stopped()
        else:
            logger.info(f"Test already completed, skip updating status to stopped")

        logger.info(f"Agent stopped for session {self.session_id}")

    async def _update_task_status_stopped(self) -> bool:
        """更新任务状态为 stopped"""
        if not self.job_instance_id:
            return False

        try:
            url = f"{self.backend_service.backend_url}/api/agentic-test/test-tasks/stop-by-job-instance/"

            payload = {"job_instance_id": self.job_instance_id}

            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"Task status updated to stopped")
                    return True
                else:
                    logger.warning(f"Failed to update task status: {data.get('message')}")
                    return False

        except Exception as e:
            logger.error(f"Error updating task status to stopped: {e}", exc_info=True)
            return False

    async def _save_report_to_database(self, report) -> bool:
        """保存测试报告到数据库

        通过后端 API 更新 TestTask 的报告数据。
        使用 job_instance_id（等于 session_id）查找任务。

        Args:
            report: TestReport 对象

        Returns:
            是否保存成功
        """
        if not self.job_instance_id:
            logger.warning("No job_instance_id, skip saving report to database")
            return False

        try:
            # 调用后端 API 保存报告
            url = f"{self.backend_service.backend_url}/api/agentic-test/test-tasks/complete-by-job-instance/"

            # 生成报告摘要
            summary_parts = []
            stats = report.case_statistics
            summary_parts.append(f"总用例数: {stats.total}")
            summary_parts.append(f"通过: {stats.passed}")
            summary_parts.append(f"失败: {stats.failed}")
            summary_parts.append(f"通过率: {stats.pass_rate:.1f}%")
            result_summary = ", ".join(summary_parts)

            payload = {
                "job_instance_id": self.job_instance_id,
                "status": "completed",
                "report_data": report.to_dict(),
                "result_summary": result_summary
            }

            logger.info(f"Saving report to database with job_instance_id={self.job_instance_id}")

            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"Report saved to database successfully")
                    return True
                else:
                    logger.error(f"Failed to save report: {data.get('message')}")
                    return False

        except Exception as e:
            logger.error(f"Error saving report to database: {e}", exc_info=True)
            return False

    async def _update_task_job_info(self) -> bool:
        """更新任务状态为 running

        在任务启动时调用，通过 job_instance_id 精确查找任务并更新状态。

        Returns:
            是否更新成功
        """
        try:
            url = f"{self.backend_service.backend_url}/api/agentic-test/test-tasks/update-job-info/"

            payload = {
                "job_instance_id": self.job_instance_id
            }

            logger.info(f"Updating job info: job_instance_id={self.job_instance_id}")

            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"Job info updated successfully")
                    return True
                else:
                    logger.warning(f"Failed to update job info: {data.get('message')}")
                    return False

        except Exception as e:
            logger.error(f"Error updating job info: {e}", exc_info=True)
            return False

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