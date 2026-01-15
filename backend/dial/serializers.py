from rest_framework import serializers
from .models import CallSession, CallTranscript


class CallTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallTranscript
        fields = ['id', 'speaker', 'text', 'is_final', 'timestamp']


class CallSessionSerializer(serializers.ModelSerializer):
    transcripts = CallTranscriptSerializer(many=True, read_only=True)
    
    class Meta:
        model = CallSession
        fields = ['id', 'session_id', 'room_id', 'user_id', 'participant_id', 
                  'agent_type', 'config_template', 'status', 'started_at', 
                  'ended_at', 'duration', 'transcripts']
