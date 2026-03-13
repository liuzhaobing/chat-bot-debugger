from rest_framework import serializers
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus, DeviceProtocol, TestTask


class AgenticTestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgenticTestSession
        fields = ['id', 'name', 'created_at', 'updated_at', 'is_active']


class AgenticTestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgenticTestLog
        fields = ['id', 'session', 'log_type', 'content', 'metadata', 'timestamp']


class DeviceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatus
        fields = ['id', 'device_id', 'device_name', 'device_type', 'status', 'last_updated']


class DeviceProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProtocol
        fields = ['id', 'protocol', 'category', 'created_at', 'updated_at']


class TTSVoiceSimpleSerializer(serializers.Serializer):
    """TTS音色简化的序列化器"""
    speaker = serializers.CharField()  # TTSVoice 的主键
    name = serializers.CharField()     # 音色名称
    display_name = serializers.CharField(source='name')  # 兼容前端，实际返回 name


class TestTaskSerializer(serializers.ModelSerializer):
    """测试任务序列化器"""
    tts_voice = TTSVoiceSimpleSerializer(read_only=True)
    iot_protocol = DeviceProtocolSerializer(read_only=True)
    tts_voice_id = serializers.CharField(write_only=True, required=False, allow_null=True)  # 使用 CharField，因为主键是 speaker
    iot_protocol_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = TestTask
        fields = [
            'id', 'name', 'prd_content', 'status',
            'tts_voice', 'iot_protocol',
            'tts_voice_id', 'iot_protocol_id',
            'report_url', 'report_data',
            'result_summary', 'error_message',
            'created_at', 'updated_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['report_url', 'report_data', 'result_summary', 'error_message', 'started_at', 'completed_at']
    
    def create(self, validated_data):
        tts_voice_id = validated_data.pop('tts_voice_id', None)
        iot_protocol_id = validated_data.pop('iot_protocol_id', None)
        
        # 设置外键关系
        if tts_voice_id:
            from chat.models import TTSVoice
            try:
                validated_data['tts_voice'] = TTSVoice.objects.get(speaker=tts_voice_id)
            except TTSVoice.DoesNotExist:
                pass
        
        if iot_protocol_id:
            try:
                validated_data['iot_protocol'] = DeviceProtocol.objects.get(id=iot_protocol_id)
            except DeviceProtocol.DoesNotExist:
                pass
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        tts_voice_id = validated_data.pop('tts_voice_id', None)
        iot_protocol_id = validated_data.pop('iot_protocol_id', None)
        
        # 设置外键关系
        if tts_voice_id is not None:
            from chat.models import TTSVoice
            try:
                validated_data['tts_voice'] = TTSVoice.objects.get(speaker=tts_voice_id)
            except TTSVoice.DoesNotExist:
                validated_data['tts_voice'] = None
        
        if iot_protocol_id is not None:
            try:
                validated_data['iot_protocol'] = DeviceProtocol.objects.get(id=iot_protocol_id)
            except DeviceProtocol.DoesNotExist:
                validated_data['iot_protocol'] = None
        
        return super().update(instance, validated_data)