from django.contrib import admin
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus, DigitalEmployee, TestTask, DeviceProtocol


@admin.register(AgenticTestSession)
class AgenticTestSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(AgenticTestLog)
class AgenticTestLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'log_type', 'content', 'timestamp']
    list_filter = ['log_type', 'timestamp']
    search_fields = ['content']
    readonly_fields = ['id', 'timestamp']
    raw_id_fields = ['session']


@admin.register(DeviceStatus)
class DeviceStatusAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'device_type', 'device_id', 'last_updated']
    list_filter = ['device_type', 'last_updated']
    search_fields = ['device_name', 'device_id']
    readonly_fields = ['id', 'last_updated']


@admin.register(DigitalEmployee)
class DigitalEmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'tts_voice', 'avatar_index', 'is_active', 'created_at']
    list_filter = ['is_active', 'avatar_index', 'created_at']
    search_fields = ['name', 'tts_voice__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['tts_voice']


@admin.register(TestTask)
class TestTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee', 'status', 'created_at', 'started_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'prd_content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'started_at', 'completed_at']
    raw_id_fields = ['employee', 'iot_protocol']


@admin.register(DeviceProtocol)
class DeviceProtocolAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'created_at', 'updated_at']
    list_filter = ['category']
    search_fields = ['id', 'category']
    readonly_fields = ['created_at', 'updated_at']