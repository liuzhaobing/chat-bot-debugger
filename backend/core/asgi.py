"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/

注意：WebSocket 服务已迁移到独立的 Worker 服务 (FastAPI)
- Worker 服务端口: 8001
- WebSocket 端点: /ws/agentic-test/{session_id}/, /ws/agentic-test/vad-asr-test/
- Django 仅处理 HTTP 请求
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application
django.setup()

# Django 只处理 HTTP 请求
# WebSocket 已迁移到 Worker 服务 (FastAPI on port 8001)
application = get_asgi_application()