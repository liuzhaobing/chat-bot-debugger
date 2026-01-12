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

class App(models.Model):
    CATEGORY_CHOICES = (
        ('featured', '精选'),
        ('lifestyle', '生活方式'),
        ('productivity', '工作效率'),
        ('other', '其他'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
