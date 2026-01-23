from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallSessionViewSet, ScenarioTestView, ScenarioTestStopView

router = DefaultRouter()
router.register(r'sessions', CallSessionViewSet, basename='call-session')

urlpatterns = [
    path('', include(router.urls)),
    path('scenario-test/', ScenarioTestView.as_view(), name='scenario-test'),
    path('scenario-test/stop/', ScenarioTestStopView.as_view(), name='scenario-test-stop'),
]
