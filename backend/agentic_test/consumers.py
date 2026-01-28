import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import AgenticTestSession, AgenticTestLog
from .agent_loop import AgenticTestAgent

logger = logging.getLogger(__name__)


class AgenticTestConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.agent = None
        self.is_running = False

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'agentic_test_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Initialize agent
        self.agent = AgenticTestAgent(self.session_id, self.send_message)
        
        logger.info(f"WebSocket connected for session {self.session_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Stop agent if running
        if self.agent and self.is_running:
            await self.agent.stop()
        
        logger.info(f"WebSocket disconnected for session {self.session_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_test':
                await self.start_test(data.get('query', ''))
            elif message_type == 'stop_test':
                await self.stop_test()
            elif message_type == 'audio_data':
                await self.handle_audio_data(
                    data.get('audio'), 
                    data.get('format', 'webm')
                )
            elif message_type == 'intervention':
                await self.handle_intervention(data.get('message', ''))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def start_test(self, initial_query):
        """开始测试"""
        if self.is_running:
            await self.send_message('error', '测试已在运行中')
            return
            
        self.is_running = True
        await self.send_message('status', '测试开始')
        
        try:
            await self.agent.start_loop(initial_query)
        except Exception as e:
            logger.error(f"Error starting test: {e}")
            await self.send_message('error', f'启动测试失败: {str(e)}')
            self.is_running = False

    async def stop_test(self):
        """停止测试"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.agent:
            await self.agent.stop()
        await self.send_message('status', '测试已停止')

    async def handle_audio_data(self, audio_data, audio_format='webm'):
        """处理音频数据"""
        if self.agent and self.is_running:
            await self.agent.process_audio(audio_data, audio_format)

    async def handle_intervention(self, message):
        """处理人工干预"""
        if self.agent and self.is_running:
            await self.agent.handle_intervention(message)

    async def send_message(self, msg_type, content, metadata=None):
        """发送消息到前端"""
        message = {
            'type': msg_type,
            'content': content,
            'timestamp': asyncio.get_event_loop().time()
        }
        if metadata:
            message['metadata'] = metadata
            
        await self.send(text_data=json.dumps(message))

    # Group message handlers
    async def test_message(self, event):
        await self.send(text_data=json.dumps(event['message']))