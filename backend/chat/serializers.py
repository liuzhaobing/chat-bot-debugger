from rest_framework import serializers
import re
import json
from .models import Provider, LLMModel, Conversation, Message, App, AppCategory, AppType


class LLMModelSerializer(serializers.ModelSerializer):
    """LLM 模型序列化器"""
    class Meta:
        model = LLMModel
        fields = ['id', 'name', 'display_name']


class ProviderSerializer(serializers.ModelSerializer):
    """提供商序列化器"""
    models = LLMModelSerializer(many=True, read_only=True)
    
    class Meta:
        model = Provider
        fields = ['id', 'name', 'base_url', 'api_key', 'models']
        extra_kwargs = {'api_key': {'write_only': True}}


class MessageSerializer(serializers.ModelSerializer):
    """消息序列化器 - 支持深度思考和 token 统计"""
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'reasoning_content', 'token_usage', 'created_at']
    
    def get_content(self, obj):
        """
        自动解析content字段
        如果是JSON字符串（多模态），解析为数组
        如果是普通字符串，直接返回
        """
        content = obj.content
        if not content:
            return ''
        
        # 尝试解析JSON
        if isinstance(content, str) and content.strip().startswith('['):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
        
        return content


class ConversationSerializer(serializers.ModelSerializer):
    """对话序列化器"""
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at']


class AppCategorySerializer(serializers.ModelSerializer):
    """应用分类序列化器"""
    app_count = serializers.IntegerField(read_only=True, source='apps.count')
    
    class Meta:
        model = AppCategory
        fields = ['id', 'name', 'app_count']


class AppTypeSerializer(serializers.ModelSerializer):
    """
    应用类型序列化器
    用于应用类型的 CRUD 操作
    """
    app_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AppType
        fields = ['id', 'name', 'code', 'description', 'is_active', 'sort_order', 'app_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_app_count(self, obj):
        """获取该类型下的应用数量"""
        return obj.apps.count()


class AppSerializer(serializers.ModelSerializer):
    """
    应用序列化器
    支持完整的应用配置，包括类型、Function Calling Parameters 等
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    app_type_name = serializers.CharField(source='app_type.name', read_only=True)
    app_type_code = serializers.CharField(source='app_type.code', read_only=True)
    
    class Meta:
        model = App
        fields = [
            'id', 'name', 'description', 'icon_url', 
            'category', 'category_name',
            'app_type', 'app_type_name', 'app_type_code',
            'execution_mode', 'system_prompt', 'parameters', 
            'provider_id', 'model_name', 'configuration',
            'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_name(self, value):
        """
        验证应用名称
        1. 不能为空
        2. 必须符合驼峰命名规范
        """
        if not value or not value.strip():
            raise serializers.ValidationError("应用名称不能为空")
        
        # 驼峰命名验证
        pattern = r'^[A-Z][a-zA-Z]*$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "应用名称必须符合驼峰命名规范（如 GetWeather），"
                "只允许英文字母，必须以大写字母开头，不允许空格和标点符号"
            )
        
        return value
    
    def validate_description(self, value):
        """验证应用描述不能为空"""
        if not value or not value.strip():
            raise serializers.ValidationError("应用描述不能为空")
        return value
    
    def validate_parameters(self, value):
        """
        验证 Function Calling Parameters 格式
        应符合 OpenAI parameters schema 规范
        """
        if not value:
            return value
        
        # 基本结构验证
        if not isinstance(value, dict):
            raise serializers.ValidationError("parameters 必须是 JSON 对象")
        
        # 如果提供了 parameters，验证必需字段
        if value:
            if 'type' in value and value['type'] != 'object':
                raise serializers.ValidationError("parameters.type 必须为 'object'")
            
            if 'properties' in value:
                properties = value['properties']
                if not isinstance(properties, dict):
                    raise serializers.ValidationError("parameters.properties 必须是对象")
                
                # 验证每个属性的格式
                for prop_name, prop_def in properties.items():
                    if not isinstance(prop_def, dict):
                        raise serializers.ValidationError(f"属性 {prop_name} 的定义必须是对象")
                    if 'type' not in prop_def:
                        raise serializers.ValidationError(f"属性 {prop_name} 必须包含 type 字段")
        
        return value
    
    def validate_app_type(self, value):
        """
        验证应用类型是否有效且已启用
        """
        if value and not value.is_active:
            raise serializers.ValidationError(f"应用类型 '{value.name}' 暂未开放")
        return value


class AppPublishSerializer(serializers.ModelSerializer):
    """
    应用发布序列化器
    用于发布应用时保存完整配置
    """
    class Meta:
        model = App
        fields = [
            'execution_mode',
            'name', 'description', 'icon_url',
            'system_prompt', 'parameters',
            'provider_id', 'model_name', 'configuration'
        ]
    
    def validate_name(self, value):
        """验证应用名称"""
        if not value or not value.strip():
            raise serializers.ValidationError("应用名称不能为空")
        
        pattern = r'^[A-Z][a-zA-Z]*$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "应用名称必须符合驼峰命名规范（如 GetWeather）"
            )
        return value
    
    def validate_description(self, value):
        """验证应用描述"""
        if not value or not value.strip():
            raise serializers.ValidationError("应用描述不能为空")
        return value
    
    def validate(self, attrs):
        """
        发布时的完整性验证
        """
        # 验证必需字段
        if not attrs.get('name'):
            raise serializers.ValidationError({"name": "应用名称不能为空"})
        
        if not attrs.get('description'):
            raise serializers.ValidationError({"description": "应用描述不能为空"})
        
        if not attrs.get('system_prompt'):
            raise serializers.ValidationError({"system_prompt": "系统提示词不能为空"})
        
        if not attrs.get('model_name'):
            raise serializers.ValidationError({"model_name": "必须选择一个模型"})
        
        return attrs


class AppListSerializer(serializers.ModelSerializer):
    """
    应用列表序列化器（精简版）
    用于应用广场列表展示
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    app_type_name = serializers.CharField(source='app_type.name', read_only=True)
    app_type_code = serializers.CharField(source='app_type.code', read_only=True)
    
    class Meta:
        model = App
        fields = [
            'id', 'name', 'description', 'icon_url',
            'category', 'category_name',
            'app_type', 'app_type_name', 'app_type_code',
            'execution_mode', 'is_featured', 'created_at'
        ]
    
    def validate_name(self, value):
        """验证应用名称"""
        if not value or not value.strip():
            raise serializers.ValidationError("应用名称不能为空")
        
        pattern = r'^[A-Z][a-zA-Z]*$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "应用名称必须符合驼峰命名规范（如 GetWeather），"
                "只允许英文字母，必须以大写字母开头，不允许空格和标点符号"
            )
        return value
    
    def validate_description(self, value):
        """验证应用描述"""
        if not value or not value.strip():
            raise serializers.ValidationError("应用描述不能为空")
        return value


