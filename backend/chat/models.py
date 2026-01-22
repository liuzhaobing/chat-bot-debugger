import json
import re
import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Provider(models.Model):
    """
    LLM 提供商模型
    存储 API 提供商的基本信息和认证凭据
    """
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(default="https://api.openai.com/v1")
    api_key = models.CharField(max_length=255, blank=True, help_text="API Key for the provider")
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class LLMModel(models.Model):
    """
    LLM 模型配置
    关联到具体的提供商
    """
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100, help_text="Model ID like gpt-4 or claude-3-opus")
    display_name = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Conversation(models.Model):
    """
    对话会话模型
    用于组织和管理消息历史
    """
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    title = models.CharField(max_length=255, blank=True, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Message(models.Model):
    """
    消息模型 - 支持多模态内容和深度思考
    content 字段可以存储纯文本或 JSON 格式的多模态数据
    reasoning_content 存储深度思考过程
    token_usage 存储 token 使用统计
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # content 兼容旧文本，推荐存储为JSON字符串，结构为{"content": [...], "raw_text": "..."}
    content = models.TextField(help_text="消息内容，推荐为多模态JSON数组，兼容纯文本")
    # 深度思考相关字段
    reasoning_content = models.TextField(
        blank=True,
        null=True,
        help_text='深度思考内容 (reasoning_content)，从 delta.reasoning_content 获取'
    )
    token_usage = models.JSONField(
        blank=True,
        null=True,
        help_text='Token 使用统计 {prompt_tokens, completion_tokens, total_tokens}'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        try:
            obj = json.loads(self.content)
            if isinstance(obj, dict) and 'content' in obj:
                # 多模态格式
                return f"{self.role}: {str(obj['content'])[:50]}"
        except Exception:
            pass
        return f"{self.role}: {self.content[:50]}"


class AppCategory(models.Model):
    """
    应用分类模型
    用于组织应用广场的应用
    """
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AppType(models.Model):
    """
    应用类型模型
    定义应用的类型：Agent 1.0, Agent 2.0, Workflow 等
    用于区分不同的应用架构和配置方式
    """
    name = models.CharField(max_length=50, help_text="显示名称，如 'Agent 1.0'")
    code = models.CharField(max_length=50, unique=True, help_text="代码标识，如 'agent_1_0'")
    description = models.TextField(blank=True, help_text="类型描述")
    is_active = models.BooleanField(default=True, help_text="是否启用")
    sort_order = models.IntegerField(default=0, help_text="排序权重，数字越小越靠前")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = "应用类型"
        verbose_name_plural = "应用类型"

    def __str__(self):
        return self.name


def validate_camel_case_name(value):
    """
    验证应用名称是否符合驼峰命名规范
    规则：
    1. 只允许英文字母（大小写）
    2. 必须以大写字母开头
    3. 不允许空格、标点符号等特殊字符
    """
    if not value:
        raise ValidationError("应用名称不能为空")
    
    # 驼峰命名正则：以大写字母开头，后续可以是大小写字母
    pattern = r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+$'
    if not re.fullmatch(pattern, value):
        raise ValidationError(
            "应用名称必须符合驼峰命名规范（如 GetWeather），"
            "只允许英文字母，必须以大写字母开头，不允许空格和标点符号"
        )


def validate_function_schema(value):
    """
    验证 Function Calling Schema 格式
    确保符合 OpenAI Function Calling 规范
    """
    if not value:
        return
    
    if not isinstance(value, dict):
        raise ValidationError("function_schema 必须是 JSON 对象")
    
    # 验证必需字段
    if 'type' not in value or value['type'] != 'function':
        raise ValidationError("function_schema 必须包含 type='function'")
    
    if 'function' not in value:
        raise ValidationError("function_schema 必须包含 function 字段")
    
    function = value['function']
    required_fields = ['name', 'description', 'parameters']
    for field in required_fields:
        if field not in function:
            raise ValidationError(f"function 必须包含 {field} 字段")
    
    # 验证 parameters 结构
    params = function['parameters']
    if not isinstance(params, dict) or params.get('type') != 'object':
        raise ValidationError("parameters 必须是 type='object' 的 JSON Schema")


class App(models.Model):
    """
    应用模型
    支持多种应用类型：Agent 1.0, Agent 2.0, Workflow 等
    可作为 Function Calling 工具或 MCP 工具使用
    """
    # 基本信息
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    name = models.CharField(
        max_length=100, 
        validators=[validate_camel_case_name],
        help_text="应用名称，必须为驼峰命名，如 GetWeather"
    )
    description = models.TextField(help_text="应用描述")
    icon_url = models.URLField(blank=True, null=True, help_text="应用图标URL")
    
    # 分类和类型
    category = models.ForeignKey(
        AppCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='apps',
        help_text="应用所属分类"
    )
    app_type = models.ForeignKey(
        AppType,
        on_delete=models.PROTECT,
        related_name='apps',
        help_text="应用类型：Agent 1.0, Agent 2.0, Workflow 等"
    )
    
    # Agent 1.0 配置字段
    EXECUTION_MODE_CHOICES = (
        ('chat', 'Chat Mode (对话聊天式)'),
        ('task', 'Task Mode (任务执行式)'),
    )
    execution_mode = models.CharField(
        max_length=10,
        choices=EXECUTION_MODE_CHOICES,
        default='chat',
        help_text="执行模式：chat=对话聊天式(system_prompt作为system消息)，task=任务执行式(prompt作为user消息)"
    )
    system_prompt = models.TextField(
        default="", 
        blank=True, 
        help_text="应用的提示词（chat模式下为系统提示词，task模式下为任务模板）"
    )
    
    # Function Calling Parameters (替代原来的 variables)
    parameters = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Function Calling 参数定义，格式符合 OpenAI parameters schema"
    )
    
    # 模型和供应商配置
    provider_id = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="使用的供应商ID（UUID格式）"
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="使用的模型名称，如 'gpt-4'"
    )
    configuration = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="模型参数配置 (temperature, max_tokens等)"
    )
    
    # 元数据
    is_featured = models.BooleanField(default=False, help_text="是否为精选应用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "应用"
        verbose_name_plural = "应用"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.app_type.name})"
    
    def get_function_schema(self):
        """
        生成 Function Calling Schema
        基于应用的 parameters 配置
        """
        # 使用应用名称作为函数名（已经是驼峰格式）
        function_name = self.name
        
        # 如果没有自定义 parameters，使用默认结构
        if not self.parameters or not self.parameters.get('properties'):
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
        else:
            parameters = self.parameters
        
        # 生成完整的 Function Calling Schema
        schema = {
            "type": "function",
            "function": {
                "name": function_name,
                "description": self.description or f"调用 {self.name} 应用",
                "parameters": parameters
            }
        }
        
        return schema


class AppScenario(models.Model):
    """
    应用场景模型
    用于存储应用的测试场景（预设参数集合）
    """
    id = models.CharField(max_length=32, primary_key=True, editable=False)
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField(max_length=100, help_text="场景名称")
    description = models.TextField(blank=True, help_text="场景描述")
    parameters = models.JSONField(default=dict, help_text="场景参数集合")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "应用场景"
        verbose_name_plural = "应用场景"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.app.name})"
