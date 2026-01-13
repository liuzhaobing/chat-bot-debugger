from rest_framework import serializers
from .models import Provider, LLMModel, Conversation, Message, App, AppCategory


class LLMModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        fields = ['id', 'name', 'display_name']

class ProviderSerializer(serializers.ModelSerializer):
    models = LLMModelSerializer(many=True, read_only=True)
    class Meta:
        model = Provider
        fields = ['id', 'name', 'base_url', 'api_key', 'models']
        extra_kwargs = {'api_key': {'write_only': True}}

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at']

class AppCategorySerializer(serializers.ModelSerializer):
    app_count = serializers.IntegerField(read_only=True, source='apps.count')
    class Meta:
        model = AppCategory
        fields = ['id', 'name', 'app_count']

class AppSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = App
        fields = [
            'id', 'name', 'description', 'icon_url', 'category', 'category_name', 
            'system_prompt', 'configuration', 'variables',
            'is_featured', 'created_at'
        ]
