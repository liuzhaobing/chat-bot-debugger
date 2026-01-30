import json
import asyncio
import logging
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import AgenticTestSession, AgenticTestLog
from .agent_loop import AgenticTestAgent
from .services import process_audio_for_asr

logger = logging.getLogger(__name__)


class AgenticTestConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.agent = None
        self.is_running = False
        self.iot_config = {}

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'agentic_test_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send connection confirmation
        await self.send_message('connection_status', 'WebSocket连接已建立', {
            'session_id': self.session_id,
            'timestamp': asyncio.get_event_loop().time(),
            'waiting_for_iot_config': True
        })
        
        logger.info(f"WebSocket connected for session {self.session_id}")

    async def initialize_agent_with_config(self, iot_config):
        """使用IOT配置初始化智能体"""
        try:
            # Initialize agent with IOT config
            self.agent = AgenticTestAgent(self.session_id, self.send_message, iot_config)
            
            await self.send_message('status', 'Agent已初始化', {
                'iot_config_received': True,
                'config': {
                    'env': iot_config.get('env', 'test'),
                    'has_token': bool(iot_config.get('token')),
                    'has_family_id': bool(iot_config.get('familyId'))
                }
            })
            
            logger.info(f"Agent initialized with IOT config for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent with IOT config: {e}")
            await self.send_message('error', f'Agent初始化失败: {str(e)}')

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Stop agent if running
        if self.agent and self.is_running:
            await self.agent.stop()
        
        logger.info(f"WebSocket disconnected for session {self.session_id}, close_code: {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.debug(f"Received message type: {message_type}")
            
            if message_type == 'start_test':
                await self.start_test(
                    data.get('query', ''), 
                    data.get('iot_config', {})
                )
            elif message_type == 'stop_test':
                await self.stop_test()
            elif message_type == 'audio_data':
                await self.handle_audio_data(
                    data.get('audio'), 
                    data.get('format', 'webm'),
                    data.get('is_complete', False)
                )
            elif message_type == 'intervention':
                await self.handle_intervention(data.get('message', ''))
            elif message_type == 'update_iot_config':
                await self.update_iot_config(data.get('config', {}))
            elif message_type == 'ping':
                await self.send_message('pong', 'pong')
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_message('error', f'未知消息类型: {message_type}')
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_message('error', 'JSON格式错误')
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_message('error', f'消息处理错误: {str(e)}')

    async def start_test(self, initial_query, iot_config=None):
        """开始测试"""
        if self.is_running:
            await self.send_message('error', '测试已在运行中')
            return
            
        self.is_running = True
        
        # 更新IOT配置
        if iot_config:
            self.iot_config = iot_config
            await self.agent.update_iot_config(iot_config)
        
        await self.send_message('status', '测试开始', {
            'initial_query': initial_query,
            'iot_config': bool(iot_config)
        })
        
        try:
            await self.agent.start_loop(initial_query, iot_config)
        except Exception as e:
            logger.error(f"Error starting test: {e}")
            await self.send_message('error', f'启动测试失败: {str(e)}')
            self.is_running = False

    async def stop_test(self):
        """停止测试"""
        if not self.is_running:
            await self.send_message('warning', '测试未在运行')
            return
            
        self.is_running = False
        if self.agent:
            await self.agent.stop()
        await self.send_message('status', '测试已停止')

    async def handle_audio_data(self, audio_data, audio_format='webm', is_complete=False):
        """处理音频数据"""
        if not audio_data:
            await self.send_message('error', '音频数据为空')
            return
            
        if self.agent and self.is_running:
            try:
                await self.agent.process_audio(audio_data, audio_format)
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await self.send_message('error', f'音频处理失败: {str(e)}')
        else:
            await self.send_message('warning', '智能体未运行，忽略音频数据')

    async def handle_intervention(self, message):
        """处理人工干预"""
        if not message.strip():
            await self.send_message('error', '干预消息不能为空')
            return
            
        if self.agent and self.is_running:
            try:
                await self.agent.handle_intervention(message)
            except Exception as e:
                logger.error(f"Error handling intervention: {e}")
                await self.send_message('error', f'处理干预失败: {str(e)}')
        else:
            await self.send_message('warning', '智能体未运行，无法处理干预')
    
    async def update_iot_config(self, config):
        """更新IOT配置"""
        try:
            self.iot_config.update(config)
            
            # 如果agent还没有初始化，现在初始化它
            if not self.agent:
                await self.initialize_agent_with_config(config)
            else:
                # 如果agent已经存在，更新其IOT配置
                await self.agent.update_iot_config(config)
            
            await self.send_message('status', 'IOT配置已更新', {
                'config': {
                    'env': config.get('env', 'test'),
                    'has_token': bool(config.get('token')),
                    'has_family_id': bool(config.get('familyId'))
                }
            })
        except Exception as e:
            logger.error(f"Error updating IOT config: {e}")
            await self.send_message('error', f'更新IOT配置失败: {str(e)}')

    async def send_message(self, msg_type, content, metadata=None):
        """发送消息到前端"""
        message = {
            'type': msg_type,
            'content': content,
            'timestamp': asyncio.get_event_loop().time(),
            'session_id': self.session_id
        }
        if metadata:
            message['metadata'] = metadata
            
        try:
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    # Group message handlers
    async def test_message(self, event):
        """处理群组消息"""
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.error(f"Error sending group message: {e}")


class VadAsrTestConsumer(AsyncWebsocketConsumer):
    """VAD+ASR测试专用WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id = None
        self.is_testing = False
        self.audio_buffer = []
        self.vad_service = None  # 添加VAD服务实例
        
    async def connect(self):
        # 从查询参数获取app_id
        query_string = self.scope.get('query_string', b'').decode()
        query_params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        
        self.app_id = query_params.get('app_id', '4f95e97b0ec641fab9772b68a81bcf4a')
        
        self.room_group_name = f'vad_asr_test_{self.app_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send_message('connection_status', 'VAD+ASR测试连接已建立', {
            'app_id': self.app_id,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        logger.info(f"VAD+ASR test WebSocket connected with app_id: {self.app_id}")
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Stop testing if running
        if self.is_testing:
            self.is_testing = False
            
        logger.info(f"VAD+ASR test WebSocket disconnected, close_code: {close_code}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.info(f"VAD+ASR test received message type: {message_type}")
            logger.info(f"Full message data: {json.dumps(data, indent=2)}")
            
            if message_type == 'audio_data':
                # 支持两种消息格式：
                # 1. 新格式（类似dial电话客服）：data.data.audio_data
                # 2. 旧格式（兼容）：data.audio
                audio_data = None
                audio_format = 'webm'
                is_complete = False
                
                if 'data' in data and isinstance(data['data'], dict):
                    # 新格式 - 类似dial电话客服
                    audio_data = data['data'].get('audio_data')
                    audio_format = data['data'].get('format', 'pcm')
                    is_complete = False  # PCM格式是流式的，不需要is_complete
                    
                    logger.info(f"New format audio data: format={audio_format}, size={data['data'].get('size', 0)}")
                    logger.info(f"Audio data present: {bool(audio_data)}, length: {len(audio_data) if audio_data else 0}")
                else:
                    # 旧格式 - 兼容性
                    audio_data = data.get('audio')
                    audio_format = data.get('format', 'webm')
                    is_complete = data.get('is_complete', False)
                    
                    logger.info(f"Old format audio data: format={audio_format}, is_complete={is_complete}")
                    logger.info(f"Audio data present: {bool(audio_data)}, length: {len(audio_data) if audio_data else 0}")
                
                if not audio_data:
                    logger.warning(f"Empty audio data received. Message keys: {list(data.keys())}")
                    if 'data' in data:
                        logger.warning(f"Data sub-keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'not a dict'}")
                    await self.send_message('error', '音频数据为空')
                    return
                
                await self.handle_audio_data(
                    audio_data,
                    audio_format,
                    is_complete,
                    data.get('app_id', self.app_id)
                )
            elif message_type == 'start_test':
                await self.start_test()
            elif message_type == 'stop_test':
                await self.stop_test()
            elif message_type == 'set_vad_level':
                await self.set_vad_level(data.get('level', 2))
            elif message_type == 'ping':
                await self.send_message('pong', 'pong')
            else:
                logger.warning(f"Unknown VAD+ASR test message type: {message_type}")
                await self.send_message('error', f'未知消息类型: {message_type}')
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received in VAD+ASR test: {e}")
            await self.send_message('error', 'JSON格式错误')
        except Exception as e:
            logger.error(f"Error processing VAD+ASR test message: {e}")
            await self.send_message('error', f'消息处理错误: {str(e)}')
    
    async def start_test(self):
        """开始VAD+ASR测试"""
        if self.is_testing:
            await self.send_message('warning', '测试已在运行中')
            return
            
        self.is_testing = True
        self.audio_buffer = []
        
        # 初始化VAD服务
        from .services import VADService
        self.vad_service = VADService()
        
        await self.send_message('system_status', 'VAD+ASR测试已启动', {
            'app_id': self.app_id,
            'testing': True,
            'vad_level': self.vad_service.vad_level if self.vad_service else 2
        })
        
        logger.info(f"Started VAD+ASR test with app_id: {self.app_id}")
    
    async def stop_test(self):
        """停止VAD+ASR测试"""
        if not self.is_testing:
            await self.send_message('warning', '测试未在运行')
            return
            
        self.is_testing = False
        self.audio_buffer = []
        self.vad_service = None  # 清理VAD服务
        
        await self.send_message('system_status', 'VAD+ASR测试已停止', {
            'app_id': self.app_id,
            'testing': False
        })
        
        logger.info(f"Stopped VAD+ASR test with app_id: {self.app_id}")
    
    async def set_vad_level(self, level):
        """设置VAD敏感度级别"""
        try:
            level = int(level)
            if not (0 <= level <= 3):
                await self.send_message('error', f'VAD级别必须在0-3之间，收到: {level}')
                return
            
            if self.vad_service:
                success = self.vad_service.set_vad_level(level)
                if success:
                    await self.send_message('vad_config', f'VAD敏感度已设置为 {level}', {
                        'level': level,
                        'description': self._get_vad_level_description(level)
                    })
                else:
                    await self.send_message('error', f'设置VAD级别失败')
            else:
                await self.send_message('warning', 'VAD服务未初始化，请先启动测试')
                
        except ValueError:
            await self.send_message('error', f'无效的VAD级别: {level}')
    
    def _get_vad_level_description(self, level):
        """获取VAD级别描述"""
        descriptions = {
            0: "最不敏感 - 只检测非常明显的语音",
            1: "较不敏感 - 检测清晰的语音",
            2: "中等敏感 - 平衡检测（默认）",
            3: "最敏感 - 检测轻微的语音活动"
        }
        return descriptions.get(level, "未知级别")
    
    async def handle_audio_data(self, audio_data, audio_format='pcm', is_complete=False, app_id=None):
        """处理音频数据进行VAD+ASR测试"""
        
        logger.info(f"Handling audio data: format={audio_format}, is_complete={is_complete}, app_id={app_id}")
        logger.debug(f"Audio data length: {len(audio_data) if audio_data else 0}")

        if not audio_data:
            logger.warning("Empty audio data received")
            await self.send_message('error', '音频数据为空')
            return
        
        try:
            # 解码base64音频数据
            audio_bytes = base64.b64decode(audio_data)
            logger.debug(f"Decoded audio bytes length: {len(audio_bytes)}")
            
            # 添加到音频缓冲区
            self.audio_buffer.append(audio_bytes)
            
            # 发送VAD状态
            await self.send_message('vad_status', 'processing', {
                'status': 'processing',
                'buffer_size': len(self.audio_buffer),
                'audio_size': len(audio_bytes),
                'format': audio_format,
                'is_complete': is_complete
            })
            
            # 实时处理音频数据 - 模拟dial电话客服的处理方式
            if audio_format == 'pcm':
                # PCM格式的实时处理
                await self.process_pcm_audio_chunk(audio_bytes, app_id or self.app_id)
            else:
                # 传统的批量处理方式（兼容旧版本）
                if is_complete or len(self.audio_buffer) >= 5:
                    await self.process_audio_buffer(app_id or self.app_id)
                
        except Exception as e:
            logger.error(f"Error handling audio data in VAD+ASR test: {e}")
            await self.send_message('error', f'音频处理失败: {str(e)}')
    
    async def process_pcm_audio_chunk(self, audio_bytes, app_id):
        """处理单个PCM音频块 - 实时处理，优化缓冲策略"""
        try:
            # 大幅增加缓冲区大小，减少处理频率
            # 16kHz, 16bit, 1channel = 32000 bytes per second
            # 3秒 = 96000 bytes (更大的音频块，减少碎片)
            target_buffer_size = 96000   # 3秒的音频数据
            max_buffer_size = 192000     # 6秒最大缓冲区
            min_process_size = 64000     # 最小处理大小：2秒
            
            # 合并当前缓冲区的音频数据
            combined_audio = b''.join(self.audio_buffer)
            
            logger.debug(f"Audio buffer: {len(combined_audio)} bytes ({len(combined_audio)/32000:.1f}s), chunks: {len(self.audio_buffer)}")
            
            # 只有当缓冲区达到目标大小时才处理
            if len(combined_audio) >= target_buffer_size:
                logger.info(f"Processing large audio chunk: {len(combined_audio)} bytes ({len(combined_audio)/32000:.1f}s)")
                
                # 使用VAD+ASR处理（VAD会决定是否保存音频文件）
                from .services import process_audio_with_vad_asr
                
                result = await process_audio_with_vad_asr(combined_audio, app_id)
                
                # 发送VAD结果
                vad_result = result.get('vad', {})
                await self.send_message('vad_status', 'detected' if vad_result.get('has_speech') else 'no_speech', {
                    'has_speech': vad_result.get('has_speech', False),
                    'confidence': vad_result.get('confidence', 0.0),
                    'speech_start': vad_result.get('speech_start', 0),
                    'speech_end': vad_result.get('speech_end', 0),
                    'audio_duration_s': len(combined_audio) / 32000,
                    'speech_ratio': vad_result.get('speech_ratio', 0.0),
                    'speech_segments': vad_result.get('speech_segments', 0)
                })
                
                # 只有VAD检测到语音时才发送ASR结果
                asr_result = result.get('asr')
                if asr_result:
                    await self.send_message('transcript_final', asr_result.get('text', ''), {
                        'app_id': app_id,
                        'audio_duration_s': len(combined_audio) / 32000,
                        'vad_confidence': vad_result.get('confidence', 0.0),
                        'speech_ratio': vad_result.get('speech_ratio', 0.0)
                    })
                    logger.info(f"ASR result: '{asr_result.get('text', '')[:50]}...'")
                else:
                    logger.info(f"VAD detected no speech in {len(combined_audio)} bytes audio (speech_ratio: {vad_result.get('speech_ratio', 0.0):.2f})")
                
                # 清空缓冲区，避免重复处理
                self.audio_buffer = []
                
            elif len(combined_audio) > max_buffer_size:
                # 如果缓冲区过大，强制处理并保留部分数据
                logger.warning(f"Buffer too large ({len(combined_audio)} bytes), force processing and keeping recent data")
                
                # 处理当前数据（如果足够大）
                if len(combined_audio) >= min_process_size:
                    from .services import process_audio_with_vad_asr
                    result = await process_audio_with_vad_asr(combined_audio, app_id)
                    
                    vad_result = result.get('vad', {})
                    logger.info(f"Force processed audio: has_speech={vad_result.get('has_speech')}, speech_ratio={vad_result.get('speech_ratio', 0.0):.2f}")
                
                # 保留最后1.5秒的音频数据作为下次的开始
                keep_size = 48000  # 1.5秒
                self.audio_buffer = [combined_audio[-keep_size:]]
                
                await self.send_message('vad_status', 'buffer_reset', {
                    'status': 'buffer_reset',
                    'message': '音频缓冲区过大已重置',
                    'kept_size': keep_size,
                    'discarded_size': len(combined_audio) - keep_size,
                    'kept_duration_s': keep_size / 32000
                })
            
            # 降低统计信息发送频率（每50个chunk发送一次）
            if len(self.audio_buffer) % 50 == 0:
                await self.send_message('audio_stats', 'realtime', {
                    'buffer_size_bytes': len(combined_audio),
                    'buffer_duration_s': len(combined_audio) / 32000,
                    'chunks_received': len(self.audio_buffer),
                    'app_id': app_id,
                    'target_buffer_s': target_buffer_size / 32000,
                    'processing_threshold': f"{target_buffer_size / 32000:.1f}s"
                })
                        
        except Exception as e:
            logger.error(f"Error processing PCM audio chunk: {e}")
            await self.send_message('error', f'PCM音频处理失败: {str(e)}')
    
    async def process_audio_buffer(self, app_id):
        """处理音频缓冲区进行ASR"""
        if not self.audio_buffer:
            return
            
        try:
            # 合并音频数据
            combined_audio = b''.join(self.audio_buffer)
            
            # 调用ASR服务
            result = await process_audio_for_asr(combined_audio, app_id)
            
            if result:
                # 发送转录结果
                if result.get('is_partial'):
                    await self.send_message('transcript_partial', result.get('text', ''), {
                        'app_id': app_id
                    })
                else:
                    await self.send_message('transcript_final', result.get('text', ''), {
                        'app_id': app_id
                    })
                    
                # 清空缓冲区（仅在最终结果时）
                if not result.get('is_partial'):
                    self.audio_buffer = []
            else:
                await self.send_message('vad_status', 'no_speech', {
                    'status': 'no_speech',
                    'message': '未检测到语音内容'
                })
                
        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")
            await self.send_message('error', f'ASR处理失败: {str(e)}')
    
    async def send_message(self, msg_type, content, metadata=None):
        """发送消息到前端"""
        message = {
            'type': msg_type,
            'content': content,
            'timestamp': asyncio.get_event_loop().time(),
            'app_id': self.app_id
        }
        if metadata:
            message.update(metadata)
            
        try:
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending VAD+ASR test message: {e}")