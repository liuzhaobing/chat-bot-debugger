from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
import requests
import json
from .models import Provider, LLMModel, Conversation, Message
from .serializers import ProviderSerializer, ConversationSerializer, MessageSerializer, LLMModelSerializer

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.filter(is_active=True)
    serializer_class = ProviderSerializer

    @action(detail=True, methods=['post'])
    def refresh_models(self, request, pk=None):
        provider = self.get_object()
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Assume OpenAI compatible /models endpoint
            response = requests.get(f"{provider.base_url}/models", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # OpenAI format: {"data": [{"id": "model-id", ...}]}
            model_list = data.get('data', [])
            saved_models = []
            
            for model_data in model_list:
                model_id = model_data.get('id')
                if model_id:
                     obj, created = LLMModel.objects.update_or_create(
                        provider=provider,
                        name=model_id,
                        defaults={'display_name': model_id}
                     )
                     saved_models.append(obj)
            
            return Response({"status": "success", "count": len(saved_models)})
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class LLMModelViewSet(viewsets.ModelViewSet):
    queryset = LLMModel.objects.all()
    serializer_class = LLMModelSerializer

class ConversationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all().order_by('-updated_at')
    serializer_class = ConversationSerializer
    pagination_class = ConversationPagination

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class ChatCompletionView(APIView):
    def post(self, request):
        conversation_id = request.data.get('conversation_id')
        model_name = request.data.get('model')
        temperature = request.data.get('temperature')
        max_tokens = request.data.get('max_tokens')
        messages = request.data.get('messages')
        system_prompt = request.data.get('system_prompt')
        # 1. Get or Create Conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            # 新建会话时，取首条user消息文本做标题
            title = "New Chat"
            if messages and isinstance(messages, list):
                for m in messages:
                    if m.get('role') == 'user':
                        user_content = m.get('content')
                        if isinstance(user_content, list):
                            for seg in user_content:
                                if seg.get('type') == 'text' and seg.get('text'):
                                    title = seg['text'][:30]
                                    break
                        elif isinstance(user_content, str):
                            title = user_content[:30]
                        break
            conversation = Conversation.objects.create(title=title)

        # 2. Save User Message（只保存本次请求的最后一条user消息，兼容content为字符串或多模态数组）
        user_msg = None
        if messages and isinstance(messages, list):
            for m in reversed(messages):
                if m.get('role') == 'user':
                    user_msg = m
                    break
        if user_msg:
            content = user_msg.get('content')
            # 只存content本身，字符串直接存，list直接存（由Django自动序列化）
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=content
            )

        # 3. 兼容messages为纯文本（字符串）或多模态（数组）
        if isinstance(messages, list):
            messages_payload = messages
        elif isinstance(messages, str):
            # 兼容老格式，自动转为OpenAI格式
            messages_payload = [{"role": "user", "content": messages}]
        else:
            messages_payload = []

        # 4. Get Provider and Model Config
        try:
            llm_model = LLMModel.objects.get(name=model_name)
            provider = llm_model.provider
        except LLMModel.DoesNotExist:
            return Response({"error": "Model not found"}, status=400)

        # 5. Call Upstream API (OpenAI Compatible)
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": messages_payload,
            "stream": True
        }
        if temperature is not None:
            try:
                payload['temperature'] = float(temperature)
            except Exception:
                pass
        if max_tokens is not None:
            try:
                payload['max_tokens'] = int(max_tokens)
            except Exception:
                pass
        if system_prompt:
            payload['messages'].insert(0, {"role": "system", "content": system_prompt})
        print("payload:", json.dumps(payload, ensure_ascii=False, indent=4))
        try:
            response = requests.post(
                f"{provider.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=502)

        def stream_generator():
            assistant_content = ""
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    text_chunk = chunk.decode('utf-8')
                    yield text_chunk
                    buffer += text_chunk
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line.startswith("data: "):
                            json_str = line[6:]
                            if json_str == "[DONE]":
                                continue
                            try:
                                data = json.loads(json_str)
                                delta = data['choices'][0]['delta']
                                if 'content' in delta:
                                    assistant_content += delta['content']
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
            # Save full message after stream ends
            if assistant_content:
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=assistant_content
                )
                conversation.save()

        response_stream = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream
