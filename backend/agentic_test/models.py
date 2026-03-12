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


class TestTask(models.Model):
    """场景测试任务模型"""
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="任务名称")
    prd_content = models.TextField(blank=True, null=True, help_text="产品PRD或需求描述")
    
    # TTS配置
    tts_voice = models.ForeignKey(
        'chat.TTSVoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_tasks',
        help_text="TTS音色配置"
    )
    
    # IOT协议配置
    iot_protocol = models.ForeignKey(
        DeviceProtocol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_tasks',
        help_text="IOT设备协议"
    )
    
    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="任务状态"
    )
    
    # 测试报告
    report_url = models.URLField(blank=True, null=True, help_text="测试报告下载链接")
    report_data = models.JSONField(default=dict, blank=True, help_text="测试报告数据")
    
    # 执行结果
    result_summary = models.TextField(blank=True, null=True, help_text="执行结果摘要")
    error_message = models.TextField(blank=True, null=True, help_text="错误信息")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True, help_text="开始执行时间")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="完成时间")
    
    class Meta:
        db_table = 'test_task'
        ordering = ['-created_at']
        verbose_name = '测试任务'
        verbose_name_plural = '测试任务'