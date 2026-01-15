from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
import requests
import json
from .models import Provider, LLMModel, Conversation, Message, App, AppCategory, AppType
from .serializers import (
    ProviderSerializer, ConversationSerializer, MessageSerializer, 
    LLMModelSerializer, AppSerializer, AppCategorySerializer,
    AppTypeSerializer, AppPublishSerializer, AppListSerializer
)

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

class AppCategoryViewSet(viewsets.ModelViewSet):
    """
    应用分类视图集
    提供应用分类的 CRUD 操作
    """
    queryset = AppCategory.objects.all()
    serializer_class = AppCategorySerializer

    def destroy(self, request, *args, **kwargs):
        """删除分类前检查是否有关联应用"""
        instance = self.get_object()
        if instance.apps.exists():
            return Response(
                {"error": "该分组下仍有应用，无法删除。请先移动或删除应用。"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class AppTypeViewSet(viewsets.ModelViewSet):
    """
    应用类型视图集
    提供应用类型的查询和管理
    """
    queryset = AppType.objects.all()
    serializer_class = AppTypeSerializer
    
    def get_queryset(self):
        """
        支持筛选：
        - is_active: 是否启用
        """
        queryset = AppType.objects.all()
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

class AppViewSet(viewsets.ModelViewSet):
    """
    应用视图集
    提供应用的完整 CRUD 操作，支持类型筛选和发布功能
    """
    queryset = App.objects.all()
    
    def get_serializer_class(self):
        """根据不同的 action 返回不同的序列化器"""
        if self.action == 'list':
            return AppListSerializer
        elif self.action == 'publish':
            return AppPublishSerializer
        return AppSerializer

    def get_queryset(self):
        """
        支持多种筛选条件：
        - category: 按分类ID或名称筛选
        - app_type: 按应用类型ID或code筛选
        - is_featured: 是否精选
        - search: 搜索应用名称或描述
        """
        queryset = App.objects.select_related('category', 'app_type').all()
        
        # 按分类筛选
        category = self.request.query_params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name=category)
        
        # 按应用类型筛选
        app_type = self.request.query_params.get('app_type')
        if app_type:
            if app_type.isdigit():
                queryset = queryset.filter(app_type_id=app_type)
            else:
                queryset = queryset.filter(app_type__code=app_type)
        
        # 按精选状态筛选
        is_featured = self.request.query_params.get('is_featured')
        if is_featured:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        发布应用
        保存完整的应用配置，包括模型、参数等
        """
        app = self.get_object()
        serializer = AppPublishSerializer(app, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "应用发布成功",
                "data": AppSerializer(app).data
            })
        
        return Response({
            "status": "error",
            "message": "发布失败",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def auto_save_prompt(self, request, pk=None):
        """
        自动保存 system_prompt
        仅保存提示词，不保存其他字段
        """
        app = self.get_object()
        system_prompt = request.data.get('system_prompt')
        
        if system_prompt is not None:
            app.system_prompt = system_prompt
            app.save(update_fields=['system_prompt', 'updated_at'])
            return Response({
                "status": "success",
                "message": "提示词已自动保存"
            })
        
        return Response({
            "status": "error",
            "message": "未提供 system_prompt"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def function_schema(self, request, pk=None):
        """
        获取应用的 Function Calling Schema
        用于将应用作为工具调用
        """
        app = self.get_object()
        schema = app.get_function_schema()
        return Response(schema)

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
    
    @action(detail=True, methods=['patch'], url_path='messages/(?P<message_id>[^/.]+)/retry')
    def retry_message(self, request, pk=None, message_id=None):
        """
        重试消息功能
        清空 assistant 消息的 content 和 reasoning_content，然后重新请求
        """
        conversation = self.get_object()
        
        try:
            message = Message.objects.get(id=message_id, conversation=conversation)
        except Message.DoesNotExist:
            return Response({"error": "消息不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        if message.role != 'assistant':
            return Response({"error": "只能重试 assistant 消息"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取该消息之前的所有消息作为上下文
        previous_messages = conversation.messages.filter(
            created_at__lt=message.created_at
        ).order_by('created_at')
        
        # 构建消息列表
        messages_payload = []
        for msg in previous_messages:
            messages_payload.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 获取重试参数
        enable_thinking = request.data.get('enable_thinking', False)
        model_name = request.data.get('model')
        temperature = request.data.get('temperature')
        max_tokens = request.data.get('max_tokens')
        
        if not model_name:
            return Response({"error": "必须提供 model 参数"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取 Provider 和 Model（需要同时匹配 provider_id 和 model_name）
        try:
            # 从之前的消息中获取 provider_id，或从请求参数中获取
            provider_id = request.data.get('provider_id')
            if not provider_id:
                return Response({"error": "必须提供 provider_id 参数"}, status=status.HTTP_400_BAD_REQUEST)
            
            llm_model = LLMModel.objects.get(name=model_name, provider_id=provider_id)
            provider = llm_model.provider
        except LLMModel.DoesNotExist:
            return Response({"error": "模型不存在"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 构建请求 payload
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
            payload['temperature'] = float(temperature)
        if max_tokens is not None:
            payload['max_tokens'] = int(max_tokens)
        if enable_thinking:
            payload['extra_body'] = {"enable_thinking": True}
        
        # 调用上游 API
        try:
            response = requests.post(
                f"{provider.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        
        # 流式响应生成器
        def retry_stream_generator():
            assistant_content = ""
            reasoning_content = ""
            token_usage_data = None
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
                                
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    
                                    if 'reasoning_content' in delta:
                                        reasoning_content += delta['reasoning_content']
                                    
                                    if 'content' in delta:
                                        assistant_content += delta['content']
                                
                                if 'usage' in data:
                                    token_usage_data = data['usage']
                                    
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
            
            # 更新数据库中的消息
            message.content = assistant_content
            message.reasoning_content = reasoning_content if reasoning_content else None
            message.token_usage = token_usage_data
            message.save()
            conversation.save()
        
        response_stream = StreamingHttpResponse(
            retry_stream_generator(),
            content_type='text/event-stream'
        )
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream

class ChatCompletionView(APIView):
    def post(self, request):
        provider_id = request.data.get('provider_id')
        conversation_id = request.data.get('conversation_id')
        model_name = request.data.get('model')
        temperature = request.data.get('temperature')
        max_tokens = request.data.get('max_tokens')
        messages = request.data.get('messages')
        system_prompt = request.data.get('system_prompt')
        extra_body = request.data.get('extra_body', {})  # 获取 extra_body 参数
        
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
            # 如果content是list（多模态），需要转为JSON字符串存储
            if isinstance(content, list):
                content = json.dumps(content, ensure_ascii=False)
            # 字符串直接存
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

        # 4. Get Provider and Model Config（必须同时匹配 provider_id 和 model_name）
        if not provider_id:
            return Response({"error": "provider_id is required"}, status=400)
        
        try:
            llm_model = LLMModel.objects.get(name=model_name, provider_id=provider_id)
            provider = llm_model.provider
        except LLMModel.DoesNotExist:
            return Response({"error": f"Model '{model_name}' not found for provider {provider_id}"}, status=400)

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
        
        # 添加 extra_body 支持（深度思考等）
        if extra_body and isinstance(extra_body, dict):
            # 验证 enable_thinking 参数
            enable_thinking = extra_body.get('enable_thinking', False)
            if isinstance(enable_thinking, bool):
                payload['extra_body'] = {"enable_thinking": enable_thinking}
        
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
            reasoning_content = ""  # 存储思考内容
            token_usage_data = None  # 存储 token 统计
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
                                
                                # 解析 delta 内容
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    
                                    # 获取思考内容
                                    if 'reasoning_content' in delta:
                                        reasoning_content += delta['reasoning_content'] if delta['reasoning_content'] else ''
                                    
                                    # 获取最终回答
                                    if 'content' in delta:
                                        assistant_content += delta['content'] if delta['content'] else ''
                                
                                # 解析 token 使用量
                                if 'usage' in data:
                                    token_usage_data = data['usage']
                                    
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
            
            # Save full message after stream ends
            if assistant_content or reasoning_content:
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=assistant_content,
                    reasoning_content=reasoning_content if reasoning_content else None,
                    token_usage=token_usage_data
                )
                conversation.save()

        response_stream = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream
