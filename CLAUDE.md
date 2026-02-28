# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat-bot-debugger is a full-stack application for testing and debugging AI chat bots and voice agents. It provides tools for testing LLM providers, managing conversations, testing voice call scenarios, and running agentic tests with VAD/ASR capabilities.

## Architecture

### Backend (Django)
- **Framework**: Django 3.2 with Django REST Framework + Channels (ASGI)
- **Database**: SQLite (development)
- **WebSocket**: Channels with InMemoryChannelLayer (development)

**Django Apps**:
- `chat` - LLM providers, models, conversations, messages, apps (Function Calling tools), app categories/scenarios
- `dial` - Voice call sessions and scenario testing for voice agents
- `agentic_test` - WebSocket consumers for real-time VAD/ASR testing, agent loop execution
- `core` - Project settings, ASGI/WSGI configuration, URL routing

**Key Files**:
- `backend/core/asgi.py` - ASGI application entry point, routes HTTP and WebSocket
- `backend/core/urls.py` - Main URL configuration
- `backend/agentic_test/routing.py` - WebSocket URL patterns for agentic tests
- `backend/agentic_test/consumers.py` - WebSocket consumers (VadAsrTestConsumer, AgenticTestConsumer)
- `backend/agentic_test/agent_loop.py` - Agent execution loop logic
- `backend/agentic_test/services.py` - Business logic for agentic testing

### Frontend (Vue.js 2)
- **Framework**: Vue 2.6 with Vue Router + Vuex
- **UI**: Custom components with highlight.js for code, markdown-it for rendering

**View Structure** (`frontend/src/views/agent/`):
- `chat-completion/` - Chat interface with LLM providers
- `model-square/` - Model management and debugging
- `app-square/` - App marketplace (Function Calling tools)
- `dial-agent/` - Voice call testing interface
- `agentic-test/` - VAD/ASR testing interface

## Commands

### Backend
```bash
cd backend

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Development server (HTTP only)
python manage.py runserver

# ASGI server (HTTP + WebSocket) - required for agentic tests
./start_asgi.sh  # Uses conda env 'chat-bot-debugger'
# Or directly:
uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --reload

# Run tests
python manage.py test
python manage.py test chat.test_api  # Specific test module
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Development server (proxies /api to backend:8000)
npm run serve

# Production build
npm run build

# Lint
npm run lint
```

## Development Notes

- The ASGI server (`uvicorn`) is required for WebSocket functionality used by agentic tests
- Frontend dev server proxies `/api/*` requests to `http://127.0.0.1:8000`
- WebSocket endpoints: `ws://localhost:8000/ws/agentic-test/<session_id>/` and `ws://localhost:8000/ws/agentic-test/vad-asr-test/`
- App model uses camel-case naming convention for Function Calling compatibility (e.g., `GetWeather`)