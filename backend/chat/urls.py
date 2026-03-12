from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProviderViewSet, LLMModelViewSet, ConversationViewSet,
    ChatCompletionView, AppViewSet, AppCategoryViewSet, AppTypeViewSet,
    AppScenarioViewSet, TTSSynthesisViewSet
)

router = DefaultRouter()
router.register(r'providers', ProviderViewSet)
router.register(r'models', LLMModelViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'apps', AppViewSet)
router.register(r'app-categories', AppCategoryViewSet)
router.register(r'app-types', AppTypeViewSet)
router.register(r'scenarios', AppScenarioViewSet, basename='app-scenario')
router.register(r'tts-voices', TTSSynthesisViewSet, basename='tts-voice')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/completions', ChatCompletionView.as_view(), name='chat-completions'),
]
