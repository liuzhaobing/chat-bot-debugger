"""
Agentic Test Agent 服务
从 backend/agentic_test/agent_loop.py 迁移
核心业务逻辑
"""
import asyncio
import json
import logging
import base64
from typing import Optional, Callable, Dict, Any
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
from app.utils.audio_utils import AudioConverter
from app.config import settings

logger = logging.getLogger(__name__)


class AgenticTestAgent:
    """Agentic Test 智能体主循环"""

    # App IDs
    JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"
    QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

    def __init__(
        self,
        session_id: str,
        send_callback: Callable,
        iot_config: Optional[Dict[str, str]] = None
    ):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self.current_query = ""
        self.loop_step = 0
        self.max_loop_steps = 10

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

        # 设备状态缓存
        self.previous_device_status: Dict = {}
        self.current_device_status: Dict = {}

        logger.info(
            f"AgenticTestAgent initialized for session {session_id} with IOT config: "
            f"env={self.iot_config.get('env')}, has_token={bool(self.iot_config.get('token'))}"
        )

    async def start_loop(self, initial_query: str, iot_config: Optional[Dict[str, str]] = None):
        """启动智能体循环"""
        self.is_running = True
        self.current_query = initial_query
        self.loop_step = 0

        if iot_config:
            self.iot_config.update(iot_config)

        await self.log_event('user_query', initial_query)
        await self.send_callback('log', f'开始处理查询: {initial_query}')
        await self.send_callback('status', '智能体循环已启动')

        try:
            # 初始化设备状态
            await self.initialize_device_status()

            # 开始主循环
            while self.is_running and self.loop_step < self.max_loop_steps:
                try:
                    self.loop_step += 1
                    await self.send_callback('status', f'执行循环步骤 {self.loop_step}')

                    # 执行完整的Agent循环
                    should_continue = await self.execute_full_loop()

                    if not should_continue:
                        await self.send_callback('status', '循环完成，等待新的音频输入...')
                        break

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

                for device in devices[:3]:
                    device_guid = device.get('deviceGuid')
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

    async def execute_full_loop(self) -> bool:
        """执行完整的Agent循环步骤"""
        try:
            # Step 1: 生成TTS音频
            await self.send_callback('status', '正在生成语音...')
            tts_result = await self.tts_service.generate_speech(self.current_query)
            await self.log_event('tts_generated', self.current_query, {
                'audio_length': len(tts_result),
                'loop_step': self.loop_step
            })

            # Step 2: 发送音频到前端播放
            await self.send_callback('audio_play', tts_result, {
                'type': 'tts',
                'text': self.current_query,
                'loop_step': self.loop_step
            })

            # Step 3: 等待智能音响回应
            await self.send_callback('status', '等待智能音响回应...')
            await asyncio.sleep(3.0)

            # Step 4: 等待音频输入
            await self.send_callback('status', '等待音频输入...')
            return False  # 等待音频输入

        except Exception as e:
            logger.error(f"Error in execute_full_loop: {e}", exc_info=True)
            await self.send_callback('error', f'循环执行失败: {str(e)}')
            return False

    async def process_audio(self, audio_data: str, audio_format: str = 'webm'):
        """处理接收到的音频数据"""
        if not self.is_running:
            return

        try:
            await self.log_event('mic_capture', '接收到音频数据', {
                'data_length': len(audio_data),
                'format': audio_format,
                'loop_step': self.loop_step
            })

            # VAD检测
            await self.send_callback('status', '正在进行语音活动检测...')
            vad_result = await self.vad_service.detect_speech(audio_data)
            await self.send_callback('vad_result', vad_result)

            if not vad_result.get('has_speech'):
                await self.send_callback('status', '未检测到语音')
                return

            # ASR识别
            await self.send_callback('status', '正在识别语音...')

            # 转换音频格式
            audio_bytes = base64.b64decode(audio_data)
            wav_audio_b64 = AudioConverter.pcm_to_wav_base64(audio_bytes)

            asr_result = await self.asr_service.recognize_speech(wav_audio_b64, audio_format="wav")
            await self.send_callback('transcript_final', asr_result, {
                'confidence': vad_result.get('confidence', 0.8),
                'loop_step': self.loop_step
            })

            if not asr_result.strip():
                await self.send_callback('status', '语音识别结果为空')
                return

            if asr_result.strip() == '<noise>':
                await self.send_callback('status', '语音识别结果为<noise>')
                return

            # 更新设备状态
            await self.send_callback('status', '查询设备状态...')
            await self.update_device_status()

            # 调用判断App分析结果
            judge_result = await self.call_judge_app(
                asr_result,
                self.current_device_status,
                self.previous_device_status
            )
            await self.log_event('app_call', json.dumps(judge_result), {'app_id': self.JUDGE_APP_ID})

            # 生成下一个查询
            next_query = await self.generate_next_query(judge_result, asr_result)

            if next_query and next_query.strip():
                self.current_query = next_query
                await self.send_callback('log', f'生成新查询: {self.current_query}')
                await self.send_callback('query_generated', {
                    'next_query': next_query,
                    'should_continue': True
                })
                await asyncio.sleep(1.0)
                await self.execute_full_loop()
            else:
                await self.send_callback('status', '对话完成，等待新的音频输入...')
                await self.send_callback('ai_response', '好的，我已经了解了当前情况。')

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
        """调用判断App分析ASR结果和设备状态变化"""
        try:
            # 检查是否使用 mock 模式
            if settings.dev_mock_external_services:
                return await self._get_mock_judge_result(asr_text)

            # TODO: 实现通过 HTTP 调用 Django Backend 的 App 执行接口
            # 目前使用 mock 模式
            logger.warning("Judge app call not fully implemented, using mock mode")
            return await self._get_mock_judge_result(asr_text)

        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return await self._get_mock_judge_result(asr_text)

    async def call_query_generator_app(
        self,
        test_scenario: str,
        conversation_history: list
    ) -> Dict[str, Any]:
        """调用DeviceControlGenerator APP生成下一轮测试query"""
        try:
            if settings.dev_mock_external_services:
                return await self._get_mock_query_result(test_scenario)

            # TODO: 实现通过 HTTP 调用 Django Backend 的 App 执行接口
            logger.warning("Query generator app call not fully implemented, using mock mode")
            return await self._get_mock_query_result(test_scenario)

        except Exception as e:
            logger.error(f"Query generator app call failed: {e}")
            return await self._get_mock_query_result(test_scenario)

    async def generate_next_query(self, judge_result: Dict[str, Any], asr_text: str) -> str:
        """根据判断结果生成下一个查询"""
        try:
            if not judge_result.get('should_continue', True):
                return ""

            suggested_action = judge_result.get('suggested_action', '')
            if suggested_action == 'end_conversation':
                return ""

            conversation_history = [
                {"role": "user", "content": self.current_query},
                {"role": "assistant", "content": asr_text}
            ]

            test_scenario = "测试厨电设备的语音控制功能"
            query_result = await self.call_query_generator_app(test_scenario, conversation_history)

            await self.log_event('query_generated', json.dumps(query_result, ensure_ascii=False), {
                'app_id': self.QUERY_GENERATOR_APP_ID,
                'loop_step': self.loop_step
            })

            await self.send_callback('query_generated', query_result)

            if not query_result.get('should_continue', True):
                return ""

            next_query = query_result.get('next_query', '')
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
        await self.send_callback('status', '智能体已停止')

        self.previous_device_status = {}
        self.current_device_status = {}
        self.loop_step = 0

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