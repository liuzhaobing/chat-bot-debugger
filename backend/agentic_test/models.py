import uuid
from django.db import models
from chat.models import App


class AgenticTestSession(models.Model):
    """Agentic Test 会话模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, default="新测试会话")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'agentic_test_session'
        ordering = ['-updated_at']


class AgenticTestLog(models.Model):
    """Agentic Test 日志模型"""
    LOG_TYPES = [
        ('user_query', '用户查询'),
        ('tts_generated', 'TTS生成'),
        ('speaker_play', '扬声器播放'),
        ('mic_capture', '麦克风采集'),
        ('vad_result', 'VAD结果'),
        ('asr_result', 'ASR识别'),
        ('iot_query', 'IOT查询'),
        ('app_call', 'App调用'),
        ('system_error', '系统错误'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AgenticTestSession, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'agentic_test_log'
        ordering = ['-timestamp']


class DeviceStatus(models.Model):
    """设备状态模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=100, unique=True)
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50)  # 油烟机、空调等
    status = models.JSONField(default=dict)  # 设备状态数据
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_status'


class DeviceProtocol(models.Model):
    """设备控制协议模型"""
    id = models.CharField(max_length=100, primary_key=True, help_text="设备标准名")
    protocol = models.JSONField(help_text="设备协议详情")
    category = models.CharField(max_length=100, help_text="设备品类")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_protocol'
        ordering = ['category', 'id']