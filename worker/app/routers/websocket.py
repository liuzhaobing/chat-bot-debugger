"""
WebSocket 路由
处理 WebSocket 连接和消息
"""
import asyncio
import json
import logging
import base64
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse

from app.websocket.manager import connection_manager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Agentic Test WebSocket ====================

@router.websocket("/ws/agentic-test/{session_id}")
async def agentic_test_websocket(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None, description="JWT Token")
):
    """
    Agentic Test WebSocket 连接端点

    Args:
        websocket: WebSocket 连接
        session_id: 会话ID
        token: JWT Token（用于认证）
    """
    # TODO: 实现 JWT 验证
    user_id = "dev_user"  # 临时：开发模式

    # 初始化状态
    audio_buffer = []
    audio_packet_count = 0
    agent = None
    iot_config = {}

    try:
        # 注册连接
        await connection_manager.connect(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
            metadata={"token": token, "agent": None, "iot_config": {}}
        )

        # 发送连接确认
        await connection_manager.send_message(
            session_id,
            {
                "type": "connection_status",
                "content": "WebSocket连接已建立",
                "metadata": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "waiting_for_iot_config": True
                }
            }
        )

        logger.info(f"WebSocket connected for session {session_id}")

        # 消息循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()

                # 更新心跳
                await connection_manager.update_heartbeat(session_id)

                # 获取连接信息
                conn_info = connection_manager.get_connection_info(session_id)
                if not conn_info:
                    logger.error(f"Connection not found: {session_id}")
                    break

                # 获取 agent 和状态
                agent = conn_info.metadata.get("agent")
                iot_config = conn_info.metadata.get("iot_config", {})

                # 处理消息
                message_type = data.get("type")
                logger.debug(f"Received message type: {message_type}")

                if message_type == "ping":
                    await connection_manager.send_message(
                        session_id,
                        {"type": "pong", "content": "pong"}
                    )

                elif message_type == "start_test":
                    query = data.get("query", "")
                    new_iot_config = data.get("iot_config", {})

                    # 更新配置
                    if new_iot_config:
                        iot_config.update(new_iot_config)
                        conn_info.metadata["iot_config"] = iot_config

                    # 创建 Agent
                    from app.services.agent_service import AgenticTestAgent

                    async def send_callback(msg_type: str, content, metadata=None):
                        """Agent 回调函数"""
                        await connection_manager.send_message(
                            session_id,
                            {
                                "type": msg_type,
                                "content": content,
                                "metadata": metadata or {}
                            }
                        )

                    agent = AgenticTestAgent(session_id, send_callback, iot_config)
                    conn_info.metadata["agent"] = agent

                    # 启动测试
                    asyncio.create_task(agent.start_loop(query, iot_config))

                    await connection_manager.send_message(
                        session_id,
                        {
                            "type": "status",
                            "content": "测试开始",
                            "metadata": {
                                "initial_query": query,
                                "iot_config": bool(iot_config)
                            }
                        }
                    )

                elif message_type == "stop_test":
                    if agent:
                        await agent.stop()

                    # 清空音频缓冲区
                    audio_buffer = []
                    audio_packet_count = 0

                    await connection_manager.send_message(
                        session_id,
                        {"type": "status", "content": "测试已停止"}
                    )

                elif message_type == "audio_data":
                    # 支持两种消息格式
                    audio_data = None
                    audio_format = 'webm'
                    is_complete = False

                    if 'data' in data and isinstance(data['data'], dict):
                        # 新格式
                        audio_data = data['data'].get('audio_data')
                        audio_format = data['data'].get('format', 'pcm')
                    else:
                        # 旧格式
                        audio_data = data.get('audio')
                        audio_format = data.get('format', 'webm')
                        is_complete = data.get('is_complete', False)

                    if not audio_data:
                        await connection_manager.send_message(
                            session_id,
                            {"type": "warning", "content": "音频数据为空"}
                        )
                        continue

                    if agent:
                        # 使用 Agent 处理音频
                        await agent.process_audio(audio_data, audio_format)
                    else:
                        # 没有 Agent，直接进行 VAD+ASR
                        await _process_audio_without_agent(
                            session_id, audio_data, audio_format,
                            audio_buffer, audio_packet_count
                        )

                elif message_type == "intervention":
                    message = data.get("message", "")
                    if agent and message:
                        await agent.handle_intervention(message)
                    else:
                        await connection_manager.send_message(
                            session_id,
                            {"type": "warning", "content": "智能体未运行或消息为空"}
                        )

                elif message_type == "update_iot_config":
                    config = data.get("config", {})
                    iot_config.update(config)
                    conn_info.metadata["iot_config"] = iot_config

                    if agent:
                        await agent.update_iot_config(config)

                    await connection_manager.send_message(
                        session_id,
                        {
                            "type": "status",
                            "content": "IOT配置已更新",
                            "metadata": {
                                "config": {
                                    "env": config.get("env", "test"),
                                    "has_token": bool(config.get("token")),
                                    "has_family_id": bool(config.get("familyId"))
                                }
                            }
                        }
                    )

                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await connection_manager.send_message(
                        session_id,
                        {
                            "type": "error",
                            "content": f"未知消息类型: {message_type}"
                        }
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                break

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await connection_manager.send_message(
                    session_id,
                    {"type": "error", "content": "JSON格式错误"}
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await connection_manager.send_message(
                    session_id,
                    {
                        "type": "error",
                        "content": f"消息处理错误: {str(e)}"
                    }
                )

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        # 停止 agent
        if agent:
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")

        # 注销连接
        await connection_manager.disconnect(session_id)


async def _process_audio_without_agent(
    session_id: str,
    audio_data: str,
    audio_format: str,
    audio_buffer: list,
    audio_packet_count: int
):
    """处理没有 Agent 时的音频数据"""
    from app.services.vad_service import VADService
    from app.services.asr_service import ASRService
    from app.utils.audio_utils import AudioConverter

    try:
        # 解码base64音频数据
        audio_bytes = base64.b64decode(audio_data)

        # PCM格式使用缓冲处理
        if audio_format == 'pcm':
            # 添加到缓冲区
            audio_buffer.append(audio_bytes)
            audio_packet_count += 1

            # 缓冲策略：累积3秒的音频数据再处理
            target_buffer_size = 96000  # 3秒 @ 16kHz, 16bit, mono
            combined_audio = b''.join(audio_buffer)

            if len(combined_audio) >= target_buffer_size:
                logger.info(f"Processing buffered audio: {len(combined_audio)} bytes")

                # VAD+ASR处理
                vad_service = VADService()
                asr_service = ASRService()

                # VAD检测
                audio_b64 = base64.b64encode(combined_audio).decode('utf-8')
                vad_result = await vad_service.detect_speech(audio_b64)

                # 发送VAD状态
                await connection_manager.send_message(
                    session_id,
                    {
                        "type": "vad_status",
                        "content": "detected" if vad_result.get('has_speech') else "no_speech",
                        "metadata": {
                            "has_speech": vad_result.get("has_speech", False),
                            "speech_ratio": vad_result.get("speech_ratio", 0.0),
                            "audio_duration_s": len(combined_audio) / 32000
                        }
                    }
                )

                # ASR识别
                if vad_result.get('has_speech'):
                    wav_audio_b64 = AudioConverter.pcm_to_wav_base64(combined_audio)
                    asr_result = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

                    await connection_manager.send_message(
                        session_id,
                        {
                            "type": "transcript_final",
                            "content": asr_result,
                            "metadata": {
                                "session_id": session_id,
                                "audio_duration_s": len(combined_audio) / 32000
                            }
                        }
                    )

                # 清空缓冲区
                audio_buffer.clear()
                audio_packet_count = 0
        else:
            # 其他格式直接处理
            vad_service = VADService()
            asr_service = ASRService()

            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            vad_result = await vad_service.detect_speech(audio_b64)

            if vad_result.get('has_speech'):
                wav_audio_b64 = AudioConverter.pcm_to_wav_base64(audio_bytes)
                asr_result = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

                await connection_manager.send_message(
                    session_id,
                    {
                        "type": "transcript_final",
                        "content": asr_result,
                        "metadata": {"session_id": session_id}
                    }
                )

    except Exception as e:
        logger.error(f"Error processing audio without agent: {e}")
        await connection_manager.send_message(
            session_id,
            {"type": "error", "content": f"音频处理失败: {str(e)}"}
        )


# ==================== VAD+ASR Test WebSocket ====================

async def _send_ws_message(websocket: WebSocket, message: dict) -> bool:
    """
    直接发送 WebSocket 消息的辅助函数

    Returns:
        bool: 发送是否成功
    """
    try:
        await websocket.send_json(message)
        return True
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {e}")
        return False


@router.websocket("/ws/agentic-test/vad-asr-test/")
async def vad_asr_test_websocket(
    websocket: WebSocket,
    app_id: Optional[str] = Query(None, description="App ID for ASR")
):
    """
    VAD+ASR 测试专用 WebSocket 端点

    这是一个独立的功能，不需要数据库 session，直接测试 VAD 和 ASR 服务。

    Args:
        websocket: WebSocket 连接
        app_id: ASR应用ID
    """
    # 使用默认 app_id
    actual_app_id = app_id or settings.asr_app_id

    # 初始化状态
    audio_buffer = []
    is_testing = False
    vad_service = None
    asr_service = None

    # 先接受连接
    await websocket.accept()
    logger.info(f"VAD+ASR test WebSocket accepted with app_id: {actual_app_id}")

    try:
        # 发送连接确认
        if not await _send_ws_message(websocket, {
            "type": "connection_status",
            "content": "VAD+ASR测试连接已建立",
            "metadata": {
                "app_id": actual_app_id
            }
        }):
            logger.error("Failed to send connection status, closing")
            return

        # 消息循环
        while True:
            try:
                # 使用 receive() 而不是 receive_json() 以正确处理断开消息
                message = await websocket.receive()

                # 检查是否是断开消息
                if message["type"] == "websocket.disconnect":
                    logger.info("Client disconnected")
                    break

                # 检查是否是文本消息
                if message["type"] != "websocket.receive":
                    logger.warning(f"Unexpected message type: {message['type']}")
                    continue

                # 解析 JSON 数据
                try:
                    data = json.loads(message.get("text", "{}"))
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await _send_ws_message(websocket, {
                        "type": "error",
                        "content": "JSON格式错误"
                    })
                    continue

                message_type = data.get("type")
                logger.debug(f"VAD+ASR test received message type: {message_type}")

                if message_type == "ping":
                    await _send_ws_message(websocket, {
                        "type": "pong",
                        "content": "pong"
                    })

                elif message_type == "start_test":
                    if is_testing:
                        await _send_ws_message(websocket, {
                            "type": "warning",
                            "content": "测试已在运行中"
                        })
                        continue

                    # 初始化 VAD 和 ASR 服务
                    from app.services.vad_service import VADService
                    from app.services.asr_service import ASRService

                    vad_service = VADService()
                    asr_service = ASRService()
                    is_testing = True
                    audio_buffer = []

                    logger.info(f"VAD+ASR services initialized: VAD level={vad_service.vad_level}")

                    await _send_ws_message(websocket, {
                        "type": "system_status",
                        "content": "VAD+ASR测试已启动",
                        "metadata": {
                            "app_id": actual_app_id,
                            "testing": True,
                            "vad_level": vad_service.vad_level if vad_service else 2
                        }
                    })

                elif message_type == "stop_test":
                    if not is_testing:
                        await _send_ws_message(websocket, {
                            "type": "warning",
                            "content": "测试未在运行"
                        })
                        continue

                    # 清理服务实例
                    is_testing = False
                    audio_buffer = []
                    vad_service = None
                    asr_service = None

                    await _send_ws_message(websocket, {
                        "type": "system_status",
                        "content": "VAD+ASR测试已停止",
                        "metadata": {
                            "app_id": actual_app_id,
                            "testing": False
                        }
                    })

                elif message_type == "set_vad_level":
                    level = data.get("level", 2)
                    try:
                        level = int(level)
                        if not (0 <= level <= 3):
                            await _send_ws_message(websocket, {
                                "type": "error",
                                "content": f"VAD级别必须在0-3之间，收到: {level}"
                            })
                            continue

                        if vad_service:
                            success = vad_service.set_vad_level(level)
                            if success:
                                descriptions = {
                                    0: "最不敏感 - 只检测非常明显的语音",
                                    1: "较不敏感 - 检测清晰的语音",
                                    2: "中等敏感 - 平衡检测（默认）",
                                    3: "最敏感 - 检测轻微的语音活动"
                                }
                                await _send_ws_message(websocket, {
                                    "type": "vad_config",
                                    "content": f"VAD敏感度已设置为 {level}",
                                    "metadata": {
                                        "level": level,
                                        "description": descriptions.get(level, "未知级别")
                                    }
                                })
                        else:
                            await _send_ws_message(websocket, {
                                "type": "warning",
                                "content": "VAD服务未初始化，请先启动测试"
                            })
                    except ValueError:
                        await _send_ws_message(websocket, {
                            "type": "error",
                            "content": f"无效的VAD级别: {level}"
                        })

                elif message_type == "audio_data":
                    if not is_testing or not vad_service:
                        await _send_ws_message(websocket, {
                            "type": "warning",
                            "content": "请先启动测试"
                        })
                        continue

                    # 解析音频数据
                    audio_data = None
                    audio_format = 'pcm'

                    if 'data' in data and isinstance(data['data'], dict):
                        audio_data = data['data'].get('audio_data')
                        audio_format = data['data'].get('format', 'pcm')
                    else:
                        audio_data = data.get('audio')
                        audio_format = data.get('format', 'webm')

                    if not audio_data:
                        await _send_ws_message(websocket, {
                            "type": "error",
                            "content": "音频数据为空"
                        })
                        continue

                    # 处理音频
                    await _process_vad_asr_audio_direct(
                        websocket, audio_data, audio_format,
                        audio_buffer, actual_app_id, vad_service, asr_service
                    )

                else:
                    logger.warning(f"Unknown VAD+ASR test message type: {message_type}")
                    await _send_ws_message(websocket, {
                        "type": "error",
                        "content": f"未知消息类型: {message_type}"
                    })

            except WebSocketDisconnect:
                logger.info("VAD+ASR test WebSocket disconnected")
                break

            except Exception as e:
                logger.error(f"Error in VAD+ASR test message processing: {e}", exc_info=True)
                # 尝试发送错误消息，如果失败则退出循环
                if not await _send_ws_message(websocket, {
                    "type": "error",
                    "content": f"消息处理错误: {str(e)}"
                }):
                    break

    except Exception as e:
        logger.error(f"VAD+ASR test WebSocket connection error: {e}", exc_info=True)

    finally:
        # 清理资源
        vad_service = None
        asr_service = None
        logger.info("VAD+ASR test resources cleaned up")


async def _process_vad_asr_audio_direct(
    websocket: WebSocket,
    audio_data: str,
    audio_format: str,
    audio_buffer: list,
    app_id: str,
    vad_service,
    asr_service
):
    """处理 VAD+ASR 测试的音频数据（直接使用 WebSocket）"""
    from app.utils.audio_utils import AudioConverter

    try:
        # 解码音频
        audio_bytes = base64.b64decode(audio_data)

        # PCM 格式使用缓冲处理
        if audio_format == 'pcm':
            audio_buffer.append(audio_bytes)

            # 缓冲策略：累积3秒音频
            target_buffer_size = 96000  # 3秒 @ 16kHz, 16bit, mono
            max_buffer_size = 192000  # 6秒
            combined_audio = b''.join(audio_buffer)

            logger.debug(f"Audio buffer: {len(combined_audio)} bytes, chunks: {len(audio_buffer)}")

            if len(combined_audio) >= target_buffer_size:
                logger.info(f"Processing audio chunk: {len(combined_audio)} bytes")

                # VAD 检测
                if vad_service:
                    audio_b64 = base64.b64encode(combined_audio).decode('utf-8')
                    vad_result = await vad_service.detect_speech(audio_b64)

                    # 发送 VAD 结果
                    await _send_ws_message(websocket, {
                        "type": "vad_status",
                        "content": "detected" if vad_result.get('has_speech') else "no_speech",
                        "metadata": {
                            "has_speech": vad_result.get("has_speech", False),
                            "confidence": vad_result.get("confidence", 0.0),
                            "speech_ratio": vad_result.get("speech_ratio", 0.0),
                            "audio_duration_s": len(combined_audio) / 32000
                        }
                    })

                    # ASR 识别
                    if vad_result.get('has_speech') and asr_service:
                        wav_audio_b64 = AudioConverter.pcm_to_wav_base64(combined_audio)
                        asr_result = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

                        await _send_ws_message(websocket, {
                            "type": "transcript_final",
                            "content": asr_result,
                            "metadata": {
                                "app_id": app_id,
                                "audio_duration_s": len(combined_audio) / 32000,
                                "vad_confidence": vad_result.get("confidence", 0.0)
                            }
                        })

                # 清空缓冲区
                audio_buffer.clear()

            elif len(combined_audio) > max_buffer_size:
                # 缓冲区过大，强制处理
                logger.warning(f"Buffer overflow, force processing")
                if vad_service:
                    audio_b64 = base64.b64encode(combined_audio).decode('utf-8')
                    vad_result = await vad_service.detect_speech(audio_b64)

                    if vad_result.get('has_speech') and asr_service:
                        wav_audio_b64 = AudioConverter.pcm_to_wav_base64(combined_audio)
                        asr_result = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

                        await _send_ws_message(websocket, {
                            "type": "transcript_final",
                            "content": asr_result,
                            "metadata": {"app_id": app_id}
                        })

                # 保留最后1.5秒数据
                keep_size = 48000
                audio_buffer.clear()
                audio_buffer.append(combined_audio[-keep_size:])

        else:
            # 其他格式直接处理
            if vad_service:
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                vad_result = await vad_service.detect_speech(audio_b64)

                await _send_ws_message(websocket, {
                    "type": "vad_status",
                    "content": "detected" if vad_result.get('has_speech') else "no_speech",
                    "metadata": {
                        "has_speech": vad_result.get("has_speech", False),
                        "audio_duration_s": len(audio_bytes) / 32000
                    }
                })

                if vad_result.get('has_speech') and asr_service:
                    wav_audio_b64 = AudioConverter.pcm_to_wav_base64(audio_bytes)
                    asr_result = await asr_service.recognize_speech(wav_audio_b64, audio_format="wav")

                    await _send_ws_message(websocket, {
                        "type": "transcript_final",
                        "content": asr_result,
                        "metadata": {"app_id": app_id}
                    })

    except Exception as e:
        logger.error(f"Error in VAD+ASR audio processing: {e}", exc_info=True)
        await _send_ws_message(websocket, {
            "type": "error",
            "content": f"音频处理失败: {str(e)}"
        })


# ==================== Stats Endpoint ====================

@router.get("/ws/stats")
async def websocket_stats():
    """获取 WebSocket 连接统计"""
    return connection_manager.get_stats()


__all__ = ["router"]