"""
Backend API 服务

统一的 Backend API 调用封装，提供通用的 App 调用接口。
所有与 Django Backend 的 HTTP 通信都应通过此服务进行。

API 协议参考 (AppViewSet.invoke_execute):
    - 端点: POST /api/apps/{app_id}/invoke/
    - 请求格式: {"message": "...", "context": [...], "parameters": {...}}
    - 响应格式: {"status": "success/error", "content": "...", "usage": {...}, "error": "..."}

流式 API 协议 (AppViewSet.invoke_stream):
    - 端点: POST /api/apps/{app_id}/invoke/stream/
    - 请求格式: 同上
    - 响应格式: SSE 流式，每个 chunk 格式:
      data: {"id":"...", "object":"chat.completion.chunk", "choices":[{"delta":{"content":"..."}}]}

使用示例:
    from app.services import BackendService

    backend = BackendService()

    # 调用任意 App
    result = await backend.invoke_app(
        app_id="your-app-id",
        message="用户输入",
        context=[{"role": "user", "content": "历史消息"}],
        parameters={"key": "value"}
    )

    if result.success:
        print(f"返回内容: {result.content}")
    else:
        print(f"调用失败: {result.error}")

    # 流式调用 App
    async for chunk in backend.invoke_app_stream(app_id="your-app-id", message="用户输入"):
        if chunk.content:
            print(chunk.content, end="", flush=True)
        if chunk.is_done:
            print("\n完成")
"""
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AppInvokeResult:
    """
    App 调用结果

    统一的返回结构，无论成功或失败都返回此对象。

    Attributes:
        success: 调用是否成功
        content: 返回的内容文本
        error: 错误信息（如果失败）
        usage: Token 使用统计
        latency_ms: 调用耗时（毫秒）
        raw_response: 原始响应数据
    """
    success: bool
    content: str = ""
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """支持直接用于 if 判断"""
        return self.success

    def __str__(self) -> str:
        """字符串表示"""
        if self.success:
            return self.content
        return f"[Error: {self.error}]"


@dataclass
class StreamChunk:
    """
    流式响应的单个 chunk

    用于表示 SSE 流式响应中的每个数据块。

    Attributes:
        content: 本次 chunk 的文本内容（增量）
        reasoning_content: 思考内容（如支持）
        is_done: 是否为结束标记 [DONE]
        is_error: 是否为错误
        error: 错误信息（如果 is_error=True）
        usage: Token 使用统计（通常在最后一个 chunk 中）
        raw_data: 原始响应数据
    """
    content: str = ""
    reasoning_content: Optional[str] = None
    is_done: bool = False
    is_error: bool = False
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """支持直接用于 if 判断是否有内容"""
        return bool(self.content) or bool(self.reasoning_content)


