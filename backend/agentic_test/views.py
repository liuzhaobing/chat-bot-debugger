from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus
from .serializers import AgenticTestSessionSerializer, AgenticTestLogSerializer, DeviceStatusSerializer
from .services import IOTService
import logging
import asyncio

logger = logging.getLogger(__name__)


class AgenticTestSessionViewSet(viewsets.ModelViewSet):
    """Agentic Test 会话视图集"""
    queryset = AgenticTestSession.objects.all()
    serializer_class = AgenticTestSessionSerializer
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """创建新的测试会话"""
        name = request.data.get('name', '新测试会话')
        session = AgenticTestSession.objects.create(name=name)
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活会话"""
        session = self.get_object()
        # 先停用其他会话
        AgenticTestSession.objects.filter(is_active=True).update(is_active=False)
        # 激活当前会话
        session.is_active = True
        session.save()
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取会话日志"""
        session = self.get_object()
        logs = session.logs.all()[:100]  # 最近100条日志
        serializer = AgenticTestLogSerializer(logs, many=True)
        return Response(serializer.data)


class DeviceStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """设备状态视图集"""
    queryset = DeviceStatus.objects.all()
    serializer_class = DeviceStatusSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取设备状态摘要"""
        devices = self.get_queryset()
        summary = {
            'total_devices': devices.count(),
            'device_types': list(devices.values_list('device_type', flat=True).distinct()),
            'last_updated': devices.order_by('-last_updated').first().last_updated if devices.exists() else None
        }
        return Response(summary)


@api_view(['POST'])
def test_iot_connection(request):
    """测试IOT连接"""
    try:
        iot_token = request.data.get('iot_token')
        family_id = request.data.get('family_id')
        env = request.data.get('env', 'test')
        
        if not iot_token or not family_id:
            return Response({
                'success': False,
                'error': 'IOT token和family_id都是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建IOT服务实例
        iot_service = IOTService(env=env)
        
        # 测试连接 - 尝试获取家庭设备列表
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(iot_service.get_family_devices(family_id, iot_token))
        finally:
            loop.close()
        
        if result.get('success', False) or result.get('rc') == 0:
            return Response({
                'success': True,
                'message': 'IOT连接测试成功',
                'device_count': len(result.get('data', []))
            })
        else:
            return Response({
                'success': False,
                'error': result.get('msg', '连接测试失败')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"IOT connection test failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_family_devices(request):
    """获取家庭设备列表"""
    try:
        iot_token = request.data.get('iot_token')
        family_id = request.data.get('family_id')
        env = request.data.get('env', 'test')
        
        if not iot_token or not family_id:
            return Response({
                'success': False,
                'error': 'IOT token和family_id都是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建IOT服务实例
        iot_service = IOTService(env=env)
        
        # 获取家庭设备列表
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(iot_service.get_family_devices(family_id, iot_token))
        finally:
            loop.close()
        
        return Response(result)
            
    except Exception as e:
        logger.error(f"Failed to get family devices: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_device_status(request):
    """获取设备状态详情"""
    try:
        iot_token = request.data.get('iot_token')
        device_guid = request.data.get('device_guid')
        env = request.data.get('env', 'test')
        
        if not iot_token or not device_guid:
            return Response({
                'success': False,
                'error': 'IOT token和device_guid都是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建IOT服务实例
        iot_service = IOTService(env=env)
        
        # 获取设备状态
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(iot_service.get_device_status(device_guid, iot_token))
        finally:
            loop.close()
        
        return Response(result)
            
    except Exception as e:
        logger.error(f"Failed to get device status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)