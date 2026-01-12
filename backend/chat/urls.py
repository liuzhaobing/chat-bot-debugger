from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProviderViewSet, LLMModelViewSet, ConversationViewSet, ChatCompletionView, AppViewSet

router = DefaultRouter()
router.register(r'providers', ProviderViewSet)
router.register(r'models', LLMModelViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'apps', AppViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('chat/completions', ChatCompletionView.as_view(), name='chat-completions'),
]
