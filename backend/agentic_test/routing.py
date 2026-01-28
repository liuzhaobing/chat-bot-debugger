from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # VAD+ASR测试路由必须放在前面，因为它更具体
    re_path(r'ws/agentic-test/vad-asr-test/$', consumers.VadAsrTestConsumer.as_asgi()),
    # 通用会话路由放在后面
    re_path(r'ws/agentic-test/(?P<session_id>[^/]+)/$', consumers.AgenticTestConsumer.as_asgi()),
]