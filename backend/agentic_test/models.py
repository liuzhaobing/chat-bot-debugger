import uuid
from django.db import models
from chat.models import App


class DigitalEmployee(models.Model):
    """数字员工模型 - 关联TTS音色和3D角色"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="数字员工名称")

    # 关联TTS音色
    tts_voice = models.ForeignKey(
        'chat.TTSVoice',
        on_delete=models.PROTECT,
        related_name='digital_employees',
        help_text="关联的TTS音色"
    )

    # 3D角色配置
    AVATAR_CHOICES = [
        (0, '橙色半圆'),
        (1, '紫色方块'),
        (2, '黑色方块'),
        (3, '黄色圆角'),
    ]
    avatar_index = models.IntegerField(
        choices=AVATAR_CHOICES,
        default=0,
        help_text="3D角色索引 (0-3)"
    )

    # 元数据
    is_active = models.BooleanField(default=True, help_text="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'digital_employee'
        ordering = ['name']
        verbose_name = '数字员工'
        verbose_name_plural = '数字员工'

    def __str__(self):
        return self.name


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
        ('stopped', '已停止'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="任务名称")
    prd_content = models.TextField(blank=True, null=True, help_text="产品PRD或需求描述")

    # 数字员工配置（新版）
    employee = models.ForeignKey(
        DigitalEmployee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="执行任务的数字员工"
    )

    # TTS配置（保留用于数据迁移兼容，后续可移除）
    tts_voice = models.ForeignKey(
        'chat.TTSVoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_tasks',
        help_text="TTS音色配置（已弃用，请使用employee）"
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
    
    # WebSocket 会话ID
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text="WebSocket会话ID")

    # 任务实例ID（用于日志追踪和报告关联）
    job_instance_id = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="任务实例ID，用于日志追踪")

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