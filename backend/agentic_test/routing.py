from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/agentic-test/(?P<session_id>[^/]+)/$', consumers.AgenticTestConsumer.as_asgi()),
]