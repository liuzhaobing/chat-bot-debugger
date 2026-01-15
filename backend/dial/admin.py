from django.contrib import admin
from .models import CallSession, CallTranscript


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user_id', 'agent_type', 'status', 'started_at', 'duration']
    list_filter = ['status', 'agent_type', 'started_at']
    search_fields = ['session_id', 'user_id', 'room_id']


@admin.register(CallTranscript)
class CallTranscriptAdmin(admin.ModelAdmin):
    list_display = ['session', 'speaker', 'text', 'is_final', 'timestamp']
    list_filter = ['speaker', 'is_final', 'timestamp']
    search_fields = ['text']
