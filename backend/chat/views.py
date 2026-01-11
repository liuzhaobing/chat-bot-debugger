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
        content = request.data.get('content')
        provider_id = request.data.get('provider_id') # Optional if we can infer from model, but safer to pass
        
        # 1. Get or Create Conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = Conversation.objects.create(title=content[:30] if content else "New Chat")
        
        # 2. Save User Message
        Message.objects.create(conversation=conversation, role='user', content=content)
        
        # 3. Prepare Context
        # Fetch last N messages or all
        history = conversation.messages.all()
        messages_payload = [{"role": msg.role, "content": msg.content} for msg in history]
        
        # 4. Get Provider and Model Config
        # Simplified: Assume provider_id passed or find via Model
        # If provider_id not passed, try finding model object
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
            "stream": True,
            # Add parameters like temperature here if passed
        }
        if request.data.get('temperature'):
            payload['temperature'] = float(request.data.get('temperature'))

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

        # 6. Stream and Save Assistant Response
        # 6. Stream and Save Assistant Response
        def stream_generator():
            assistant_content = ""
            buffer = ""
            
            # Use iter_content to stream raw bytes immediately
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    text_chunk = chunk.decode('utf-8')
                    yield text_chunk # Pass through immediately
                    
                    # Process for DB saving
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
            
                # Update conversation timestamp
                conversation.save()

        response_stream = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream
