from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CallSession, CallTranscript
from .serializers import CallSessionSerializer, CallTranscriptSerializer


class CallSessionViewSet(viewsets.ModelViewSet):
    """通话会话管理"""
    queryset = CallSession.objects.all()
    serializer_class = CallSessionSerializer
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """创建新的通话会话"""
        data = request.data
        session = CallSession.objects.create(
            session_id=data.get('session_id'),
            room_id=data.get('room_id'),
            user_id=data.get('user_id'),
            participant_id=data.get('participant_id'),
            agent_type=data.get('agent_type', 'robam_workflow'),
            config_template=data.get('config_template', 'ai_telephone'),
            status='active'
        )
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """结束通话会话"""
        session = self.get_object()
        from django.utils import timezone
        session.status = 'ended'
        session.ended_at = timezone.now()
        if session.started_at:
            duration = (session.ended_at - session.started_at).total_seconds()
            session.duration = int(duration)
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_transcript(self, request, pk=None):
        """添加字幕记录"""
        session = self.get_object()
        data = request.data
        transcript = CallTranscript.objects.create(
            session=session,
            speaker=data.get('speaker'),
            text=data.get('text'),
            is_final=data.get('is_final', False)
        )
        serializer = CallTranscriptSerializer(transcript)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def transcripts(self, request, pk=None):
        """获取会话的所有字幕"""
        session = self.get_object()
        transcripts = session.transcripts.all()
        serializer = CallTranscriptSerializer(transcripts, many=True)
        return Response(serializer.data)
