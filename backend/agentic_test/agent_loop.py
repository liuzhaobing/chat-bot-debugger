import asyncio
import json
import logging
import base64
from typing import Optional, Callable
from channels.db import database_sync_to_async
from .models import AgenticTestSession, AgenticTestLog
from .services import TTSService, ASRService, VADService, IOTService

logger = logging.getLogger(__name__)


class AgenticTestAgent:
    """Agentic Test 智能体主循环"""
    
    def __init__(self, session_id: str, send_callback: Callable):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False
        self.current_query = ""
        
        # 初始化服务
        self.tts_service = TTSService()
        self.asr_service = ASRService()
        self.vad_service = VADService()
        self.iot_service = IOTService()
        
    async def start_loop(self, initial_query: str):
        """启动智能体循环"""
        self.is_running = True
        self.current_query = initial_query
        
        await self.log_event('user_query', initial_query)
        await self.send_callback('log', f'开始处理查询: {initial_query}')
        
        while self.is_running:
            try:
                await self.execute_loop_step()
                await asyncio.sleep(0.1)  # 防止过度占用CPU
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await self.log_event('system_error', str(e))
                await self.send_callback('error', f'循环执行错误: {str(e)}')
                break
    
    async def execute_loop_step(self):
        """执行一个循环步骤"""
        if not self.current_query:
            return
            
        # Step 1: 生成TTS
        await self.send_callback('status', '正在生成语音...')
        tts_result = await self.tts_service.generate_speech(self.current_query)
        await self.log_event('tts_generated', self.current_query, {'audio_length': len(tts_result)})
        
        # Step 2: 播放音频
        await self.send_callback('audio_play', tts_result, {'type': 'tts'})
        await self.log_event('speaker_play', '播放TTS音频')
        
        # Step 3: 等待智能音响回应 (模拟等待)
        await self.send_callback('status', '等待智能音响回应...')
        await asyncio.sleep(2)  # 模拟等待时间
        
        # Step 4: 麦克风采集 (等待前端发送音频数据)
        await self.send_callback('status', '等待音频输入...')
        # 这里会通过 process_audio 方法接收音频数据
        
    async def process_audio(self, audio_data: str, audio_format: str = 'webm'):
        """处理接收到的音频数据"""
        if not self.is_running:
            return
            
        await self.log_event('mic_capture', '接收到音频数据', {
            'data_length': len(audio_data),
            'format': audio_format
        })
        
        # Step 5: VAD断句
        vad_result = await self.vad_service.detect_speech(audio_data)
        await self.log_event('vad_result', json.dumps(vad_result))
        
        if vad_result.get('has_speech'):
            # Step 6: ASR识别
            await self.send_callback('status', '正在识别语音...')
            asr_result = await self.asr_service.recognize_speech(
                audio_data, 
                audio_format=audio_format
            )
            await self.log_event('asr_result', asr_result)
            
            # Step 7: 查询IOT设备状态
            await self.send_callback('status', '查询设备状态...')
            device_status = await self.iot_service.get_device_status()
            await self.log_event('iot_query', json.dumps(device_status))
            
            # Step 8: 调用App判断 (预留接口)
            await self.send_callback('status', '分析结果...')
            app_result = await self.call_app_988988(asr_result, device_status)
            await self.log_event('app_call', json.dumps(app_result))
            
            # Step 9: 生成下一个查询
            self.current_query = app_result.get('next_query', '')
            if self.current_query:
                await self.send_callback('log', f'生成新查询: {self.current_query}')
            else:
                await self.send_callback('status', '测试完成')
                self.is_running = False
    
    async def call_app_988988(self, asr_text: str, device_status: dict) -> dict:
        """调用app-id=988988进行判断 (预留接口)"""
        # TODO: 实现实际的App调用逻辑
        return {
            'analysis': f'分析ASR结果: {asr_text}',
            'device_changes': '检测到设备状态变化',
            'next_query': '请检查油烟机是否正常工作',
            'confidence': 0.85
        }
    
    async def handle_intervention(self, message: str):
        """处理人工干预"""
        await self.log_event('user_query', f'人工干预: {message}')
        self.current_query = message
        await self.send_callback('log', f'接收到干预指令: {message}')
    
    async def stop(self):
        """停止智能体"""
        self.is_running = False
        await self.send_callback('status', '智能体已停止')
    
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
            session = AgenticTestSession.objects.get(id=self.session_id)
            AgenticTestLog.objects.create(
                session=session,
                log_type=log_type,
                content=content,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to log event: {e}")