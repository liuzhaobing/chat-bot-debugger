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

class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
