from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallSessionViewSet

router = DefaultRouter()
router.register(r'sessions', CallSessionViewSet, basename='call-session')

urlpatterns = [
    path('', include(router.urls)),
]
