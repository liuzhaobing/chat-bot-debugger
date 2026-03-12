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


# 特殊标记：噪音重试耗尽后跳过当前轮次，直接生成下一个 query
SKIP_TO_NEXT_QUERY = "<skip_to_next_query>"


class AgenticTestAgent:
    """Agentic Test 智能体主循环

    固定时长音频采集方案：
    - 前端持续发送音频数据给后端
    - 后端在发送 TTS 时开始积累音频 buffer
    - 积累固定时长（默认20秒）后进行 ASR 识别
    - 实现一人一轮的交互模式
    """

    # App IDs
    JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"
    QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

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
            fixed_duration: float = None,
            audio_mode: str = None
    ):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self.current_query = ""
        self.current_asr_result = ""
        self.real_voice_active_time = 0.0

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

        # 测试用例
        self.test_cases: List = [
            {
                "id": "APPL-LIGHT-001",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "语音打开一体机内部灯光",
                "type": "Functional",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端（如App/音箱/眼镜）账号已绑定该设备并具备控制权限",
                    "设备当前无故障告警（如门故障/控制板故障）"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "通过语音发出指令：\"打开一体机灯\"（或\"打开烤箱灯/打开内部照明\"），识别到目标设备为CQ38-i7",
                    "等待语音平台下发物模型指令 lightControl，参数 lightSwitch=1，controlTerminalType=语音端类型（如有）",
                    "调用查询状态接口（如设备状态查询/灯状态上报）或通过设备面板/摄像观察确认灯光状态"
                ],
                "expect_results": [
                    "语音识别成功并命中设备CQ38-i7",
                    "下发 lightControl(lightSwitch=1) 成功，平台返回成功/设备ACK成功",
                    "一体机内部照明灯点亮，灯状态从0变为1（或等效状态上报）"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-002",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "语音关闭一体机内部灯光",
                "type": "Functional",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端账号已绑定该设备并具备控制权限",
                    "一体机内部灯当前为开启状态（lightSwitch=1）"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "通过语音发出指令：\"关闭一体机灯\"（或\"关闭烤箱灯/关闭内部照明\"）",
                    "等待语音平台下发物模型指令 lightControl，参数 lightSwitch=0",
                    "查询/观察确认灯光状态"
                ],
                "expect_results": [
                    "语音识别成功并命中设备CQ38-i7",
                    "下发 lightControl(lightSwitch=0) 成功",
                    "一体机内部照明灯熄灭，灯状态从1变为0（或等效状态上报）"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-003",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "语音重复打开：灯已开启时再次打开应幂等成功",
                "type": "State",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端账号已绑定该设备并具备控制权限",
                    "灯已开启（lightSwitch=1）"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "语音指令：\"打开一体机灯\"",
                    "观察平台返回与设备状态上报"
                ],
                "expect_results": [
                    "下发 lightControl(lightSwitch=1) 成功或返回已是目标状态（均视为成功）",
                    "灯保持开启状态不闪烁、不重启、不出现异常告警",
                    "状态上报保持 lightSwitch=1（或等效）"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-004",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "语音重复关闭：灯已关闭时再次关闭应幂等成功",
                "type": "State",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端账号已绑定该设备并具备控制权限",
                    "灯已关闭（lightSwitch=0）"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "语音指令：\"关闭一体机灯\"",
                    "观察平台返回与设备状态上报"
                ],
                "expect_results": [
                    "下发 lightControl(lightSwitch=0) 成功或返回已是目标状态（均视为成功）",
                    "灯保持关闭状态",
                    "状态上报保持 lightSwitch=0（或等效）"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-005",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "语音快速切换：连续开->关->开，最终状态应为开启",
                "type": "State",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端账号已绑定该设备并具备控制权限"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "在5秒内依次语音下发：\"打开一体机灯\"、\"关闭一体机灯\"、\"打开一体机灯\"",
                    "等待所有指令下发完成并观察设备最终状态上报"
                ],
                "expect_results": [
                    "三次语音均命中设备CQ38-i7且均成功下发对应 lightControl 指令",
                    "设备不出现卡死/重启/异常告警",
                    "最终灯状态为开启（lightSwitch=1），状态上报与实际一致"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-006",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "边界：语音指令包含设备别名/型号混合表达仍能控制灯光",
                "type": "EdgeCase",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端账号已绑定该设备并具备控制权限",
                    "家庭内存在多台一体机（例如CQ38-i7、CQ01-i1、CQ9878A）以验证消歧"
                ],
                "device_guids": [
                    "38-i750411c84f366",
                    "38-i750411c84f366"
                ],
                "steps": [
                    "语音指令：\"打开CQ38-i7灯\" 或 \"打开CQ38灯\" 或 \"打开一体机CQ38-i7的灯\"",
                    "观察语音端是否提示命中CQ38-i7并执行",
                    "查询/观察灯状态"
                ],
                "expect_results": [
                    "语音NLP正确消歧并命中CQ38-i7（deviceGuid=38-i750411c84f366）",
                    "下发 lightControl(lightSwitch=1) 成功",
                    "CQ38-i7灯光状态变为开启"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-007",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "错误处理：家庭存在多台一体机但用户说\"打开一体机灯\"应触发澄清/选择",
                "type": "Error",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "同家庭存在其他一体机设备（如deviceGuid=Q01i16879c4bd72e5、9878Ac8478c00eca5）",
                    "语音端账号已绑定这些设备或至少能被语音端发现"
                ],
                "device_guids": [
                    "38-i750411c84f366",
                    "Q01i16879c4bd72e5",
                    "9878Ac8478c00eca5"
                ],
                "steps": [
                    "语音指令：\"打开一体机灯\"（不指明具体设备）",
                    "观察语音端交互：是否要求选择设备/确认目标",
                    "在澄清后选择CQ38-i7并确认执行（如语音回复\"打开CQ38-i7\"）"
                ],
                "expect_results": [
                    "当目标不唯一时，语音端不应误控其他一体机",
                    "语音端发起澄清或提供可选设备列表",
                    "确认CQ38-i7后，下发 lightControl(lightSwitch=1) 成功且仅CQ38-i7灯被打开"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-008",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "错误处理：设备离线时语音打开灯应失败并给出可理解提示",
                "type": "Error",
                "preconditions": [
                    "将CQ38-i7断网或断电使其离线（deviceGuid=38-i750411c84f366）",
                    "语音端账号仍绑定该设备"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "语音指令：\"打开一体机CQ38-i7的灯\"",
                    "观察语音端提示与平台下发结果（超时/离线错误）"
                ],
                "expect_results": [
                    "平台下发失败，返回设备离线/不可达/超时等明确错误码或错误信息",
                    "语音端提示用户设备离线，未改变设备灯光状态",
                    "不应出现“已打开”等误导性成功播报"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-009",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "错误处理：无权限账号尝试语音控制灯光应被拒绝",
                "type": "Security",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "使用未被家庭授权/未共享该设备的账号登录语音端",
                    "该账号可发起语音但无设备控制权限"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "未授权账号语音指令：\"打开CQ38-i7灯\"",
                    "观察平台鉴权与语音端提示"
                ],
                "expect_results": [
                    "平台鉴权失败（如403/无权限），不下发或下发被拒绝",
                    "语音端提示无权限/需要授权/无法控制",
                    "CQ38-i7灯光状态不发生变化"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-010",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "安全：语音文本注入/特殊字符不应导致异常下发或越权（lightSwitch仅允许0/1）",
                "type": "Security",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "语音端支持文本指令入口（如输入框/快捷命令）或可模拟ASR结果"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "通过文本指令输入异常内容（示例）：\"打开灯;lightSwitch=2\"、\"打开灯{\"lightSwitch\":999}\"、\"<script>alert(1)</script>打开灯\"",
                    "观察语音解析结果与实际下发到物模型的参数",
                    "查询/观察设备灯状态与平台日志"
                ],
                "expect_results": [
                    "解析/参数校验生效：仅允许 lightSwitch 取值0或1，异常值被拒绝或纠正为合法指令",
                    "平台与语音端不出现脚本执行/崩溃/日志污染等安全问题",
                    "设备仅在合法指令下改变灯状态"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-011",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "性能：语音开灯端到端响应时间满足要求（如<=3秒，可配置阈值）",
                "type": "Performance",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "网络状况正常（语音端与设备均可稳定访问平台）",
                    "已定义验收阈值（例如：从语音结束到灯亮<=3秒）"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "开始计时，在语音端发出\"打开CQ38-i7灯\"并结束说话",
                    "记录语音识别完成时间、平台下发时间、设备ACK时间、灯亮时间（以日志或观测为准）",
                    "重复测试10次取P95"
                ],
                "expect_results": [
                    "10次均成功控制灯光开启",
                    "端到端时延P95满足阈值（如<=3秒；以项目验收标准为准）",
                    "无明显超时、重试风暴或丢指令现象"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            },
            {
                "id": "APPL-LIGHT-012",
                "module": "一体机 - 灯光控制(lightControl)",
                "title": "状态联动：执行pause/continue/stop等工作控制后，灯光语音控制仍可用且状态不被错误重置",
                "type": "State",
                "preconditions": [
                    "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
                    "设备可进入工作态（可用startWork启动任一模式，或使用设备面板启动）",
                    "语音端账号已绑定该设备并具备控制权限"
                ],
                "device_guids": [
                    "38-i750411c84f366"
                ],
                "steps": [
                    "启动一体机工作（startWork或实际启动），确认设备处于运行中",
                    "语音指令：\"打开一体机灯\"，确认灯亮",
                    "语音/APP触发暂停（pauseWork），再语音指令：\"关闭一体机灯\"",
                    "语音/APP触发继续（continueWork），再语音指令：\"打开一体机灯\"",
                    "语音/APP触发停止（stopWork），确认灯状态与最后一次指令一致"
                ],
                "expect_results": [
                    "在运行/暂停/继续/停止各状态下，lightControl均可正常下发并生效",
                    "暂停/继续/停止不会将灯状态错误重置（除非产品定义必须重置并有明确说明/上报）",
                    "每次操作均有明确ACK/状态上报，且与实际灯光一致"
                ],
                "actual_results": [],
                "test_result": "NotRun"
            }
        ]

        # 当前测试用例
        self.current_case_index = 0
        self.current_case: Dict = {}

        # 固定时长音频缓冲区
        self.audio_buffer: List[bytes] = []
        self.buffer_start_time: Optional[float] = None  # 开始积累的时间
        self.is_buffering: bool = False  # 是否正在积累
        self.buffer_lock = asyncio.Lock()  # 缓冲区锁

        # Noise 重试机制
        self.noise_retry_count: int = 0  # 当前 noise 重试次数
        self.max_noise_retry: int = 2  # 最大重试次数（总共3次机会）

        # 音频输入等待事件
        self._audio_input_event = asyncio.Event()  # 音频输入完成事件

        # 对话历史管理（最多保留最近20轮）
        self.conversation_history: List[Dict[str, str]] = []
        self.max_conversation_history_length = 20

        logger.info(
            f"AgenticTestAgent initialized for session {session_id} with IOT config: "
            f"env={self.iot_config.get('env')}, has_token={bool(self.iot_config.get('token'))}, "
            f"fixed_duration={self.fixed_duration}s"
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
        await self.send_callback('ai_response', initial_query)
        await self.send_callback('log', f'开始处理查询: {initial_query}')
        await self.send_callback('status', '智能体循环已启动')

        try:
            # 初始化设备状态
            await self.initialize_device_status()

            # 初始化当前测试用例
            self.current_case = self.test_cases[self.current_case_index]

            # 固定时长模式：先播放初始 TTS，然后开始积累音频
            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                await self.send_callback('status', '固定时长模式：播放初始 TTS...')
                await self.execute_full_loop()  # 播放 TTS 并启动 buffering

            # 开始主循环
            while self.is_running and self.loop_step < self.max_loop_steps:
                try:
                    self.loop_step += 1
                    await self.send_callback('status', f'执行循环步骤 {self.loop_step}')

                    if self.audio_mode == self.AUDIO_MODE_VAD:
                        # VAD 模式：执行完整的Agent循环
                        should_continue = await self.execute_full_loop()

                        if not should_continue:
                            # 等待音频输入，保持 is_running 为 True
                            await self.send_callback('status', '等待新的音频输入...')
                            # 清除事件标志，等待 process_audio 触发
                            self._audio_input_event.clear()
                            # 等待音频输入事件，最多等待 200 秒
                            try:
                                await asyncio.wait_for(self._audio_input_event.wait(), timeout=200.0)
                                await self.send_callback('status', '收到音频输入，继续处理...')
                            except asyncio.TimeoutError:
                                await self.send_callback('status', '等待音频超时，继续监听...')
                                continue
                    else:
                        # 固定时长模式：等待前端持续发送音频
                        # process_audio 会处理音频累积、ASR、Brain 处理和下一轮 TTS
                        # 主循环只需要保持运行状态，等待停止信号
                        await self.send_callback('status', f'固定时长模式：等待音频输入（目标 {self.fixed_duration} 秒）...')
                        self._audio_input_event.clear()
                        try:
                            # 等待一个较长的超时时间，让 process_audio 有足够时间处理
                            await asyncio.wait_for(self._audio_input_event.wait(), timeout=600.0)
                        except asyncio.TimeoutError:
                            # 超时后检查是否仍在运行
                            if self.is_running:
                                await self.send_callback('status', '等待音频超时，继续等待...')
                                continue
                            else:
                                break

                    await asyncio.sleep(1.0)  # 短暂休眠，避免 CPU 空转

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
            self._stop_buffering()  # 确保停止 buffering
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
                    device_status = device.get('status')
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
            if asr_text == SKIP_TO_NEXT_QUERY:
                # 噪音重试耗尽，直接生成下一个 query
                await self.send_callback('status', '噪音重试耗尽，生成下一个测试...')
                judge_result = {'should_continue': True}
                next_query = await self.generate_next_query(judge_result, SKIP_TO_NEXT_QUERY)
                if next_query and next_query.strip():
                    self.current_query = next_query
                    self._add_to_conversation_history('user', next_query)
                    await self.send_callback('ai_response', next_query)
                    return BrainProcessResult(
                        success=True,
                        next_query=next_query,
                        should_continue=True,
                        ai_response=next_query,
                        analysis={'type': 'skip_to_next_after_noise_retry'}
                    )
                else:
                    return BrainProcessResult(
                        success=True,
                        next_query="",
                        should_continue=False,
                        ai_response="对话完成",
                        analysis={'type': 'skip_to_next_no_more_queries'}
                    )

            if asr_text == '<noise>' or not asr_text or not asr_text.strip():
                return BrainProcessResult(
                    success=True,
                    next_query="",
                    should_continue=False,
                    ai_response="检测到噪音或空输入，请重新说话",
                    analysis={'type': 'noise_or_empty_detected'}
                )

            # 记录用户输入（ASR识别的文本）
            self._add_to_conversation_history('assistant', asr_text)

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
                self._add_to_conversation_history('user', next_query)
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
            await self.wait_for_speaker_response(wait_time=0.0)

            # 根据音频模式决定是否继续循环
            if self.audio_mode == self.AUDIO_MODE_FIXED_DURATION:
                # 固定时长模式：播放 TTS 后开始积累音频 buffer
                await self.send_callback('status', f'TTS播放完成，开始积累 {self.fixed_duration} 秒音频...')
                self._start_buffering()  # 开始积累音频 buffer
                return False  # 返回 False，让主循环等待音频输入
            else:
                # VAD 模式：继续循环，持续处理音频
                await self.send_callback('status', '等待音频输入...')
                return True

        except Exception as e:
            logger.error(f"Error in execute_full_loop: {e}", exc_info=True)
            await self.send_callback('error', f'循环执行失败: {str(e)}')
            return False

    async def process_audio(self, audio_data: str, audio_format: str = 'pcm', audio_mode: str = None):
        """
        处理接收到的音频数据

        根据 audio_mode 选择不同的处理方式：
        - 'vad': VAD 方案，音频缓冲 -> VAD检测 -> ASR识别
        - 'fixed_duration': 固定时长方案，后端控制 buffer 积累时机

        固定时长模式流程：
        1. TTS 播放完成后设置 is_buffering=True，开始积攒 buffer
        2. 前端持续发送音频，后端累积到 audio_buffer
        3. 累积时长达到 fixed_duration 后停止 buffering，进行 ASR 识别
        4. ASR 识别完成 -> Brain 处理 -> TTS 播放 -> 回到步骤1

        Args:
            audio_data: Base64编码的音频数据
            audio_format: 音频格式，默认 pcm
            audio_mode: 音频处理模式，如果为 None 则使用实例的 audio_mode
        """
        if not self.is_running:
            return

        # 确定使用哪种音频处理模式
        mode = audio_mode or self.audio_mode

        try:
            if mode == self.AUDIO_MODE_FIXED_DURATION:
                # ===== 固定时长方案: 后端控制 buffer 积累 =====
                vad_asr_result = await self._process_fixed_duration_with_buffer(audio_data, audio_format)

                if vad_asr_result is None:
                    # buffer 未满，继续累积
                    return

                if not vad_asr_result.success:
                    await self.send_callback('error', f'固定时长音频处理失败: {vad_asr_result.error_message}')
                    return

                # 未检测到语音或结果为空
                if not vad_asr_result.has_speech or not vad_asr_result.asr_text:
                    await self.send_callback('status', '语音识别结果为空，准备下一轮...')
                    # 重置 buffering 状态，等待下一轮
                    self._start_buffering()
                    return

                # 检测到 noise - 固定时长模式的重试逻辑
                if vad_asr_result.asr_text == '<noise>':
                    self.noise_retry_count += 1
                    await self.send_callback('status', f'检测到噪音 ({self.noise_retry_count}/{self.max_noise_retry + 1})')

                    if self.noise_retry_count <= self.max_noise_retry:
                        # 未达到最大重试次数，重新播放 TTS 并开始积累
                        await self.send_callback('status', '重新播放提示音，请再次说话...')
                        await asyncio.sleep(0.5)  # 短暂延迟

                        # 重新播放当前 TTS
                        audio_output_result = await self.generate_and_play_audio(self.current_query)
                        if audio_output_result.success:
                            # 播放成功，开始新的 buffer 积累（不重置 noise 计数器）
                            self._start_buffering(reset_noise_count=False)
                        else:
                            # 播放失败，重置计数器并开始新一轮
                            await self.send_callback('error', 'TTS播放失败，跳过当前轮次')
                            self._start_buffering(reset_noise_count=True)
                    else:
                        # 达到最大重试次数，放弃当前轮次，生成下一个 query
                        await self.send_callback('status', '多次检测到噪音，跳过当前轮次，生成下一个测试...')
                        self.noise_retry_count = 0  # 重置计数器

                        # 直接进入下一轮 Brain 处理（使用特殊标记生成下一个 query）
                        brain_result = await self.process_brain_with_device_context(SKIP_TO_NEXT_QUERY)
                        if brain_result.success and brain_result.next_query:
                            await asyncio.sleep(1.0)
                            await self.execute_full_loop()
                            self._audio_input_event.set()
                        else:
                            await self.send_callback('status', '对话完成，等待新的音频输入...')
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
                # 固定时长模式：触发事件让主循环知道处理已完成
                if mode == self.AUDIO_MODE_FIXED_DURATION:
                    self._audio_input_event.set()
            else:
                await self.send_callback('status', '对话完成，等待新的音频输入...')

        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            await self.send_callback('error', f'音频处理失败: {str(e)}')

    def _start_buffering(self, reset_noise_count: bool = True):
        """
        开始积累音频 buffer

        在 TTS 播放完成后调用，表示后端准备好接收用户的语音输入。

        Args:
            reset_noise_count: 是否重置 noise 重试计数器
                - True: 新的一轮对话，重置计数器
                - False: noise 重试场景，保持当前计数器
        """
        self.audio_buffer = []
        self.buffer_start_time = time.perf_counter()
        self.is_buffering = True
        if reset_noise_count:
            self.noise_retry_count = 0
        logger.info(f"Started buffering audio, duration target: {self.fixed_duration}s, noise_retry: {self.noise_retry_count}/{self.max_noise_retry}")
        # 注意: send_callback 是异步的，这里只是设置状态，状态变化会通过其他方式通知前端

    def _stop_buffering(self):
        """
        停止积累音频 buffer
        """
        self.is_buffering = False
        logger.info("Stopped buffering audio")

    async def _process_fixed_duration_with_buffer(self, audio_data: str, audio_format: str = 'pcm') -> Optional[VADASRResult]:
        """
        固定时长模式：后端控制 buffer 积累和处理

        Args:
            audio_data: Base64编码的音频数据
            audio_format: 音频格式

        Returns:
            VADASRResult: 处理结果，如果 buffer 未满返回 None
        """
        try:
            # 如果不在 buffering 状态，忽略音频数据
            if not self.is_buffering:
                logger.debug("Not in buffering state, ignoring audio data")
                return None

            # 解码 Base64 音频数据
            audio_bytes = base64.b64decode(audio_data)

            # 累积到 buffer
            async with self.buffer_lock:
                self.audio_buffer.append(audio_bytes)
                total_bytes = sum(len(chunk) for chunk in self.audio_buffer)

            # 计算当前 buffer 时长（16kHz, 16bit, mono = 32000 bytes/sec）
            current_duration = total_bytes / 32000

            await self.send_callback('buffer_status', {
                'current_duration': round(current_duration, 2),
                'target_duration': self.fixed_duration,
                'is_buffering': True
            })

            logger.debug(f"Buffer: {current_duration:.2f}s / {self.fixed_duration}s")

            # 检查是否达到目标时长
            if current_duration < self.fixed_duration:
                return None  # 继续累积

            # 达到目标时长，停止 buffering 并处理
            self._stop_buffering()

            await self.send_callback('status', f'音频积累完成: {current_duration:.2f}秒，开始识别...')

            # 合并 buffer 中的音频
            async with self.buffer_lock:
                combined_audio = b''.join(self.audio_buffer)
                self.audio_buffer = []

            await self.log_event('mic_capture', '固定时长音频积累完成', {
                'audio_bytes': len(combined_audio),
                'duration_s': current_duration,
                'format': audio_format,
                'loop_step': self.loop_step
            })

            # 直接进行 ASR 识别（跳过 VAD）
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
                speech_ratio=1.0,
                confidence=0.9
            )

        except Exception as e:
            logger.error(f"Error processing fixed duration audio with buffer: {e}", exc_info=True)
            await self.send_callback('error', f'固定时长音频处理失败: {str(e)}')
            return VADASRResult(
                success=False,
                error_message=str(e)
            )

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
        self.current_case = self.test_cases[self.current_case_index]
        try:
            if not judge_result.get('should_continue', True):
                return ""

            suggested_action = judge_result.get('suggested_action', '')
            if suggested_action == 'end_conversation':
                return ""

            # 使用全局对话历史
            conversation_history_context = self._get_conversation_history_context()

            # 使用家庭设备列表上下文
            family_devices_context = self._get_family_devices_context()

            # 格式化当前测试用例为 markdown 表格
            current_case_context = self._format_current_case_context()

            query_result = await self.call_query_generator_app(
                message="\n\n".join([
                    "**当前测试用例**：", current_case_context,
                    "**家庭设备列表**：", family_devices_context,
                    "**对话历史**：", conversation_history_context,
                    "**当前设备状态**：", []
                ])
            )

            await self.log_event('query_generated', json.dumps(query_result, ensure_ascii=False), {
                'app_id': self.QUERY_GENERATOR_APP_ID,
                'loop_step': self.loop_step
            })

            await self.send_callback('query_generated', query_result)

            if not query_result.get('should_continue', True):
                self.current_case_index += 1
                await self.send_callback('log', f'准备加载下一条测试用例：{self.current_case_index}.{self.test_cases[self.current_case_index].get("title")}')

            next_query = query_result.get('user_input', '')

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
            role_name = "测试员" if msg['role'] == 'user' else "被测系统"
            lines.append(f"- {role_name}: {msg['content']}")

        return "\n".join(lines)

    def _clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info(f"Conversation history cleared for session {self.session_id}")

    def _get_family_devices_context(self) -> str:
        """
        获取家庭设备列表的文本格式，用于传递给LLM

        Returns:
            格式化的设备列表文本（markdown表格）
        """
        if not self.family_devices:
            return "无设备"

        lines = ["| 设备GUID | 设备类型 | 设备标准型号 | 设备昵称 | 设备状态 |", "|:---------|:---------|:---------|:---------|:---------|"]
        for device_guid, device in self.family_devices.items():
            nick_name = device.get('nick_name', 'N/A') or 'N/A'
            category_name = device.get('category_name', 'N/A') or 'N/A'
            display_type = device.get('display_type', 'N/A') or 'N/A'
            device_status = device.get('device_status')
            device_status = '在线' if device_status else '离线'
            lines.append(f"| {device_guid} | {category_name} | {display_type} | {nick_name} | {device_status} |")

        return "\n".join(lines)

    def _format_current_case_context(self) -> str:
        """
        格式化当前测试用例为 markdown 表格

        Returns:
            格式化的测试用例文本（markdown表格）
        """
        if not self.current_case:
            return "无用例"

        # 定义表格列
        headers = ["id", "module", "title", "type", "preconditions", "device_guids",
                   "steps", "expect_results", "actual_results", "test_result"]
        header_names = {
            "id": "用例ID",
            "module": "模块",
            "title": "标题",
            "type": "类型",
            "preconditions": "前置条件",
            "device_guids": "要操控设备的deviceGuid",
            "steps": "测试步骤",
            "expect_results": "预期结果",
            "actual_results": "实际结果",
            "test_result": "测试结果"
        }

        # 构建表头
        lines = ["| " + " | ".join([header_names.get(h, h) for h in headers]) + " |"]
        lines.append("|" + "|".join([":---" for _ in headers]) + "|")

        # 构建数据行
        row_values = []
        for h in headers:
            value = self.current_case.get(h, 'N/A')
            if value is None:
                value = 'N/A'
            elif isinstance(value, list):
                value = '<br>'.join(str(v) for v in value)
            else:
                value = str(value)
            row_values.append(value)
        lines.append("| " + " | ".join(row_values) + " |")

        return "\n".join(lines)

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