class BackendService:
    """
    Backend API 服务

    提供统一的 Backend API 调用接口，封装了 HTTP 请求细节和错误处理。

    主要功能:
        - invoke_app: 通用的 App 调用方法，返回完整结果
        - invoke_app_stream: 流式调用方法，实时返回结果

    Attributes:
        backend_url: Backend API 基础 URL
        default_timeout: 默认超时时间（秒）
    """

    def __init__(
            self,
            backend_url: Optional[str] = None,
            timeout: Optional[float] = None
    ):
        """
        初始化 Backend 服务

        Args:
            backend_url: Backend API URL，默认使用 settings.backend_api_url
            timeout: 默认超时时间（秒），默认使用 settings.asr_timeout
        """
        self.backend_url = backend_url or settings.backend_api_url
        self.default_timeout = timeout or settings.asr_timeout

    async def invoke_app(
            self,
            app_id: str,
            message: Optional[str] = None,
            context: Optional[List[Dict[str, str]]] = None,
            parameters: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None
    ) -> AppInvokeResult:
        """
        调用 Backend App 执行接口

        这是调用任何 App 的统一入口，适用于所有类型的 App。
        特定 App 的便捷方法应在各自的 *service.py 中实现。

        API 端点: POST /api/apps/{app_id}/invoke/

        请求格式:
            {
                "message": "string (可选) - 用户输入消息",
                "context": [{"role": "user|assistant", "content": "..."}] (可选) - 历史上下文,
                "parameters": {"key": "value"} (可选) - Function Calling 参数
            }

        响应格式:
            {
                "request_id": "string - 请求唯一标识",
                "app_id": "string - 应用 ID",
                "app_name": "string - 应用名称",
                "status": "success|error - 执行状态",
                "content": "string - 执行结果内容",
                "usage": {"prompt_tokens": N, "completion_tokens": M} (可选),
                "latency_ms": "integer - 执行耗时",
                "error": "string (可选) - 错误信息"
            }

        Args:
            app_id: 要调用的 App ID
            message: 用户输入的消息内容
            context: 历史消息上下文，格式为 [{'role': 'user|assistant', 'content': '...'}]
            parameters: Function Calling 参数，具体格式取决于 App 定义
            timeout: 请求超时时间（秒），None 则使用默认值

        Returns:
            AppInvokeResult: 统一的结果对象
                - success=True 时，content 包含返回内容
                - success=False 时，error 包含错误信息
        """
        url = f"{self.backend_url}/api/apps/{app_id}/invoke/"
        request_timeout = timeout or self.default_timeout

        # 构建请求 payload
        payload = {
            "message": message or "",
            "context": context or [],
            "parameters": parameters or {}
        }

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                # 使用 INFO 级别日志，便于追踪非流式调用
                logger.info(f"[NON-STREAM] Invoking Backend App: {app_id}")
                logger.info(f"[NON-STREAM] URL: {url}")
                logger.debug(f"Payload keys: {list(payload.keys())}")

                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                return self._parse_invoke_response(data)

        except httpx.TimeoutException:
            error_msg = f"Backend API timeout after {request_timeout}s"
            logger.error(error_msg)
            return AppInvokeResult(
                success=False,
                error=error_msg
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Backend API HTTP error: {e.response.status_code}"
            logger.error(f"{error_msg} - {e.response.text}")
            return AppInvokeResult(
                success=False,
                error=error_msg,
                raw_response={"status_code": e.response.status_code, "body": e.response.text}
            )

        except Exception as e:
            error_msg = f"Backend API call failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return AppInvokeResult(
                success=False,
                error=error_msg
            )

    async def invoke_app_stream(
            self,
            app_id: str,
            message: Optional[str] = None,
            context: Optional[List[Dict[str, str]]] = None,
            parameters: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式调用 Backend App 执行接口

        通过 SSE 流式返回结果，适用于需要实时输出的场景。

        API 端点: POST /api/apps/{app_id}/invoke/stream/

        请求格式:
            {
                "message": "string (可选) - 用户输入消息",
                "context": [{"role": "user|assistant", "content": "..."}] (可选) - 历史上下文,
                "parameters": {"key": "value"} (可选) - Function Calling 参数
            }

        响应格式 (SSE):
            data: {"id":"...", "object":"chat.completion.chunk", "choices":[{"delta":{"content":"..."}}]}
            data: [DONE]

        Args:
            app_id: 要调用的 App ID
            message: 用户输入的消息内容
            context: 历史消息上下文
            parameters: Function Calling 参数
            timeout: 请求超时时间（秒）

        Yields:
            StreamChunk: 流式响应的每个 chunk
        """
        url = f"{self.backend_url}/api/apps/{app_id}/invoke/stream/"
        request_timeout = timeout or self.default_timeout

        payload = {
            "message": message or "",
            "context": context or [],
            "parameters": parameters or {}
        }

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                # 使用 INFO 级别日志，便于追踪流式调用
                logger.info(f"[STREAM] Invoking Backend App: {app_id}")
                logger.info(f"[STREAM] URL: {url}")

                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        chunk = self._parse_stream_line(line)
                        if chunk:
                            yield chunk

                            # 如果是结束或错误，终止迭代
                            if chunk.is_done or chunk.is_error:
                                return

        except httpx.TimeoutException:
            error_msg = f"Backend API stream timeout after {request_timeout}s"
            logger.error(error_msg)
            yield StreamChunk(is_error=True, error=error_msg)

        except httpx.HTTPStatusError as e:
            error_msg = f"Backend API HTTP error: {e.response.status_code}"
            logger.error(f"{error_msg} - {await e.response.aread()}")
            yield StreamChunk(is_error=True, error=error_msg)

        except Exception as e:
            error_msg = f"Backend API stream failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield StreamChunk(is_error=True, error=error_msg)

    def _parse_stream_line(self, line: str) -> Optional[StreamChunk]:
        """
        解析 SSE 流式响应的单行

        Args:
            line: SSE 格式的单行数据，如 "data: {...}" 或 "data: [DONE]"

        Returns:
            StreamChunk 对象，如果行无法解析则返回 None
        """
        # SSE 格式：以 "data: " 开头
        if not line.startswith("data: "):
            return None

        data_str = line[6:]  # 去掉 "data: " 前缀

        # 检查是否为结束标记
        if data_str == "[DONE]":
            return StreamChunk(is_done=True)

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse SSE data: {data_str}")
            return None

        # 检查是否为错误响应
        if "error" in data and "status" in data:
            # 错误格式: {"status": "error", "error": "..."}
            return StreamChunk(
                is_error=True,
                error=data.get("error", "Unknown error"),
                raw_data=data
            )

        # 解析标准 OpenAI 格式的 chunk
        # 格式: {"choices": [{"delta": {"content": "..."}}], "usage": {...}}
        content = ""
        reasoning_content = None
        usage = None

        choices = data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            content = delta.get("content", "") or ""
            reasoning_content = delta.get("reasoning_content")

        # usage 通常在最后一个 chunk 中
        if "usage" in data:
            usage = data["usage"]

        return StreamChunk(
            content=content,
            reasoning_content=reasoning_content,
            usage=usage,
            raw_data=data
        )

    async def get_device_protocol(self, protocol_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备协议详情

        API 端点: GET /api/agentic-test/device-protocols/{protocol_id}/

        Args:
            protocol_id: 设备协议 ID

        Returns:
            协议详情字典，如果失败返回 None
        """
        url = f"{self.backend_url}/api/agentic-test/device-protocols/{protocol_id}/"
        request_timeout = self.default_timeout

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                logger.debug(f"Fetching device protocol: {protocol_id}")
                logger.debug(f"URL: {url}")

                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Successfully fetched device protocol: {protocol_id}")
                return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Device protocol not found: {protocol_id}")
            else:
                logger.error(f"Failed to fetch device protocol: {e.response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch device protocol: {e}", exc_info=True)
            return None

    def _parse_invoke_response(self, data: Dict[str, Any]) -> AppInvokeResult:
        """
        解析 invoke API 响应

        Args:
            data: API 返回的 JSON 数据

        Returns:
            AppInvokeResult: 统一的结果对象
        """
        status = data.get("status", "")
        content = data.get("content", "")
        error = data.get("error")
        usage = data.get("usage")
        latency_ms = data.get("latency_ms")

        if status == "success":
            logger.debug(f"Backend App invoke success: {len(content)} chars content")
            return AppInvokeResult(
                success=True,
                content=content,
                usage=usage,
                latency_ms=latency_ms,
                raw_response=data
            )
        else:
            error_msg = error or "Unknown error"
            logger.error(f"Backend App invoke failed: {error_msg}")
            return AppInvokeResult(
                success=False,
                content=content,
                error=error_msg,
                usage=usage,
                latency_ms=latency_ms,
                raw_response=data
            )


# ============================================================================
# 全局单例（可选使用）
# ============================================================================

_backend_service: Optional[BackendService] = None


def get_backend_service() -> BackendService:
    """
    获取全局 BackendService 单例

    使用单例可以复用连接池，提高性能。

    Returns:
        BackendService 实例
    """
    global _backend_service
    if _backend_service is None:
        _backend_service = BackendService()
    return _backend_service