# -*- coding: utf-8 -*-
"""
DIAL客户端
用于与ROKI智能客服系统进行通话交互
"""
import json
import os
import time
import base64
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Union, Any


class DialClient:
    """
    DIAL客户端
    用于与ROKI智能客服系统进行通话交互
    """

    def __init__(
            self,
            address: str,
            consumer_id: str = "17744270115",
            logger: Optional[logging.LoggerAdapter] = logging.getLogger(__name__),
    ):
        """
        初始化DIAL客户端
        
        Args:
            address: DIAL服务地址
            consumer_id: 消费者ID
        """
        self.address = address.rstrip("/")
        self.consumer_id = consumer_id
        self.history_messages = []
        self.logger = logger

    @property
    def headers(self) -> Dict[str, str]:
        """请求头"""
        return {"Content-Type": "application/json"}

    def dialogue_start(
            self,
            session_id: str,
            phone_number: Optional[str] = None,
            call_connect_time: Optional[str] = None
    ) -> Tuple[bool, Union[Dict, str]]:
        """
        开始通话会话
        
        Args:
            session_id: 会话ID
            phone_number: 电话号码，默认使用consumer_id
            call_connect_time: 通话连接时间，默认使用当前时间
            
        Returns:
            (是否成功, 响应数据或错误信息)
        """
        try:
            url = f"{self.address}/v1/sip-call/dialogue-start"
            now_str = call_connect_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload = {
                "sessionId": session_id,
                "callConnectTime": now_str,
                "phoneNumber": phone_number or self.consumer_id
            }

            self.logger.info(f"dialogue_start request: {json.dumps(payload, ensure_ascii=False)}")

            start_time = time.perf_counter()
            response = requests.post(
                url=url,
                headers=self.headers,
                json=payload,
                timeout=10,
                verify=False,
            )
            end_time = time.perf_counter()
            cost = int(1000 * (end_time - start_time))

            response.raise_for_status()
            result = response.json()
            self.logger.info(f"dialogue_start success, cost: {cost}ms")
            return True, result

        except Exception as e:
            self.logger.error(f"dialogue_start failed: {e}")
            return False, str(e)

    def dialogue_end(
            self,
            session_id: str,
            call_duration: int,
            hangup_type: int = 1,
            call_hangup_time: Optional[str] = None
    ) -> Tuple[bool, Union[Dict, str]]:
        """
        结束通话会话
        
        Args:
            session_id: 会话ID
            call_duration: 通话时长（秒）
            hangup_type: 挂断类型，默认为1
            call_hangup_time: 挂断时间，默认使用当前时间
            
        Returns:
            (是否成功, 响应数据或错误信息)
        """
        try:
            url = f"{self.address}/v1/sip-call/dialogue-end"
            now_str = call_hangup_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload = {
                "sessionId": session_id,
                "callHangupTime": now_str,
                "callDuration": call_duration,
                "hangupType": hangup_type
            }

            self.logger.info(f"dialogue_end request: {json.dumps(payload, ensure_ascii=False)}")

            start_time = time.perf_counter()
            response = requests.post(
                url=url,
                headers=self.headers,
                json=payload,
                timeout=10,
                verify=False,
            )
            end_time = time.perf_counter()
            cost = int(1000 * (end_time - start_time))

            response.raise_for_status()
            result = response.json()
            self.logger.info(f"dialogue_end success, cost: {cost}ms")
            return True, result

        except Exception as e:
            self.logger.error(f"dialogue_end failed: {e}")
            return False, str(e)

    def completions_stream(
            self,
            session_id: str,
            index: int,
            query: str = "",
            user_audio: Optional[str] = None,
            no_response: bool = False,
            **kwargs
    ) -> Tuple[Dict[str, Any], List[int], Optional[Exception]]:
        """
        发送对话请求（流式）
        
        Args:
            session_id: 会话ID
            index: 消息索引
            query: 用户查询文本
            user_audio: 用户音频base64编码
            no_response: 是否为静默请求
            **kwargs: 其他参数
            
        Returns:
            (响应内容字典, 耗时列表, 异常)
        """
        payload = {
            "consumerId": kwargs.get("consumerId") or self.consumer_id,
            "sessionId": session_id,
            "query": query,
            "index": index,
            "stream": True,
            "noResponse": no_response
        }

        # 记录用户消息
        self.history_messages.append({
            "role": "user",
            "content": query,
            "timestamp": int(time.time() * 1000)
        })

        if not no_response and user_audio:
            payload["userInput"] = {"user_audio": user_audio}

        # 添加额外参数
        if trace_id := kwargs.get("traceId"):
            payload["traceId"] = trace_id

        try:
            url = f"{self.address}/v1/sip-call/completions"
            self.logger.info(f"completions_stream request: {json.dumps(payload, ensure_ascii=False)}")

            start_time = time.perf_counter()
            response = requests.post(
                url=url,
                headers=self.headers,
                json=payload,
                timeout=60,
                stream=True,
                verify=False,
            )
            end_time = time.perf_counter()
            cost = int(1000 * (end_time - start_time))

            response.raise_for_status()

            # 解析流式响应
            response_content = []
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    response_content.append(chunk)

            result = self._parse_stream_content(response_content)

            # 记录助手消息
            if not no_response and query and result.get("answer"):
                content = result["answer"]
                metadata = result.get("metadata", {})
                self.history_messages.append({
                    "role": "assistant",
                    "content": content,
                    "timestamp": int(time.time() * 1000),
                    "metadata": metadata
                })

            return result, [cost], None

        except Exception as e:
            self.logger.error(f"completions_stream failed: {e}")
            return {}, [0], e

    def _parse_stream_content(self, response_content: List[bytes]) -> Dict[str, Any]:
        """
        解析流式响应内容
        
        Args:
            response_content: 响应内容列表
            
        Returns:
            解析后的响应字典
        """
        full_content = ""
        buffer = ""
        result = {
            "answer": "",
            "metadata": {},
            "session_id": "",
        }

        try:
            for chunk in response_content:
                if not chunk:
                    continue

                # 将chunk解码并添加到buffer
                buffer += chunk.decode("utf-8")

                # 按行分割处理（SSE是按行传输的）
                lines = buffer.split("\n")

                # 保留最后一个可能不完整的行
                buffer = lines[-1]

                # 处理完整的行
                for line in lines[:-1]:
                    line = line.strip()
                    if not line:
                        continue

                    # 处理 data: 前缀
                    if line.startswith("data:"):
                        line = line[5:].strip()

                    # 跳过结束标记
                    if line == "[DONE]":
                        continue

                    # 尝试解析JSON
                    try:
                        data = json.loads(line)
                        if session_id := data.get("sessionId"):
                            result["session_id"] = session_id
                        if "choices" in data and len(data["choices"]) > 0:
                            message = data["choices"][0].get("message", {})
                            if content := message.get("content", ""):
                                full_content += content
                            if metadata := message.get("metadata", {}):
                                result["metadata"] = metadata
                    except Exception as parse_error:
                        self.logger.debug(f"parse json failed for line: {line[:100]}, error: {parse_error}")
                        continue

            # 处理buffer中剩余的数据
            if line := buffer.strip():
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line and line != "[DONE]":
                    try:
                        data = json.loads(line)
                        if session_id := data.get("sessionId"):
                            result["session_id"] = session_id
                        if "choices" in data and len(data["choices"]) > 0:
                            message = data["choices"][0].get("message", {})
                            if content := message.get("content", ""):
                                full_content += content
                            if metadata := message.get("metadata", {}):
                                result["metadata"] = metadata
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"parse stream content failed: {e}")

        result["answer"] = full_content
        return result


