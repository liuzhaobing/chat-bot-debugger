from rest_framework import serializers
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus, DeviceProtocol, TestTask, DigitalEmployee
import uuid


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
        fields = ['id', 'protocol', 'category', 'functions_md', 'created_at', 'updated_at']


class TTSVoiceSimpleSerializer(serializers.Serializer):
    """TTS音色简化的序列化器"""
    speaker = serializers.CharField()  # TTSVoice 的主键
    name = serializers.CharField()     # 音色名称
    display_name = serializers.CharField(source='name')  # 兼容前端，实际返回 name


class DigitalEmployeeSerializer(serializers.ModelSerializer):
    """数字员工序列化器"""
    tts_voice = TTSVoiceSimpleSerializer(read_only=True)
    tts_voice_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    task_count = serializers.SerializerMethodField(help_text="任务数量")

    class Meta:
        model = DigitalEmployee
        fields = [
            'id', 'name', 'tts_voice', 'tts_voice_id',
            'avatar_index', 'is_active',
            'created_at', 'updated_at', 'task_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def create(self, validated_data):
        tts_voice_id = validated_data.pop('tts_voice_id', None)

        if tts_voice_id:
            from chat.models import TTSVoice
            try:
                validated_data['tts_voice'] = TTSVoice.objects.get(speaker=tts_voice_id)
            except TTSVoice.DoesNotExist:
                raise serializers.ValidationError({'tts_voice_id': 'TTS音色不存在'})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        tts_voice_id = validated_data.pop('tts_voice_id', None)

        if tts_voice_id is not None:
            from chat.models import TTSVoice
            try:
                validated_data['tts_voice'] = TTSVoice.objects.get(speaker=tts_voice_id)
            except TTSVoice.DoesNotExist:
                validated_data['tts_voice'] = None

        return super().update(instance, validated_data)


class TestTaskSerializer(serializers.ModelSerializer):
    """测试任务序列化器"""
    employee = DigitalEmployeeSerializer(read_only=True)
    iot_protocol = DeviceProtocolSerializer(read_only=True)
    employee_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    iot_protocol_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    # 保留 tts_voice 用于向后兼容
    tts_voice = TTSVoiceSimpleSerializer(read_only=True)

    class Meta:
        model = TestTask
        fields = [
            'id', 'name', 'prd_content', 'status',
            'employee', 'iot_protocol', 'session_id', 'job_instance_id',
            'employee_id', 'iot_protocol_id',
            'tts_voice',  # 向后兼容
            'report_url', 'report_data',
            'result_summary', 'error_message',
            'created_at', 'updated_at', 'started_at', 'completed_at'
        ]
        # job_instance_id 可以由前端传入，不再设为只读
        read_only_fields = ['report_url', 'report_data', 'result_summary', 'error_message', 'started_at', 'completed_at']

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id', None)
        iot_protocol_id = validated_data.pop('iot_protocol_id', None)

        # 如果没有提供 job_instance_id，自动生成
        if not validated_data.get('job_instance_id'):
            validated_data['job_instance_id'] = str(uuid.uuid4())

        # 设置外键关系
        if employee_id:
            try:
                validated_data['employee'] = DigitalEmployee.objects.get(id=employee_id)
            except DigitalEmployee.DoesNotExist:
                pass

        if iot_protocol_id:
            try:
                validated_data['iot_protocol'] = DeviceProtocol.objects.get(id=iot_protocol_id)
            except DeviceProtocol.DoesNotExist:
                pass

        return super().create(validated_data)

    def update(self, instance, validated_data):
        employee_id = validated_data.pop('employee_id', None)
        iot_protocol_id = validated_data.pop('iot_protocol_id', None)

        # 设置外键关系
        if employee_id is not None:
            try:
                validated_data['employee'] = DigitalEmployee.objects.get(id=employee_id)
            except DigitalEmployee.DoesNotExist:
                validated_data['employee'] = None

        if iot_protocol_id is not None:
            try:
                validated_data['iot_protocol'] = DeviceProtocol.objects.get(id=iot_protocol_id)
            except DeviceProtocol.DoesNotExist:
                validated_data['iot_protocol'] = None

        return super().update(instance, validated_data)