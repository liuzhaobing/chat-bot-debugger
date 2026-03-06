import asyncio
import json
import logging
import base64
from typing import Optional, Callable, Dict, Any
from channels.db import database_sync_to_async
from .models import AgenticTestSession, AgenticTestLog
from .services import TTSService, ASRService, VADService, IOTService, AudioProcessingService
from chat.views import AppViewSet
from chat.models import App

logger = logging.getLogger(__name__)


class AgenticTestAgent:
    """Agentic Test 智能体主循环"""
    
    def __init__(self, session_id: str, send_callback: Callable, iot_config: Dict[str, str] = None):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self.current_query = ""
        self.loop_step = 0
        self.max_loop_steps = 10  # 防止无限循环
        
        # IOT配置 - 在初始化服务之前设置
        self.iot_config = iot_config or {
            'token': '',
            'familyId': '',
            'env': 'test'
        }
        
        # 初始化服务 - IOTService现在可以使用配置
        self.tts_service = TTSService()
        self.asr_service = ASRService()
        self.vad_service = VADService()
        self.iot_service = IOTService(
            token=self.iot_config.get('token', ''),
            family_id=self.iot_config.get('familyId', ''),
            env=self.iot_config.get('env', 'test')
        )
        self.audio_service = AudioProcessingService()
        
        # App IDs
        self.judge_app_id = "988988"  # 判断App ID
        self.generate_query_app_id = "c7a27bd4e3cf49008ae99fc69817f155"  # 生成查询App ID (DeviceControlQueryGenerator)
        
        # 设备状态缓存
        self.previous_device_status = {}
        self.current_device_status = {}
        
        logger.info(f"AgenticTestAgent initialized for session {session_id} with IOT config: env={self.iot_config.get('env')}, has_token={bool(self.iot_config.get('token'))}, has_family_id={bool(self.iot_config.get('familyId'))}")
        
    async def start_loop(self, initial_query: str, iot_config: Dict[str, str] = None):
        """启动智能体循环"""
        self.is_running = True
        self.current_query = initial_query
        self.loop_step = 0
        
        # 更新IOT配置
        if iot_config:
            self.iot_config.update(iot_config)
        
        await self.log_event('user_query', initial_query)
        await self.send_callback('log', f'开始处理查询: {initial_query}')
        await self.send_callback('status', '智能体循环已启动')
        
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
                    
                # 短暂延迟，避免过快循环
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await self.log_event('system_error', str(e))
                await self.send_callback('error', f'循环执行错误: {str(e)}')
                break
    
    async def initialize_device_status(self):
        """初始化设备状态"""
        try:
            if not self.iot_config.get('token') or not self.iot_config.get('family_id'):
                await self.send_callback('warning', 'IOT配置不完整，使用模拟数据')
                return
            
            # 获取家庭设备列表
            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['family_id'], 
                self.iot_config['token']
            )
            
            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])
                await self.send_callback('log', f'发现 {len(devices)} 个设备')
                
                # 获取每个设备的状态
                for device in devices[:3]:  # 限制前3个设备，避免过多请求
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
    
    async def execute_full_loop(self):
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
            await self.log_event('speaker_play', '播放TTS音频')
            
            # Step 3: 等待智能音响回应（模拟等待时间）
            await self.send_callback('status', '等待智能音响回应...')
            await asyncio.sleep(3.0)  # 给智能音响响应时间
            
            # Step 4: 等待麦克风采集音频数据
            await self.send_callback('status', '等待音频输入...')
            # 这里会通过 process_audio 方法接收音频数据
            
            return False  # 等待音频输入，暂停循环
            
        except Exception as e:
            logger.error(f"Error in execute_full_loop: {e}")
            await self.send_callback('error', f'循环执行失败: {str(e)}')
            return False
        
    async def process_audio(self, audio_data: str, audio_format: str = 'webm'):
        """处理接收到的音频数据 - 完整的Agent循环"""
        if not self.is_running:
            return
            
        try:
            await self.log_event('mic_capture', '接收到音频数据', {
                'data_length': len(audio_data),
                'format': audio_format,
                'loop_step': self.loop_step
            })
            
            # Step 5: VAD断句检测
            await self.send_callback('status', '正在进行语音活动检测...')
            vad_result = await self.vad_service.detect_speech(audio_data)
            await self.log_event('vad_result', json.dumps(vad_result))
            
            # 发送VAD结果到前端
            await self.send_callback('vad_result', vad_result)
            
            if not vad_result.get('has_speech'):
                await self.send_callback('status', '未检测到语音，等待新的音频输入...')
                return
            
            # Step 6: ASR语音识别
            await self.send_callback('status', '正在识别语音...')
            asr_result = await self.asr_service.recognize_speech(
                audio_data, 
                audio_format=audio_format
            )
            await self.log_event('asr_result', asr_result)
            
            # 发送ASR结果到前端
            await self.send_callback('transcript_final', asr_result, {
                'confidence': vad_result.get('confidence', 0.8),
                'loop_step': self.loop_step
            })
            
            if not asr_result.strip():
                await self.send_callback('status', '语音识别结果为空，等待新的音频输入...')
                return
            
            # Step 7: 查询IOT设备状态
            await self.send_callback('status', '查询设备状态...')
            await self.update_device_status()
            
            # Step 8: 调用判断App分析结果
            await self.send_callback('status', '分析语音内容和设备状态...')
            judge_result = await self.call_judge_app(asr_result, self.current_device_status, self.previous_device_status)
            await self.log_event('app_call', json.dumps(judge_result), {'app_id': self.judge_app_id})
            
            # Step 9: 根据判断结果生成下一个查询
            next_query = await self.generate_next_query(judge_result, asr_result)
            
            if next_query and next_query.strip():
                self.current_query = next_query
                await self.send_callback('log', f'生成新查询: {self.current_query}')
                
                # 继续循环
                await asyncio.sleep(1.0)  # 短暂延迟
                await self.execute_full_loop()
            else:
                await self.send_callback('status', '对话完成，等待新的音频输入...')
                await self.send_callback('ai_response', '好的，我已经了解了当前情况。还有什么需要帮助的吗？')
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await self.send_callback('error', f'音频处理失败: {str(e)}')
            await self.log_event('system_error', str(e))
    
    async def update_device_status(self):
        """更新设备状态"""
        try:
            if not self.iot_config.get('token') or not self.iot_config.get('family_id'):
                # 使用模拟数据
                self.current_device_status = await self.iot_service._get_mock_device_status('mock_device')
                await self.log_event('iot_query', '使用模拟设备状态数据')
                return
            
            # 更新之前的状态
            self.previous_device_status = self.current_device_status.copy()
            self.current_device_status = {}
            
            # 获取家庭设备列表
            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['family_id'], 
                self.iot_config['token']
            )
            
            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])
                
                # 获取每个设备的当前状态
                for device in devices[:3]:  # 限制前3个设备
                    device_guid = device.get('deviceGuid')
                    if device_guid:
                        status_result = await self.iot_service.get_device_status(
                            device_guid, 
                            self.iot_config['token']
                        )
                        if status_result.get('success', False) or status_result.get('rc') == 0:
                            self.current_device_status[device_guid] = status_result.get('data', [])
                
                await self.log_event('iot_query', f'更新了 {len(self.current_device_status)} 个设备状态')
                
                # 发送设备状态到前端
                await self.send_callback('device_status_update', {
                    'current': self.current_device_status,
                    'previous': self.previous_device_status,
                    'changes': self.detect_device_changes()
                })
            
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            await self.send_callback('warning', f'设备状态更新失败: {str(e)}')
    
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
                changes[device_guid] = {
                    'has_change': False
                }
        
        return changes
    
    async def call_judge_app(self, asr_text: str, current_status: Dict, previous_status: Dict) -> Dict[str, Any]:
        """调用判断App分析ASR结果和设备状态变化"""
        try:
            # 获取判断App实例
            app = await database_sync_to_async(App.objects.get)(id=self.judge_app_id)
            app_viewset = AppViewSet()
            
            # 准备参数
            parameters = {
                "asr_text": asr_text,
                "current_device_status": json.dumps(current_status),
                "previous_device_status": json.dumps(previous_status),
                "device_changes": json.dumps(self.detect_device_changes()),
                "loop_step": self.loop_step
            }
            
            # 调用App
            result = await database_sync_to_async(app_viewset._execute_app)(
                app=app, 
                parameters=parameters
            )
            
            if result["status"] == "success":
                try:
                    # 尝试解析JSON结果
                    judge_result = json.loads(result["content"])
                    return judge_result
                except json.JSONDecodeError:
                    # 如果不是JSON，包装成标准格式
                    return {
                        'analysis': result["content"],
                        'confidence': 0.8,
                        'should_continue': True,
                        'suggested_action': 'continue_conversation'
                    }
            else:
                logger.error(f'Judge app call failed: {result.get("error")}')
                return await self._get_mock_judge_result(asr_text)
                
        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return await self._get_mock_judge_result(asr_text)
    
    async def call_query_generator_app(self, test_scenario: str, conversation_history: list) -> Dict[str, Any]:
        """调用DeviceControlGenerator APP生成下一轮测试query"""
        try:
            # 获取QueryGenerator App实例
            app = await database_sync_to_async(App.objects.get)(id=self.generate_query_app_id)
            app_viewset = AppViewSet()
            
            # 准备家庭设备列表
            family_devices_list = []
            if self.iot_config.get('token') and self.iot_config.get('familyId'):
                devices_result = await self.iot_service.get_family_devices(
                    self.iot_config['familyId'], 
                    self.iot_config['token']
                )
                if devices_result.get('success', False) or devices_result.get('rc') == 0:
                    family_devices_list = devices_result.get('data', [])
            
            # 准备参数
            from datetime import datetime
            parameters = {
                "test_scenario": test_scenario,
                "family_devices": json.dumps(family_devices_list, ensure_ascii=False),
                "conversation_history": conversation_history,
                "current_device_status": json.dumps(self.current_device_status, ensure_ascii=False),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 调用App
            result = await database_sync_to_async(app_viewset._execute_app)(
                app=app, 
                parameters=parameters
            )
            
            if result["status"] == "success":
                try:
                    # 尝试解析JSON结果
                    query_result = json.loads(result["content"])
                    return query_result
                except json.JSONDecodeError:
                    logger.error(f'Query generator returned non-JSON: {result["content"]}')
                    return await self._get_mock_query_result(test_scenario)
            else:
                logger.error(f'Query generator app call failed: {result.get("error")}')
                return await self._get_mock_query_result(test_scenario)
                
        except Exception as e:
            logger.error(f"Query generator app call failed: {e}")
            return await self._get_mock_query_result(test_scenario)
    
    async def generate_next_query(self, judge_result: Dict[str, Any], asr_text: str) -> str:
        """根据判断结果生成下一个查询"""
        try:
            # 检查是否应该继续对话
            if not judge_result.get('should_continue', True):
                return ""
            
            # 如果有建议的下一步动作
            suggested_action = judge_result.get('suggested_action', '')
            if suggested_action == 'end_conversation':
                return ""
            
            # 构建对话历史
            conversation_history = [
                {"role": "user", "content": self.current_query},
                {"role": "assistant", "content": asr_text}
            ]
            
            # 调用TestQueryGenerator APP生成下一轮query
            test_scenario = "测试厨电设备的语音控制功能，包括开关机、档位调节、灯光控制等基本操作"
            query_result = await self.call_query_generator_app(test_scenario, conversation_history)
            
            # 记录生成的query结果
            await self.log_event('query_generated', json.dumps(query_result, ensure_ascii=False), {
                'app_id': self.generate_query_app_id,
                'loop_step': self.loop_step
            })
            
            # 发送query生成结果到前端
            await self.send_callback('query_generated', query_result)
            
            # 检查是否应该继续
            if not query_result.get('should_continue', True):
                await self.send_callback('log', '测试场景已完成')
                return ""
            
            # 返回生成的query
            next_query = query_result.get('next_query', '')
            if next_query:
                await self.send_callback('log', f'生成测试意图: {query_result.get("test_intent", "N/A")}')
                await self.send_callback('log', f'目标设备: {query_result.get("target_device_name", "N/A")}')
                await self.send_callback('log', f'期望变化: {json.dumps(query_result.get("expected_device_changes", {}), ensure_ascii=False)}')
            
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
        await self.log_event('user_query', f'人工干预: {message}')
        self.current_query = message
        self.loop_step = 0  # 重置循环步骤
        await self.send_callback('log', f'接收到干预指令: {message}')
        
        # 重新开始循环
        if self.is_running:
            await self.execute_full_loop()
    
    async def stop(self):
        """停止智能体"""
        self.is_running = False
        await self.send_callback('status', '智能体已停止')
        await self.log_event('system_status', '智能体循环已停止')
    
    async def update_iot_config(self, config: Dict[str, str]):
        """更新IOT配置"""
        self.iot_config.update(config)
        
        # 更新IOTService的配置
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
    
    def _detect_audio_format(self, audio_data: str) -> str:
        """
        检测音频格式（简单的启发式方法）
        
        Args:
            audio_data: base64编码的音频数据
            
        Returns:
            检测到的音频格式
        """
        try:
            # 解码前几个字节来检测文件头
            audio_bytes = base64.b64decode(audio_data[:100])  # 只解码前面一部分
            
            # 检测常见的音频文件头
            if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:20]:
                return 'wav'
            elif audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/Matroska
                return 'webm'
            elif audio_bytes.startswith(b'OggS'):
                return 'ogg'
            elif audio_bytes.startswith(b'\xff\xfb') or audio_bytes.startswith(b'\xff\xf3') or audio_bytes.startswith(b'\xff\xf2'):
                return 'mp3'
            elif audio_bytes.startswith(b'ftyp'):
                return 'mp4'
            else:
                # 默认假设是 wav 格式
                logger.warning(f"Unknown audio format, assuming wav. First bytes: {audio_bytes[:10].hex()}")
                return 'wav'
                
        except Exception as e:
            logger.error(f"Error detecting audio format: {e}")
            return 'wav'  # 默认格式
    
    @database_sync_to_async
    def log_event(self, log_type: str, content: str, metadata: dict = None):
        """记录事件日志"""
        try:
            # 如果session_id不是有效的UUID，则跳过数据库记录
            if len(self.session_id) < 32:  # 简单检查UUID长度
                logger.debug(f"Skipping DB log for test session: {log_type} - {content}")
                return
                
            session = AgenticTestSession.objects.get(id=self.session_id)
            AgenticTestLog.objects.create(
                session=session,
                log_type=log_type,
                content=content,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.debug(f"Failed to log event (expected for test): {e}")