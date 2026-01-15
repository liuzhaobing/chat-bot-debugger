from django.db import models


class CallSession(models.Model):
    """通话会话记录"""
    session_id = models.CharField(max_length=255, unique=True)
    room_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    participant_id = models.CharField(max_length=255)
    agent_type = models.CharField(max_length=100)
    config_template = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='pending')  # pending, active, ended
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # in seconds
    
    class Meta:
        db_table = 'dial_call_session'
        ordering = ['-started_at']


class CallTranscript(models.Model):
    """通话字幕记录"""
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='transcripts')
    speaker = models.CharField(max_length=50)  # speaker00, speaker01
    text = models.TextField()
    is_final = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dial_call_transcript'
        ordering = ['timestamp']
