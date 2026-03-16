from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import AgenticTestSession, AgenticTestLog, DeviceStatus, DeviceProtocol, TestTask, DigitalEmployee
from .serializers import (
    AgenticTestSessionSerializer, AgenticTestLogSerializer, DeviceStatusSerializer,
    DeviceProtocolSerializer, TestTaskSerializer, DigitalEmployeeSerializer
)
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


class DeviceProtocolViewSet(viewsets.ModelViewSet):
    """设备控制协议视图集"""
    queryset = DeviceProtocol.objects.all()
    serializer_class = DeviceProtocolSerializer
    lookup_field = 'id'


class DigitalEmployeeViewSet(viewsets.ModelViewSet):
    """数字员工视图集

    提供数字员工的完整CRUD操作，以及获取员工任务历史等功能
    """
    queryset = DigitalEmployee.objects.all()
    serializer_class = DigitalEmployeeSerializer

    def get_queryset(self):
        """支持按 is_active 筛选"""
        queryset = DigitalEmployee.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)
        return queryset.select_related('tts_voice')

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """获取该员工的任务历史"""
        employee = self.get_object()
        tasks = employee.tasks.all()[:50]  # 最近50条任务
        serializer = TestTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TestTaskViewSet(viewsets.ModelViewSet):
    """场景测试任务视图集
    
    提供测试任务的完整CRUD操作，以及启动任务、下载报告等功能
    """
    queryset = TestTask.objects.all()
    serializer_class = TestTaskSerializer
    
    def get_queryset(self):
        """支持按状态筛选"""
        queryset = TestTask.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.select_related('employee__tts_voice', 'iot_protocol')
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动测试任务"""
        task = self.get_object()
        
        if task.status == 'running':
            return Response({
                'status': 'error',
                'message': '任务正在运行中'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = timezone.now()
        task.error_message = None
        task.save()
        
        # TODO: 异步启动测试任务执行
        # 这里可以启动一个后台任务来执行测试
        
        return Response({
            'status': 'success',
            'message': '任务已启动',
            'task': TestTaskSerializer(task).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成任务（内部API，由测试执行器调用）"""
        task = self.get_object()
        
        report_url = request.data.get('report_url')
        report_data = request.data.get('report_data', {})
        result_summary = request.data.get('result_summary', '')
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.report_url = report_url
        task.report_data = report_data
        task.result_summary = result_summary
        task.save()
        
        return Response({
            'status': 'success',
            'message': '任务已完成',
            'task': TestTaskSerializer(task).data
        })
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """标记任务失败（内部API，由测试执行器调用）"""
        task = self.get_object()
        
        error_message = request.data.get('error_message', '未知错误')
        
        task.status = 'failed'
        task.completed_at = timezone.now()
        task.error_message = error_message
        task.save()
        
        return Response({
            'status': 'success',
            'message': '任务已标记为失败',
            'task': TestTaskSerializer(task).data
        })
    
    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        """下载测试报告"""
        task = self.get_object()
        
        if not task.report_url:
            return Response({
                'status': 'error',
                'message': '报告尚未生成'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'report_url': task.report_url,
            'report_data': task.report_data
        })
