from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
import httpx
import json
import uuid
import time
import base64
from jinja2 import Template
from .models import Provider, LLMModel, Conversation, Message, App, AppCategory, AppType, AppScenario, TTSVoice
from .serializers import (
    ProviderSerializer, ConversationSerializer, MessageSerializer,
    LLMModelSerializer, AppSerializer, AppCategorySerializer,
    AppTypeSerializer, AppPublishSerializer, AppListSerializer,
    AppInvokeRequestSerializer, AppFunctionCallingRequestSerializer,
    AppMCPRequestSerializer, AppExecuteResponseSerializer,
    AppScenarioSerializer, TTSVoiceSerializer, serializers,
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
            with httpx.Client() as client:
                response = client.get(f"{provider.base_url}/models", headers=headers, timeout=10.0)
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

    # ============================
    # App 执行核心方法
    # ============================

    def _execute_agent_1_0(self, app, user_message=None, context=None, parameters=None):
        """
        执行 Agent 1.0 类型的应用

        支持两种执行模式：
        - chat: 对话聊天式，system_prompt 作为 system 消息，支持上下文
        - task: 任务执行式，prompt_template 替换参数后作为 user 消息，无上下文

        Args:
            app: App 模型实例
            user_message: 用户输入的消息
            context: 可选的历史消息上下文（仅 chat 模式有效）
            parameters: 可选的参数（用于替换提示词中的变量）

        Returns:
            dict: 包含 content, usage, error 的结果字典
        """
        start_time = time.time()

        try:
            # 1. 获取 Provider
            if not app.provider_id:
                return {
                    "status": "error",
                    "content": "",
                    "error": "应用未配置 Provider",
                    "usage": None
                }

            try:
                provider = Provider.objects.get(id=app.provider_id)
            except Provider.DoesNotExist:
                return {
                    "status": "error",
                    "content": "",
                    "error": f"Provider {app.provider_id} 不存在",
                    "usage": None
                }

            # 2. 验证模型配置
            if not app.model_name:
                return {
                    "status": "error",
                    "content": "",
                    "error": "应用未配置模型",
                    "usage": None
                }

            # 3. 构建消息列表 - 根据执行模式采用不同策略
            messages_payload = []
            execution_mode = getattr(app, 'execution_mode', 'chat')

            if execution_mode == 'task':
                # ========== 任务执行式 (Task Mode) ==========
                # 将 system_prompt（任务模板）替换参数后作为 user 消息
                # 每次执行独立，不保留上下文历史

                # 参数替换：使用 Jinja2 渲染模板
                try:
                    prompt_template = Template(app.system_prompt or "").render(**(parameters or {}))
                except Exception as e:
                    # 如果渲染失败，回退到原始 prompt，记录日志（此处暂略），或者直接报错
                    # 为保证鲁棒性，先回退，但通常 Jinja2 很宽容
                    prompt_template = app.system_prompt or ""

                # 最终消息：模板 + 用户输入（如有）
                final_message = prompt_template
                if user_message and user_message.strip():
                    # 如果有额外的用户输入，追加到模板后面
                    final_message = f"{prompt_template}\n\n{user_message}"

                # Task 模式：只有一条 user 消息
                messages_payload.append({
                    "role": "user",
                    "content": final_message
                })

            else:
                # ========== 对话聊天式 (Chat Mode, 默认) ==========
                # system_prompt 作为 system 消息，支持多轮上下文

                # 参数替换：使用 Jinja2 渲染模板
                try:
                    system_prompt = Template(app.system_prompt or "").render(**(parameters or {}))
                except Exception:
                    system_prompt = app.system_prompt or ""

                # 添加系统提示词
                if system_prompt:
                    messages_payload.append({
                        "role": "system",
                        "content": system_prompt
                    })

                # 添加上下文消息（历史对话）
                if context and isinstance(context, list):
                    for msg in context:
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                            messages_payload.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                if user_message:
                    # 添加用户消息
                    messages_payload.append({
                        "role": "user",
                        "content": user_message
                    })

            # 4. 构建请求 payload
            headers = {
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": app.model_name,
                "messages": messages_payload,
                "stream": False
            }

            # 添加配置参数（temperature, max_tokens 等）
            configuration = app.configuration or {}
            if 'temperature' in configuration:
                payload['temperature'] = float(configuration['temperature'])
            if 'max_tokens' in configuration:
                payload['max_tokens'] = int(configuration['max_tokens'])

            # 5. 调用大模型 API
            with httpx.Client() as client:
                response = client.post(
                    f"{provider.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()

            # 6. 解析响应
            content = ""
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')

            usage = result.get('usage', None)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "status": "success",
                "content": content,
                "error": None,
                "usage": usage,
                "latency_ms": latency_ms,
                "execution_mode": execution_mode  # 返回执行模式供调用方参考
            }

        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "content": "",
                "error": f"调用大模型失败: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except httpx.RequestError as e:
            return {
                "status": "error",
                "content": "",
                "error": f"请求错误: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "status": "error",
                "content": "",
                "error": f"执行失败: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    def _execute_agent_1_0_stream(self, app, provider, messages_payload, configuration):
        """
        流式执行 Agent 1.0 类型的应用

        注意：数据库查询必须在生成器外部完成，避免在 ASGI 异步上下文中调用同步 ORM

        Args:
            app: App 模型实例
            provider: Provider 模型实例（已查询）
            messages_payload: 已构建好的消息列表
            configuration: 应用配置

        Yields:
            str: SSE 格式的流式数据行
        """
        start_time = time.time()

        # 内部生成器函数
        def stream_generator():
            nonlocal start_time
            try:
                # 1. 构建请求 payload（启用流式）
                headers = {
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": app.model_name,
                    "messages": messages_payload,
                    "stream": True,
                    "stream_options": {"include_usage": True}
                }

                # 添加配置参数
                if 'temperature' in configuration:
                    payload['temperature'] = float(configuration['temperature'])
                if 'max_tokens' in configuration:
                    payload['max_tokens'] = int(configuration['max_tokens'])

                # 2. 流式调用大模型 API
                with httpx.stream(
                        "POST",
                        f"{provider.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60.0
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield line + '\n'

            except httpx.HTTPStatusError as e:
                error_data = json.dumps({
                    "status": "error",
                    "error": f"调用大模型失败: {str(e)}",
                    "latency_ms": int((time.time() - start_time) * 1000)
                }, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
            except httpx.RequestError as e:
                error_data = json.dumps({
                    "status": "error",
                    "error": f"请求错误: {str(e)}",
                    "latency_ms": int((time.time() - start_time) * 1000)
                }, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
            except Exception as e:
                error_data = json.dumps({
                    "status": "error",
                    "error": f"执行失败: {str(e)}",
                    "latency_ms": int((time.time() - start_time) * 1000)
                }, ensure_ascii=False)
                yield f"data: {error_data}\n\n"

        return stream_generator()

    def _execute_agent_asr(self, app, user_message=None, context=None, parameters=None):
        """
        执行 Agent ASR 类型的应用
        专门处理语音识别任务

        Args:
            app: App 模型实例
            user_message: 用户输入的消息（可能包含音频数据）
            context: 可选的历史消息上下文
            parameters: 可选的参数（包含音频数据等）

        Returns:
            dict: 包含 content, usage, error 的结果字典
        """
        start_time = time.time()
        # print(json.dumps(parameters, ensure_ascii=False))

        try:
            # 1. 获取 Provider
            if not app.provider_id:
                return {
                    "status": "error",
                    "content": "",
                    "error": "应用未配置 Provider",
                    "usage": None,
                    "latency_ms": int((time.time() - start_time) * 1000)
                }

            try:
                provider = Provider.objects.get(id=app.provider_id)
            except Provider.DoesNotExist:
                return {
                    "status": "error",
                    "content": "",
                    "error": f"Provider {app.provider_id} 不存在",
                    "usage": None,
                    "latency_ms": int((time.time() - start_time) * 1000)
                }

            # 2. 验证模型配置
            if not app.model_name:
                return {
                    "status": "error",
                    "content": "",
                    "error": "应用未配置模型",
                    "usage": None,
                    "latency_ms": int((time.time() - start_time) * 1000)
                }

            # 3. 从参数中获取音频数据
            audio_data = None
            audio_format = "wav"
            language = "zh-CN"
            asr_context = None

            if parameters:
                audio_data = parameters.get('audio_data')
                audio_format = parameters.get('audio_format', 'wav')
                language = parameters.get('language', 'zh-CN')
                asr_context = parameters.get('context')

            # 如果没有音频数据，返回错误
            if not audio_data:
                return {
                    "status": "error",
                    "content": "",
                    "error": "缺少音频数据参数 audio_data",
                    "usage": None,
                    "latency_ms": int((time.time() - start_time) * 1000)
                }

            # 4. 构建消息列表
            messages_payload = []

            # 添加系统提示词（如果有）
            if app.system_prompt:
                messages_payload.append({
                    "role": "system",
                    "content": app.system_prompt
                })

            # 构建用户消息
            user_content = []

            # 添加文本前缀
            if asr_context:
                text_prefix = f"Previous assistant reply: {asr_context}\n\nUser input: "
            else:
                text_prefix = "User input: "

            user_content.append({
                "type": "text",
                "text": text_prefix
            })

            # 添加音频数据
            user_content.append({
                "type": "input_audio",
                "input_audio": {
                    "format": audio_format,
                    # "data": audio_data
                    "data": "data:;base64," + audio_data
                }
            })

            messages_payload.append({
                "role": "user",
                "content": user_content
            })

            # 5. 构建请求 payload
            headers = {
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": app.model_name,
                "messages": messages_payload,
                "modalities": ["text"],
                "stream": True,
                "stream_options": {"include_usage": True}
            }

            # 添加配置参数（temperature, max_tokens 等）
            configuration = app.configuration or {}
            if 'temperature' in configuration:
                payload['temperature'] = float(configuration['temperature'])
            if 'max_tokens' in configuration:
                payload['max_tokens'] = int(configuration['max_tokens'])

            # 6. 调用大模型 API (流式)
            recognized_text = ""
            usage = None

            with httpx.stream(
                    "POST",
                    f"{provider.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
            ) as response:
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    recognized_text += content
                            # 获取 usage 信息
                            if "usage" in data:
                                usage = data["usage"]
                        except json.JSONDecodeError:
                            pass  # 忽略解析错误

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "status": "success",
                "content": recognized_text,
                "error": None,
                "usage": usage,
                "latency_ms": latency_ms,
                "execution_mode": "asr"
            }

        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "content": "",
                "error": f"调用大模型失败: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except httpx.RequestError as e:
            return {
                "status": "error",
                "content": "",
                "error": f"请求错误: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "status": "error",
                "content": "",
                "error": f"ASR执行失败: {str(e)}",
                "usage": None,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    def _execute_app(self, app, user_message=None, context=None, parameters=None):
        """
        App 执行调度器
        根据 app_type 调用对应的执行方法

        Args:
            app: App 模型实例
            user_message: 用户输入的消息
            context: 可选的历史消息上下文
            parameters: 可选的参数

        Returns:
            dict: 执行结果
        """
        app_type_code = app.app_type.code if app.app_type else None

        if app_type_code == 'agent_1_0':
            return self._execute_agent_1_0(app, user_message, context, parameters)
        elif app_type_code == 'agent_asr':
            return self._execute_agent_asr(app, user_message, context, parameters)
        else:
            # 其他类型暂未实现
            return {
                "status": "error",
                "content": "",
                "error": f"应用类型 '{app_type_code}' 暂未支持执行",
                "usage": None,
                "latency_ms": 0
            }

    # ============================
    # 1. API 直接调用接口
    # ============================

    @action(detail=True, methods=['get'], url_path='invoke')
    def invoke_info(self, request, pk=None):
        """
        [GET] 获取 API 直接调用的信息
        
        返回应用的基本信息和调用说明
        """
        app = self.get_object()

        return Response({
            "app_id": app.id,
            "app_name": app.name,
            "description": app.description,
            "app_type": app.app_type.code if app.app_type else None,
            "endpoint": f"/api/chat/apps/{app.id}/invoke/",
            "method": "POST",
            "request_format": {
                "message": "string (必填) - 用户输入的消息",
                "context": "array (可选) - 历史消息上下文 [{'role': 'user|assistant', 'content': '...'}]",
                "parameters": "object (可选) - Function Calling 参数",
                "stream": "boolean (可选, 默认 false) - 是否启用流式响应"
            },
            "response_format": {
                "request_id": "string - 请求唯一标识",
                "app_id": "string - 应用 ID",
                "app_name": "string - 应用名称",
                "status": "string - 执行状态 (success/error)",
                "content": "string - 执行结果内容",
                "usage": "object - Token 使用统计",
                "latency_ms": "integer - 执行耗时（毫秒）"
            }
        })

    @action(detail=True, methods=['post'], url_path='invoke')
    def invoke_execute(self, request, pk=None):
        """
        [POST] API 直接调用执行接口

        执行 App 并返回结果
        """
        app = self.get_object()
        request_id = uuid.uuid4().hex

        # 验证请求数据
        serializer = AppInvokeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "content": "",
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 执行 App
        result = self._execute_app(
            app=app,
            user_message=data.get('message', ''),
            context=data.get('context'),
            parameters=data.get('parameters')
        )

        # 构建响应
        response_data = {
            "request_id": request_id,
            "app_id": app.id,
            "app_name": app.name,
            "status": result['status'],
            "content": result['content'],
        }

        if result.get('error'):
            response_data['error'] = result['error']
        if result.get('usage'):
            response_data['usage'] = result['usage']
        if result.get('latency_ms'):
            response_data['latency_ms'] = result['latency_ms']

        status_code = status.HTTP_200_OK if result['status'] == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response_data, status=status_code)

    @action(detail=True, methods=['post'], url_path='invoke/stream')
    def invoke_stream(self, request, pk=None):
        """
        [POST] 流式执行 App

        实时返回 SSE 格式的流式响应，适用于 Agent 1.0 类型应用
        """
        app = self.get_object()
        request_id = uuid.uuid4().hex

        # 验证应用类型
        app_type_code = app.app_type.code if app.app_type else None
        if app_type_code != 'agent_1_0':
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "error": f"流式接口仅支持 Agent 1.0 类型应用，当前类型: {app_type_code}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证请求数据
        serializer = AppInvokeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_message = data.get('message', '')
        context = data.get('context')
        parameters = data.get('parameters')

        # ========== 在生成器外部完成所有同步操作（数据库查询、消息构建） ==========

        # 1. 获取 Provider
        if not app.provider_id:
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "error": "应用未配置 Provider"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            provider = Provider.objects.get(id=app.provider_id)
        except Provider.DoesNotExist:
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "error": f"Provider {app.provider_id} 不存在"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. 验证模型配置
        if not app.model_name:
            return Response({
                "request_id": request_id,
                "app_id": app.id,
                "app_name": app.name,
                "status": "error",
                "error": "应用未配置模型"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. 构建消息列表
        messages_payload = []
        execution_mode = getattr(app, 'execution_mode', 'chat')

        if execution_mode == 'task':
            # 任务执行式 (Task Mode)
            try:
                prompt_template = Template(app.system_prompt or "").render(**(parameters or {}))
            except Exception:
                prompt_template = app.system_prompt or ""

            final_message = prompt_template
            if user_message and user_message.strip():
                final_message = f"{prompt_template}\n\n{user_message}"

            messages_payload.append({
                "role": "user",
                "content": final_message
            })
        else:
            # 对话聊天式 (Chat Mode)
            try:
                system_prompt = Template(app.system_prompt or "").render(**(parameters or {}))
            except Exception:
                system_prompt = app.system_prompt or ""

            if system_prompt:
                messages_payload.append({
                    "role": "system",
                    "content": system_prompt
                })

            if context and isinstance(context, list):
                for msg in context:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages_payload.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })

            if user_message:
                messages_payload.append({
                    "role": "user",
                    "content": user_message
                })

        # 4. 获取配置
        configuration = app.configuration or {}

        # ========== 调用流式执行 ==========
        stream_generator = self._execute_agent_1_0_stream(
            app=app,
            provider=provider,
            messages_payload=messages_payload,
            configuration=configuration
        )

        response_stream = StreamingHttpResponse(
            stream_generator,
            content_type='text/event-stream'
        )
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream

    # ============================
    # 2. Function Calling 调用接口
    # ============================

    @action(detail=True, methods=['get'], url_path='function')
    def function_info(self, request, pk=None):
        """
        [GET] 获取 Function Calling 调用信息
        
        返回符合 OpenAI Function Calling 格式的 Schema
        """
        app = self.get_object()
        schema = app.get_function_schema()

        return Response({
            "app_id": app.id,
            "app_name": app.name,
            "endpoint": f"/api/chat/apps/{app.id}/function/",
            "method": "POST",
            "function_schema": schema,
            "request_format": {
                "name": "string (必填) - 函数名称（即 App 名称）",
                "arguments": "object (必填) - 函数参数，JSON 格式"
            },
            "response_format": {
                "request_id": "string - 请求唯一标识",
                "name": "string - 函数名称",
                "content": "string - 执行结果内容",
                "status": "string - 执行状态"
            }
        })

    @action(detail=True, methods=['post'], url_path='function')
    def function_execute(self, request, pk=None):
        """
        [POST] Function Calling 执行接口

        按照 OpenAI Function Calling 格式执行函数并返回结果
        """
        app = self.get_object()
        request_id = uuid.uuid4().hex

        # 验证请求数据
        serializer = AppFunctionCallingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "request_id": request_id,
                "name": app.name,
                "status": "error",
                "content": "",
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 验证函数名是否匹配
        if data['name'] != app.name:
            return Response({
                "request_id": request_id,
                "name": data['name'],
                "status": "error",
                "content": "",
                "error": f"函数名 '{data['name']}' 与应用名 '{app.name}' 不匹配"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 解析 arguments
        arguments = data['arguments']
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return Response({
                    "request_id": request_id,
                    "name": app.name,
                    "status": "error",
                    "content": "",
                    "error": "arguments 必须是有效的 JSON 格式"
                }, status=status.HTTP_400_BAD_REQUEST)

        # 从 arguments 中提取 message（如果有），否则将 arguments 作为参数传入
        user_message = arguments.pop('message', None) or arguments.pop('query', None) or json.dumps(arguments,
                                                                                                    ensure_ascii=False)

        # 执行 App
        result = self._execute_app(
            app=app,
            user_message=user_message,
            parameters=arguments
        )

        # 构建 Function Calling 格式的响应
        response_data = {
            "request_id": request_id,
            "name": app.name,
            "status": result['status'],
            "content": result['content'],
        }

        if result.get('error'):
            response_data['error'] = result['error']
        if result.get('usage'):
            response_data['usage'] = result['usage']
        if result.get('latency_ms'):
            response_data['latency_ms'] = result['latency_ms']

        status_code = status.HTTP_200_OK if result['status'] == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response_data, status=status_code)

    # ============================
    # 3. MCP 调用接口
    # ============================

    @action(detail=True, methods=['get'], url_path='mcp')
    def mcp_info(self, request, pk=None):
        """
        [GET] 获取 MCP (Model Context Protocol) 调用信息
        
        返回符合 MCP 协议格式的工具定义
        """
        app = self.get_object()

        # 构建 MCP 格式的工具定义
        mcp_tool_definition = {
            "name": app.name,
            "description": app.description,
            "inputSchema": app.parameters or {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        return Response({
            "app_id": app.id,
            "app_name": app.name,
            "endpoint": f"/api/chat/apps/{app.id}/mcp/",
            "method": "POST",
            "mcp_tool_definition": mcp_tool_definition,
            "request_format": {
                "call_id": "string (可选) - 工具调用 ID，若不传则自动生成",
                "tool_name": "string (必填) - 工具名称（即 App 名称）",
                "input": "object (可选) - 工具调用输入参数"
            },
            "response_format": {
                "call_id": "string - 工具调用 ID",
                "tool_name": "string - 工具名称",
                "content": "string - 执行结果内容",
                "status": "string - 执行状态",
                "isError": "boolean - 是否发生错误"
            }
        })

    @action(detail=True, methods=['post'], url_path='mcp')
    def mcp_execute(self, request, pk=None):
        """
        [POST] MCP (Model Context Protocol) 执行接口

        按照 MCP 协议格式执行工具并返回结果
        """
        app = self.get_object()

        # 验证请求数据
        serializer = AppMCPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "call_id": request.data.get('call_id', uuid.uuid4().hex),
                "tool_name": app.name,
                "status": "error",
                "content": "",
                "isError": True,
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        call_id = data.get('call_id') or uuid.uuid4().hex

        # 验证工具名是否匹配
        if data['tool_name'] != app.name:
            return Response({
                "call_id": call_id,
                "tool_name": data['tool_name'],
                "status": "error",
                "content": "",
                "isError": True,
                "error": f"工具名 '{data['tool_name']}' 与应用名 '{app.name}' 不匹配"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取输入参数
        tool_input = data.get('input', {})

        # 从 input 中提取 message（如果有），否则将 input 作为参数传入
        user_message = tool_input.pop('message', None) or tool_input.pop('query', None) or json.dumps(tool_input,
                                                                                                      ensure_ascii=False)

        # 执行 App
        result = self._execute_app(
            app=app,
            user_message=user_message,
            parameters=tool_input
        )

        # 构建 MCP 格式的响应
        response_data = {
            "call_id": call_id,
            "tool_name": app.name,
            "status": result['status'],
            "content": result['content'],
            "isError": result['status'] != 'success'
        }

        if result.get('error'):
            response_data['error'] = result['error']
        if result.get('usage'):
            response_data['usage'] = result['usage']
        if result.get('latency_ms'):
            response_data['latency_ms'] = result['latency_ms']

        status_code = status.HTTP_200_OK if result['status'] == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response_data, status=status_code)

    @action(detail=True, methods=['post'], url_path='toggle-featured')
    def toggle_featured(self, request, pk=None):
        """
        切换应用的精选状态
        """
        app = self.get_object()
        app.is_featured = not app.is_featured
        app.save(update_fields=['is_featured', 'updated_at'])

        return Response({
            "status": "success",
            "message": f"应用已{'设为精选' if app.is_featured else '取消精选'}",
            "is_featured": app.is_featured
        })


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
        provider_id = request.data.get('provider_id')
        if not provider_id:
            return Response({"error": "必须提供 provider_id 参数"}, status=status.HTTP_400_BAD_REQUEST)

        try:
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

        # 流式响应生成器
        def retry_stream_generator():
            assistant_content = ""
            reasoning_content = ""
            token_usage_data = None
            buffer = ""

            with httpx.stream(
                    "POST",
                    f"{provider.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)

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

                    # 直接 yield 原始行
                    if line:
                        yield line + '\n'

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
            if "gpt" not in model_name.lower():
                payload['extra_body'] = {"enable_thinking": enable_thinking}

        # 流式响应生成器
        def stream_generator():
            assistant_content = ""
            reasoning_content = ""  # 存储思考内容
            token_usage_data = None  # 存储 token 统计

            with httpx.stream(
                    "POST",
                    f"{provider.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)

                            # 解析 delta 内容
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})

                                # 获取思考内容
                                if 'reasoning_content' in delta:
                                    reasoning_content += delta['reasoning_content'] if delta[
                                        'reasoning_content'] else ''

                                # 获取最终回答
                                if 'content' in delta:
                                    assistant_content += delta['content'] if delta['content'] else ''

                            # 解析 token 使用量
                            if 'usage' in data:
                                token_usage_data = data['usage']

                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

                    # 直接 yield 原始行
                    if line:
                        yield line + '\n'

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

        response_stream = StreamingHttpResponse(
            stream_generator(),
            content_type='text/event-stream'
        )
        response_stream['Cache-Control'] = 'no-cache'
        response_stream['X-Accel-Buffering'] = 'no'
        return response_stream


class AppScenarioViewSet(viewsets.ModelViewSet):
    """
    应用场景视图集
    提供应用场景的 CRUD 操作
    """
    queryset = AppScenario.objects.all().order_by('-updated_at')
    serializer_class = AppScenarioSerializer

    def get_queryset(self):
        """
        支持按 app_id 筛选
        """
        queryset = super().get_queryset()
        app_id = self.request.query_params.get('app_id')
        if app_id:
            queryset = queryset.filter(app_id=app_id)
        return queryset


class TTSSynthesisViewSet(viewsets.ModelViewSet):
    """
    TTS 语音合成视图集
    提供基于存储的语音配置进行文本转语音的功能
    """
    queryset = TTSVoice.objects.all()
    serializer_class = TTSVoiceSerializer

    class TTSSynthesisRequestSerializer(serializers.Serializer):
        """
        TTS 合成请求序列化器
        """
        text = serializers.CharField(required=True, help_text="要转换的文本")
        sample_rate = serializers.IntegerField(default=24000, help_text="音频采样率")

    @action(detail=True, methods=['post'], url_path='invoke')
    def invoke_execute(self, request, pk=None):
        """
        [POST] API 直接调用执行接口

        执行 TTS 语音合成并返回结果
        speaker 通过 pk 传入
        """
        voice = self.get_object()

        # 验证请求数据
        serializer = self.TTSSynthesisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        text = data['text']
        sample_rate = data['sample_rate']

        try:
            # 构建请求头和 payload
            headers = {
                "Content-Type": "application/json",
                "X-Api-App-Id": voice.app_id,
                "X-Api-Access-Key": voice.access_key,
                "X-Api-Resource-Id": voice.resource_id,
            }

            payload = {
                "req_params": {
                    "speaker": voice.speaker,
                    "text": text,
                    "audio_params": {
                        "format": "wav",
                        "sample_rate": sample_rate,
                    }
                }
            }

            # 调用 TTS 服务
            audio_base64_list = []
            with httpx.stream(
                    "POST",
                    voice.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if "data" in chunk_data:
                                audio_data = chunk_data["data"]
                                if audio_data:
                                    audio_base64_list.append(audio_data)
                        except json.JSONDecodeError:
                            continue

            # 合并音频数据
            if not audio_base64_list:
                return Response({
                    "status": "error",
                    "error": "TTS 服务返回空数据"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            audio_bytes = b"".join([base64.b64decode(chunk) for chunk in audio_base64_list])
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            return Response({
                "status": "success",
                "audio": audio_b64,
                "speaker": voice.speaker
            })

        except httpx.HTTPStatusError as e:
            return Response({
                "status": "error",
                "error": f"调用 TTS 服务失败: {str(e)}"
            }, status=status.HTTP_502_BAD_GATEWAY)
        except httpx.RequestError as e:
            return Response({
                "status": "error",
                "error": f"请求错误: {str(e)}"
            }, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({
                "status": "error",
                "error": f"TTS 合成失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
