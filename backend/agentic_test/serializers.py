from rest_framework import serializers
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus


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