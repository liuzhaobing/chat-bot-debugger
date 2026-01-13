import json
from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(default="https://api.openai.com/v1")
    api_key = models.CharField(max_length=255, blank=True, help_text="API Key for the provider")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LLMModel(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100, help_text="Model ID like gpt-4 or claude-3-opus")
    display_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# 支持多模态内容的消息模型
class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # content 兼容旧文本，推荐存储为JSON字符串，结构为{"content": [...], "raw_text": "..."}
    content = models.TextField(help_text="消息内容，推荐为多模态JSON数组，兼容纯文本")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

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
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class App(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(AppCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='apps')
    
    # Agent 1.0 Fields
    system_prompt = models.TextField(default="", blank=True, help_text="应用的系统提示词")
    configuration = models.JSONField(default=dict, blank=True, help_text="模型参数配置 (temperature, max_tokens等)")
    variables = models.JSONField(default=list, blank=True, help_text="提示词中定义的变量列表")
    
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
