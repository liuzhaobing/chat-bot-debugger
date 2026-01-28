conda activate chat-bot-debugger
DJANGO_SETTINGS_MODULE=core.settings uvicorn core.asgi:application --host 0.0.0.0 --port 8000