# ============================
# App 执行相关序列化器
# ============================

class AppInvokeRequestSerializer(serializers.Serializer):
    """
    API 直接调用请求序列化器
    用于通过 API 直接执行 App
    """
    # 用户输入的消息
    message = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="用户输入的消息内容"
    )
    # 可选的上下文消息（历史对话）
    context = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="可选的历史消息上下文，格式为 [{'role': 'user|assistant', 'content': '...'}]"
    )
    # Function Calling 参数传入
    parameters = serializers.DictField(
        required=False,
        default=dict,
        help_text="传入的 Function Calling 参数"
    )
    # 是否启用流式响应
    stream = serializers.BooleanField(
        required=False,
        default=False,
        help_text="是否启用流式响应"
    )


class AppFunctionCallingRequestSerializer(serializers.Serializer):
    """
    Function Calling 调用请求序列化器
    格式符合 OpenAI Function Calling 规范
    """
    # 函数名（即 App 名称）
    name = serializers.CharField(
        required=True,
        help_text="函数名称（即 App 名称）"
    )
    # 函数参数
    arguments = serializers.JSONField(
        required=True,
        help_text="函数参数，JSON 格式"
    )


class AppMCPRequestSerializer(serializers.Serializer):
    """
    MCP (Model Context Protocol) 调用请求序列化器
    符合 MCP 协议规范
    """
    # 工具调用 ID
    call_id = serializers.CharField(
        required=False,
        help_text="工具调用 ID，若不传则自动生成"
    )
    # 工具名（即 App 名称）
    tool_name = serializers.CharField(
        required=True,
        help_text="工具名称（即 App 名称）"
    )
    # 工具参数
    input = serializers.JSONField(
        required=False,
        default=dict,
        help_text="工具调用输入参数"
    )


class AppExecuteResponseSerializer(serializers.Serializer):
    """
    App 执行响应序列化器
    统一的执行结果返回格式
    """
    # 请求 ID
    request_id = serializers.CharField(help_text="请求唯一标识")
    # 应用 ID
    app_id = serializers.CharField(help_text="执行的应用 ID")
    # 应用名称
    app_name = serializers.CharField(help_text="执行的应用名称")
    # 执行状态
    status = serializers.ChoiceField(
        choices=['success', 'error', 'pending'],
        help_text="执行状态"
    )
    # 执行结果
    content = serializers.CharField(
        allow_blank=True,
        help_text="执行结果内容"
    )
    # 错误信息（如有）
    error = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="错误信息"
    )
    # Token 使用统计
    usage = serializers.DictField(
        required=False,
        help_text="Token 使用统计"
    )
    # 执行耗时（毫秒）
    latency_ms = serializers.IntegerField(
        required=False,
        help_text="执行耗时（毫秒）"
    )
