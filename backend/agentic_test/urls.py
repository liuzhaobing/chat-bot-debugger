from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgenticTestSessionViewSet,
    DeviceStatusViewSet,
    DeviceProtocolViewSet,
    TestTaskViewSet,
    test_iot_connection,
    get_family_devices,
    get_device_status
)

router = DefaultRouter()
router.register(r'sessions', AgenticTestSessionViewSet)
router.register(r'devices', DeviceStatusViewSet)
router.register(r'device-protocols', DeviceProtocolViewSet)
router.register(r'test-tasks', TestTaskViewSet)

urlpatterns = [
    path('api/agentic-test/', include(router.urls)),
    path('api/agentic-test/iot/test-connection/', test_iot_connection, name='test_iot_connection'),
    path('api/agentic-test/iot/family-devices/', get_family_devices, name='get_family_devices'),
    path('api/agentic-test/iot/device-status/', get_device_status, name='get_device_status'),
]