def generate_trace_id(prefix: str = "DIAL") -> str:
    """生成追踪ID"""

    def generate_job_instance_id(tp: str):
        now = datetime.now()
        return tp.upper() + now.strftime("%Y%m%d%H%M%S") + base64.b32encode(os.urandom(5)).decode("ascii")

    return generate_job_instance_id(prefix) + "_myroki_test_com"


def text_to_speech(text: str, sample_rate: int = 24000) -> str:
    """
    Args:
        text: 要转换的文本
        sample_rate: 采样率
    Returns:
        base64编码的音频数据
    """
    base_url = os.environ.get("TTS_BASE_URL")
    app_id = os.environ.get("TTS_APP_ID")
    access_key = os.environ.get("TTS_ACCESS_KEY")
    resource_id = os.environ.get("TTS_RESOURCE_ID")
    speaker = os.environ.get("TTS_SPEAKER")

    header = {
        "Content-Type": "application/json",
        "X-Api-App-Id": app_id,
        "X-Api-Access-Key": access_key,
        "X-Api-Resource-Id": resource_id,
    }
    payload = {
        "req_params": {
            "speaker": speaker,
            "text": text,
            "audio_params": {
                "format": "wav",
                "sample_rate": sample_rate,
            }
        }
    }
    response = requests.post(
        base_url,
        headers=header,
        json=payload,
        stream=True
    )

    # 检查响应状态
    response.raise_for_status()

    audio_base64_list = []
    for line in response.iter_lines():
        if line:
            try:
                # 解析每行JSON数据
                chunk_data = json.loads(line.decode("utf-8"))
                if "data" in chunk_data:
                    data = chunk_data["data"]
                    if data:
                        audio_base64_list.append(data)
            except json.JSONDecodeError:
                continue
    audio_bytes = b"".join([base64.b64decode(chunk) for chunk in audio_base64_list])
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return audio_b64
