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
            
            logger.debug(f"VAD+ASR test received message type: {message_type}")
            
            if message_type == 'audio_data':
                await self.handle_audio_data(
                    data.get('audio'),
                    data.get('format', 'webm'),
                    data.get('is_complete', False),
                    data.get('app_id', self.app_id)
                )
            elif message_type == 'start_test':
                await self.start_test()
            elif message_type == 'stop_test':
                await self.stop_test()
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
        
        await self.send_message('system_status', 'VAD+ASR测试已启动', {
            'app_id': self.app_id,
            'testing': True
        })
        
        logger.info(f"Started VAD+ASR test with app_id: {self.app_id}")
    
    async def stop_test(self):
        """停止VAD+ASR测试"""
        if not self.is_testing:
            await self.send_message('warning', '测试未在运行')
            return
            
        self.is_testing = False
        self.audio_buffer = []
        
        await self.send_message('system_status', 'VAD+ASR测试已停止', {
            'app_id': self.app_id,
            'testing': False
        })
        
        logger.info(f"Stopped VAD+ASR test with app_id: {self.app_id}")
    
    async def handle_audio_data(self, audio_data, audio_format='webm', is_complete=False, app_id=None):
        """处理音频数据进行VAD+ASR测试"""

        if not audio_data:
            await self.send_message('error', '音频数据为空')
            return
        
        try:
            # 解码base64音频数据
            audio_bytes = base64.b64decode(audio_data)
            
            # 添加到音频缓冲区
            self.audio_buffer.append(audio_bytes)
            
            # 发送VAD状态
            await self.send_message('vad_status', 'processing', {
                'buffer_size': len(self.audio_buffer),
                'audio_size': len(audio_bytes),
                'is_complete': is_complete
            })
            
            # 如果是完整的音频片段或缓冲区足够大，进行ASR处理
            if is_complete or len(self.audio_buffer) >= 5:  # 每5个音频块处理一次
                await self.process_audio_buffer(app_id or self.app_id)
                
        except Exception as e:
            logger.error(f"Error handling audio data in VAD+ASR test: {e}")
            await self.send_message('error', f'音频处理失败: {str(e)}')
    
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
                        'confidence': result.get('confidence', 0.0),
                        'app_id': app_id
                    })
                else:
                    await self.send_message('transcript_final', result.get('text', ''), {
                        'confidence': result.get('confidence', 0.0),
                        'app_id': app_id
                    })
                    
                # 清空缓冲区（仅在最终结果时）
                if not result.get('is_partial'):
                    self.audio_buffer = []
            else:
                await self.send_message('vad_status', 'no_speech', {
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