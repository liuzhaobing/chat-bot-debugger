# Worker 微服务拆分架构设计文档

> 创建日期: 2026-03-11
> 状态: 设计阶段

## 目录

1. [当前架构概览](#一当前架构概览)
2. [拆分方案](#二拆分方案)
3. [详细拆分设计](#三详细拆分设计)
4. [服务间通信设计](#四服务间通信设计)
5. [数据类定义调整](#五数据类定义调整)
6. [HTTP API 接口定义](#六http-api-接口定义)
7. [消息队列通信协议](#七消息队列通信协议)
8. [代码迁移方案](#八代码迁移方案)
9. [错误处理和重试机制](#九错误处理和重试机制)
10. [服务监控和健康检查](#十服务监控和健康检查)
11. [测试用例](#十一测试用例)
12. [实施步骤](#十二实施步骤)

---

## 一、当前架构概览

### 1.1 现有架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Worker (FastAPI + WebSocket)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   VAD       │    │    ASR      │    │    TTS      │          │
│  │  Service    │    │  Service    │    │  Service    │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                      │
│  ┌─────────────────────────▼─────────────────────────┐          │
│  │            AgenticTestAgent                        │          │
│  │  ┌─────────────────┐  ┌─────────────────────────┐ │          │
│  │  │ 音频输入层       │  │ 云端大脑处理层           │ │          │
│  │  │ - audio_buffer  │  │ - process_brain         │ │          │
│  │  │ - VAD           │  │ - call_judge_app        │ │          │
│  │  │ - ASR           │  │ - generate_next_query   │ │          │
│  │  └─────────────────┘  └─────────────────────────┘ │          │
│  │  ┌─────────────────────────────────────────────┐   │          │
│  │  │ 音频输出层                                   │   │          │
│  │  │ - generate_and_play_audio (TTS)             │   │          │
│  │  └─────────────────────────────────────────────┘   │          │
│  └─────────────────────────────────────────────────────┘          │
│                            │                                      │
│                   WebSocket Router                                │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                      Browser (WebSocket)
```

### 1.2 核心文件

| 文件 | 职责 |
|------|------|
| `app/services/agent_service.py` | 核心业务逻辑，包含音频输入层、云端大脑处理层、音频输出层 |
| `app/services/vad_service.py` | 语音活动检测 |
| `app/services/asr_service.py` | 语音识别 |
| `app/services/tts_service.py` | 语音合成 |
| `app/services/backend_service.py` | Backend API 调用封装 |
| `app/services/iot_service.py` | IoT 设备状态管理 |
| `app/utils/audio_utils.py` | 音频处理工具（缓冲、转换） |
| `app/routers/websocket.py` | WebSocket 路由 |
| `app/websocket/manager.py` | WebSocket 连接管理 |

---

## 二、拆分方案

### 2.1 目标架构图

```
┌────────────────────────────────┐     ┌────────────────────────────────┐
│      Voice Service (语音处理)    │     │     Brain Service (文本处理)    │
├────────────────────────────────┤     ├────────────────────────────────┤
│                                │     │                                │
│  ┌──────────────────────────┐  │     │  ┌──────────────────────────┐  │
│  │   WebSocket Endpoint     │  │     │  │   HTTP/WS Endpoint       │  │
│  │   /ws/voice/{session_id} │  │     │  │   /api/brain/process     │  │
│  └────────────┬─────────────┘  │     │  └────────────┬─────────────┘  │
│               │                │     │               │                │
│  ┌────────────▼─────────────┐  │     │  ┌────────────▼─────────────┐  │
│  │   AudioBufferProcessor   │  │     │  │   BrainProcessor         │  │
│  │   (音频缓冲管理)          │  │     │  │   (NLP处理核心)          │  │
│  └────────────┬─────────────┘  │     │  └────────────┬─────────────┘  │
│               │                │     │               │                │
│  ┌────────────▼─────────────┐  │     │  ┌────────────▼─────────────┐  │
│  │   VADService             │  │     │  │   - process_brain        │  │
│  │   (语音活动检测)          │  │     │  │   - call_judge_app       │  │
│  └────────────┬─────────────┘  │     │  │   - generate_next_query  │  │
│               │                │     │  │   - conversation_manager │  │
│  ┌────────────▼─────────────┐  │     │  └──────────────────────────┘  │
│  │   ASRService             │  │     │                                │
│  │   (语音识别)              │  │     │  ┌──────────────────────────┐  │
│  └────────────┬─────────────┘  │     │  │   BackendService         │  │
│               │                │     │  │   (调用LLM Apps)          │  │
│  ┌────────────▼─────────────┐  │     │  └──────────────────────────┘  │
│  │   TTSService             │  │     │                                │
│  │   (语音合成)              │  │     │  ┌──────────────────────────┐  │
│  └────────────┬─────────────┘  │     │  │   IoTService             │  │
│               │                │     │  │   (设备状态管理)          │  │
│  └────────────┴──────────────┘  │     │  └──────────────────────────┘  │
│                                │     │                                │
│  输入: WebSocket音频流          │     │  输入: ASR文本                │
│  输出: ASR文本 / TTS音频        │     │  输出: 处理后的文本/指令      │
│                                │     │                                │
└────────────────────────────────┘     └────────────────────────────────┘
         │                                          ▲
         │          ASR Text (消息队列/HTTP)        │
         └──────────────────────────────────────────┘
```

### 2.2 服务职责划分

#### Voice Service (语音处理服务)

| 职责 | 描述 |
|------|------|
| WebSocket 连接管理 | 接收浏览器音频流，发送音频和状态消息 |
| 音频缓冲 | 累积音频数据，达到阈值后处理 |
| VAD | 语音活动检测，判断是否有语音 |
| ASR | 语音转文字 |
| TTS | 文字转语音，返回音频流 |

#### Brain Service (文本处理服务)

| 职责 | 描述 |
|------|------|
| NLP处理 | 调用大模型处理文本 |
| 测试循环逻辑 | 管理测试步骤和状态 |
| 对话历史管理 | 维护多轮对话上下文 |
| 设备状态管理 | IoT设备状态查询和变更检测 |
| App调用 | 调用Judge App和Query Generator App |

---

## 三、详细拆分设计

### 3.1 Voice Service 目录结构

```
voice-service/
├── app/
│   ├── main.py                    # FastAPI入口
│   ├── config.py                  # 配置
│   ├── routers/
│   │   ├── websocket.py           # WebSocket路由
│   │   └── monitoring.py          # 监控路由
│   ├── services/
│   │   ├── vad_service.py         # VAD服务
│   │   ├── asr_service.py         # ASR服务
│   │   ├── tts_service.py         # TTS服务
│   │   ├── audio_processor.py     # 音频处理服务
│   │   └── brain_client.py        # Brain Service客户端
│   ├── utils/
│   │   └── audio_utils.py         # 音频工具
│   ├── websocket/
│   │   └── manager.py             # WebSocket管理器
│   ├── schemas/
│   │   └── audio.py               # 音频相关Schema
│   ├── core/
│   │   ├── database.py            # 数据库
│   │   ├── redis.py               # Redis
│   │   └── logging.py             # 日志
│   └── models/
│       └── session.py             # 会话模型
├── common/
│   ├── errors.py                  # 错误定义
│   ├── retry.py                   # 重试机制
│   └── health.py                  # 健康检查
├── tests/
│   ├── test_vad_service.py
│   ├── test_asr_service.py
│   ├── test_tts_service.py
│   └── test_brain_client.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

### 3.2 Brain Service 目录结构

```
brain-service/
├── app/
│   ├── main.py                    # FastAPI入口
│   ├── config.py                  # 配置
│   ├── routers/
│   │   ├── brain.py               # Brain处理API
│   │   ├── session.py             # 会话管理API
│   │   └── monitoring.py          # 监控路由
│   ├── services/
│   │   ├── brain_service.py       # 核心处理逻辑
│   │   ├── backend_service.py     # Backend API调用
│   │   ├── iot_service.py         # IoT服务
│   │   └── conversation_manager.py # 对话历史管理
│   ├── models/
│   │   ├── session.py             # 会话模型
│   │   └── device.py              # 设备状态模型
│   ├── schemas/
│   │   └── brain.py               # 请求/响应Schema
│   ├── core/
│   │   ├── database.py
│   │   ├── redis.py
│   │   └── logging.py
│   └── utils/
│       └── helpers.py             # 辅助函数
├── common/
│   ├── errors.py
│   ├── retry.py
│   └── health.py
├── tests/
│   ├── test_brain_service.py
│   ├── test_api.py
│   └── test_iot_service.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

### 3.3 关键代码位置对照表

| 功能 | 原位置 (agent_service.py) | 拆分后位置 |
|------|---------------------------|------------|
| 音频缓冲 | `AudioBufferProcessor` (audio_utils.py) | Voice Service |
| VAD检测 | `perform_vad_and_asr()` L330-419 | Voice Service |
| ASR识别 | `ASRService` (asr_service.py) | Voice Service |
| TTS生成 | `generate_and_play_audio()` L566-629 | Voice Service |
| NLP处理 | `process_brain()` L427-534 | Brain Service |
| Judge App | `call_judge_app()` L812-868 | Brain Service |
| Query生成 | `call_query_generator_app()` L870-913 | Brain Service |
| 对话历史 | `_add_to_conversation_history()` L999-1021 | Brain Service |
| 设备状态 | `update_device_status()` L758-793 | Brain Service |
| IoT服务 | `IOTService` (iot_service.py) | Brain Service |

---

## 四、服务间通信设计

### 4.1 方案 A: HTTP REST API (推荐用于初始拆分)

```
Voice Service                          Brain Service
     │                                      │
     │  POST /api/brain/process             │
     │  {                                   │
     │    "session_id": "xxx",              │
     │    "asr_text": "打开油烟机",          │
     │    "context": {...}                  │
     │  }                                   │
     │ ─────────────────────────────────────►│
     │                                      │
     │  Response:                           │
     │  {                                   │
     │    "success": true,                  │
     │    "next_query": "已为您打开油烟机",  │
     │    "should_continue": true,          │
     │    "tts_text": "好的，已为您打开"     │
     │  }                                   │
     │ ◄─────────────────────────────────────│
     │                                      │
```

### 4.2 方案 B: 消息队列 (推荐用于高并发场景)

```
                    Redis / RabbitMQ
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    │                    ▼
Voice Service       [asr_text_queue]    Brain Service
    │                    │                    │
    │  publish asr_text  │                    │
    │ ──────────────────►│                    │
    │                    │  consume           │
    │                    │───────────────────►│
    │                    │                    │ process
    │                    │  publish tts_text  │
    │                    │◄───────────────────│
    │  consume tts_text  │                    │
    │◄───────────────────│                    │
    ▼                                         │
  TTS播放                                     │
```

---

## 五、数据类定义调整

### 5.1 Voice Service 数据类

```python
# voice_service/app/schemas/audio.py

@dataclass
class AudioInputResult:
    """音频输入处理结果"""
    success: bool
    audio_bytes: Optional[bytes] = None
    audio_duration_s: float = 0.0
    error_message: Optional[str] = None


@dataclass
class VADASRResult:
    """VAD和ASR处理结果"""
    success: bool
    has_speech: bool = False
    asr_text: str = ""
    speech_ratio: float = 0.0
    confidence: float = 0.8
    error_message: Optional[str] = None


@dataclass
class AudioOutputResult:
    """音频输出处理结果"""
    success: bool
    audio_data: Optional[bytes] = None
    text: str = ""
    error_message: Optional[str] = None
```

### 5.2 Brain Service 数据类

```python
# brain_service/app/schemas/brain.py

@dataclass
class BrainProcessRequest:
    """Brain处理请求"""
    session_id: str
    asr_text: str
    loop_step: int = 0
    iot_config: Optional[Dict[str, str]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


@dataclass
class BrainProcessResult:
    """Brain处理结果"""
    success: bool
    next_query: str = ""
    should_continue: bool = True
    ai_response: str = ""
    tts_text: str = ""  # 用于TTS播放的文本
    analysis: Optional[Dict[str, Any]] = None
    error: Optional['ServiceError'] = None
```

---

## 六、HTTP API 接口定义

### 6.1 Brain Service API

#### 处理ASR文本

```
POST /api/brain/process
```

**Request:**
```json
{
  "session_id": "string",
  "asr_text": "打开油烟机",
  "loop_step": 1,
  "iot_config": {
    "token": "xxx",
    "familyId": "xxx",
    "env": "test"
  },
  "conversation_history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，有什么可以帮您？"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "next_query": "已为您打开油烟机",
  "should_continue": true,
  "ai_response": "好的，正在为您打开油烟机",
  "tts_text": "好的，已为您打开油烟机",
  "analysis": {
    "intent": "device_control",
    "target_device": "油烟机",
    "action": "turn_on"
  }
}
```

#### 会话管理

```
POST /api/brain/session/{session_id}/start
```

**Request:**
```json
{
  "initial_query": "测试油烟机控制",
  "iot_config": {
    "token": "xxx",
    "familyId": "xxx",
    "env": "test"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "xxx",
  "message": "会话已启动"
}
```

```
POST /api/brain/session/{session_id}/stop
GET /api/brain/session/{session_id}
DELETE /api/brain/session/{session_id}
```

#### 人工干预

```
POST /api/brain/session/{session_id}/intervention
```

**Request:**
```json
{
  "message": "停止测试"
}
```

**Response:**
```json
{
  "success": true,
  "should_continue": false,
  "tts_text": "好的，测试已停止"
}
```

#### IoT配置更新

```
PUT /api/brain/session/{session_id}/iot-config
```

**Request:**
```json
{
  "token": "new_token",
  "familyId": "new_family_id",
  "env": "prod"
}
```

### 6.2 Voice Service WebSocket 消息类型

#### 客户端 -> 服务端

| 类型 | 描述 | 参数 |
|------|------|------|
| `start_test` | 启动测试 | `query`, `iot_config` |
| `stop_test` | 停止测试 | - |
| `audio_data` | 音频数据 | `audio` (base64), `format` |
| `intervention` | 人工干预 | `message` |
| `update_iot_config` | 更新IoT配置 | `config` |
| `ping` | 心跳 | - |

#### 服务端 -> 客户端

| 类型 | 描述 | 参数 |
|------|------|------|
| `connection_status` | 连接状态 | `session_id`, `user_id` |
| `status` | 状态更新 | `content` |
| `vad_status` | VAD结果 | `has_speech`, `speech_ratio` |
| `transcript_final` | ASR识别结果 | `content` |
| `audio_play` | TTS音频 | `audio` (base64) |
| `ai_response` | AI响应 | `content` |
| `error` | 错误 | `content` |
| `pong` | 心跳响应 | - |

---

## 七、消息队列通信协议

### 7.1 Redis 消息格式

#### ASR文本消息 (Voice -> Brain)

```json
{
  "message_id": "uuid",
  "timestamp": 1709876543.123,
  "session_id": "session_uuid",
  "type": "asr_text",
  "payload": {
    "asr_text": "打开油烟机",
    "loop_step": 1,
    "confidence": 0.95,
    "audio_duration_s": 2.5
  },
  "metadata": {
    "iot_config": {
      "token": "xxx",
      "familyId": "xxx",
      "env": "test"
    }
  }
}
```

#### TTS文本消息 (Brain -> Voice)

```json
{
  "message_id": "uuid",
  "timestamp": 1709876544.456,
  "session_id": "session_uuid",
  "type": "tts_text",
  "payload": {
    "tts_text": "好的，已为您打开油烟机",
    "should_continue": true,
    "next_query": "已为您打开油烟机"
  },
  "metadata": {
    "intent": "device_control",
    "target_device": "油烟机"
  }
}
```

### 7.2 队列命名规范

| 队列名 | 方向 | 描述 |
|--------|------|------|
| `voice:asr:{session_id}` | Voice -> Brain | ASR识别结果 |
| `brain:tts:{session_id}` | Brain -> Voice | TTS文本和指令 |
| `voice:events:{session_id}` | Voice -> Brain | 事件通知 |
| `brain:commands:{session_id}` | Brain -> Voice | 控制命令 |

### 7.3 消息确认机制

```python
# 发布消息
await redis.xadd(
    f"voice:asr:{session_id}",
    {
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "asr_text": asr_text,
        # ...
    }
)

# 消费消息（带确认）
async def consume_messages(session_id: str):
    group_name = f"brain_consumer_{session_id}"
    await redis.xgroup_create(
        f"voice:asr:{session_id}",
        group_name,
        id="0",
        mkstream=True
    )

    while True:
        messages = await redis.xreadgroup(
            group_name,
            "consumer_1",
            {f"voice:asr:{session_id}": ">"},
            count=1,
            block=5000
        )

        for stream, msgs in messages:
            for msg_id, data in msgs:
                try:
                    await process_message(data)
                    await redis.xack(
                        f"voice:asr:{session_id}",
                        group_name,
                        msg_id
                    )
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
```

---

## 八、代码迁移方案

### 8.1 第一阶段：接口抽象

#### 创建共享 Schema

```python
# common/schemas.py

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class BrainProcessRequest(BaseModel):
    session_id: str
    asr_text: str
    loop_step: int = 0
    iot_config: Optional[Dict[str, str]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class BrainProcessResponse(BaseModel):
    success: bool
    next_query: str = ""
    should_continue: bool = True
    ai_response: str = ""
    tts_text: str = ""
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 8.2 第二阶段：Voice Service 抽取

#### VoiceAgent 类设计

```python
# voice-service/app/services/voice_agent_service.py

class VoiceAgent:
    """Voice Agent - 管理音频处理流程"""

    def __init__(
        self,
        session_id: str,
        send_callback: Callable,
        iot_config: Optional[Dict[str, str]] = None
    ):
        self.session_id = session_id
        self.send_callback = send_callback
        self.is_running = False

        # 初始化服务
        self.vad_service = VADService()
        self.asr_service = ASRService()
        self.tts_service = TTSService()
        self.brain_client = BrainServiceClient()

        # 音频缓冲
        self.audio_buffer = AudioBufferProcessor()

    async def start_loop(self, initial_query: str, iot_config: Dict):
        """启动循环"""
        self.is_running = True

        # 通知 Brain Service 启动会话
        await self.brain_client.start_session(
            self.session_id, initial_query, iot_config
        )

        # 执行初始TTS
        await self.generate_and_play_audio(initial_query)

        while self.is_running:
            # 等待音频输入
            await self._wait_for_audio_input()

    async def process_audio(self, audio_data: str, audio_format: str):
        """处理音频输入"""
        # 1. 音频缓冲
        input_result = await self._process_audio_buffer(audio_data, audio_format)
        if not input_result.audio_bytes:
            return

        # 2. VAD检测
        vad_result = await self.vad_service.detect_speech(
            base64.b64encode(input_result.audio_bytes).decode()
        )

        if not vad_result.get('has_speech'):
            return

        # 3. ASR识别
        wav_audio = AudioConverter.pcm_to_wav_base64(input_result.audio_bytes)
        asr_text = await self.asr_service.recognize_speech(wav_audio)

        # 4. 调用 Brain Service
        brain_result = await self.brain_client.process_asr_text(
            session_id=self.session_id,
            asr_text=asr_text
        )

        # 5. TTS播放
        if brain_result.success and brain_result.tts_text:
            await self.generate_and_play_audio(brain_result.tts_text)

    async def generate_and_play_audio(self, text: str):
        """生成并播放TTS音频"""
        audio_data = await self.tts_service.generate_speech(text)
        await self.send_callback('audio_play', audio_data, {'text': text})

    async def stop(self):
        """停止"""
        self.is_running = False
        await self.brain_client.stop_session(self.session_id)
```

### 8.3 第三阶段：Brain Service 抽取

#### BrainService 类设计

```python
# brain-service/app/services/brain_service.py

class BrainService:
    """Brain Service - 文本处理核心"""

    # App IDs
    JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"
    QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

    def __init__(self):
        self._sessions: Dict[str, SessionContext] = {}
        self.backend_service = BackendService()
        self.iot_service = IOTService()

    def get_or_create_session(self, session_id: str) -> SessionContext:
        """获取或创建会话"""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(session_id)
        return self._sessions[session_id]

    async def process_brain(
        self,
        session_id: str,
        asr_text: str,
        loop_step: int = 0,
        iot_config: Optional[Dict] = None
    ) -> Dict:
        """处理ASR文本"""
        ctx = self.get_or_create_session(session_id)
        ctx.loop_step = loop_step

        # 检查噪音或空输入
        if asr_text == '<noise>' or not asr_text.strip():
            return {
                'success': True,
                'should_continue': False,
                'tts_text': '请重新说话'
            }

        # 添加到对话历史
        ctx.add_to_history('user', asr_text)

        # 调用 Query Generator
        query_result = await self.call_query_generator_app(
            self._build_query_message(ctx, iot_config)
        )

        next_query = query_result.get('user_input', '')
        if next_query:
            ctx.add_to_history('assistant', next_query)

        return {
            'success': True,
            'next_query': next_query,
            'should_continue': query_result.get('should_continue', True),
            'tts_text': next_query
        }

    async def call_query_generator_app(self, message: str) -> Dict:
        """调用 Query Generator App"""
        result = await self.backend_service.invoke_app(
            app_id=self.QUERY_GENERATOR_APP_ID,
            message=message
        )

        if result.success:
            return json.loads(result.content)
        return self._get_mock_query_result()

    def _build_query_message(
        self,
        ctx: SessionContext,
        iot_config: Optional[Dict]
    ) -> str:
        """构建查询消息"""
        return f"""**对话历史**：
{ctx.get_history_context()}

**家庭设备列表**：
{iot_config or {}}
"""

    def clear_session(self, session_id: str):
        """清理会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    is_running: bool = False
    loop_step: int = 0
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    max_history_length: int = 20

    def add_to_history(self, role: str, content: str):
        """添加到历史"""
        if content:
            self.conversation_history.append({
                'role': role,
                'content': content.strip()
            })

            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history = self.conversation_history[-self.max_history_length:]

    def get_history_context(self) -> str:
        """获取历史上下文"""
        if not self.conversation_history:
            return "无历史对话"

        lines = []
        for msg in self.conversation_history:
            role_name = "用户" if msg['role'] == 'user' else "助手"
            lines.append(f"{role_name}: {msg['content']}")

        return "\n".join(lines)
```

---

## 九、错误处理和重试机制

### 9.1 错误码定义

```python
# common/errors.py

class ErrorCode(Enum):
    """错误码定义"""
    # 通用错误 (1xxx)
    UNKNOWN = 1000
    INVALID_REQUEST = 1001
    TIMEOUT = 1002
    SERVICE_UNAVAILABLE = 1003

    # Voice Service 错误 (2xxx)
    AUDIO_DECODE_FAILED = 2001
    AUDIO_BUFFER_OVERFLOW = 2002
    VAD_PROCESSING_FAILED = 2003
    ASR_PROCESSING_FAILED = 2004
    TTS_PROCESSING_FAILED = 2005

    # Brain Service 错误 (3xxx)
    SESSION_NOT_FOUND = 3001
    BRAIN_PROCESSING_FAILED = 3002
    APP_INVOKE_FAILED = 3003
    DEVICE_STATUS_UPDATE_FAILED = 3004

    # 服务间通信错误 (4xxx)
    BRAIN_SERVICE_UNREACHABLE = 4001
    BACKEND_SERVICE_UNREACHABLE = 4002
```

### 9.2 重试配置

```python
# common/retry.py

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避 + 抖动）"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay


# 默认重试配置
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=10.0
)

# Brain Service 调用重试配置
BRAIN_SERVICE_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=5.0
)
```

### 9.3 熔断机制

```python
# common/circuit_breaker.py

class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_open_until = 0

    def is_open(self) -> bool:
        """检查熔断器是否打开"""
        if self._circuit_open:
            if time.time() > self._circuit_open_until:
                # 进入半开状态
                self._circuit_open = False
                return False
            return True
        return False

    def record_success(self):
        """记录成功"""
        self._consecutive_failures = 0
        self._circuit_open = False

    def record_failure(self):
        """记录失败"""
        self._consecutive_failures += 1

        if self._consecutive_failures >= self.failure_threshold:
            self._circuit_open = True
            self._circuit_open_until = time.time() + self.recovery_timeout
```

---

## 十、服务监控和健康检查

### 10.1 健康检查端点

| 端点 | 描述 | 响应码 |
|------|------|--------|
| `GET /health` | 完整健康检查 | 200/503 |
| `GET /health/live` | 存活检查 | 200 |
| `GET /health/ready` | 就绪检查 | 200/503 |
| `GET /metrics` | Prometheus指标 | 200 |

### 10.2 Prometheus 指标

#### Voice Service 指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `voice_ws_connections_active` | Gauge | 活跃WebSocket连接数 |
| `voice_audio_packets_received_total` | Counter | 接收的音频包数量 |
| `voice_vad_processing_duration_seconds` | Histogram | VAD处理耗时 |
| `voice_asr_requests_total` | Counter | ASR请求数（按状态） |
| `voice_tts_requests_total` | Counter | TTS请求数（按状态） |
| `voice_brain_service_requests_total` | Counter | Brain Service调用数 |

#### Brain Service 指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `brain_process_requests_total` | Counter | 处理请求数（按状态） |
| `brain_process_duration_seconds` | Histogram | 处理耗时 |
| `brain_app_invocations_total` | Counter | App调用数 |
| `brain_active_sessions` | Gauge | 活跃会话数 |
| `brain_conversation_history_size` | Histogram | 对话历史长度 |

### 10.3 日志格式

```json
{
  "timestamp": "2026-03-11T10:30:00.123Z",
  "level": "INFO",
  "service": "voice-service",
  "session_id": "xxx",
  "message": "ASR recognized",
  "extra": {
    "asr_text": "打开油烟机",
    "audio_duration_s": 2.5,
    "latency_ms": 150
  }
}
```

---

## 十一、测试用例

### 11.1 Voice Service 测试

```python
# tests/test_vad_service.py

class TestVADService:
    def test_detect_speech_no_audio(self, vad_service):
        """测试空音频"""

    async def test_detect_speech_silence(self, vad_service):
        """测试静音"""

    async def test_detect_speech_with_voice(self, vad_service):
        """测试有语音的数据"""


# tests/test_asr_service.py

class TestASRService:
    async def test_recognize_speech_mock(self, asr_service):
        """测试 Mock ASR"""

    async def test_recognize_speech_with_backend(self, asr_service):
        """测试通过 Backend 识别"""

    async def test_recognize_speech_fallback_to_mock(self, asr_service):
        """测试失败时降级"""


# tests/test_tts_service.py

class TestTTSService:
    async def test_generate_speech_with_cache(self, tts_service):
        """测试缓存命中"""

    async def test_generate_mock_speech(self, tts_service):
        """测试 Mock TTS"""


# tests/test_brain_client.py

class TestBrainServiceClient:
    async def test_process_asr_text_success(self, client):
        """测试成功处理"""

    async def test_process_asr_text_failure(self, client):
        """测试处理失败"""

    async def test_circuit_breaker(self, client):
        """测试熔断"""
```

### 11.2 Brain Service 测试

```python
# tests/test_brain_service.py

class TestBrainService:
    def test_get_or_create_session(self, brain_service):
        """测试会话管理"""

    def test_conversation_history(self, brain_service):
        """测试对话历史"""

    async def test_process_brain_noise(self, brain_service):
        """测试处理噪音"""

    async def test_process_brain_success(self, brain_service):
        """测试成功处理"""

    async def test_call_query_generator_app(self, brain_service):
        """测试App调用"""


# tests/test_api.py

class TestBrainAPI:
    def test_health(self):
        """测试健康检查"""

    def test_process_endpoint(self):
        """测试处理端点"""

    def test_session_lifecycle(self):
        """测试会话生命周期"""
```

### 11.3 集成测试

```python
# tests/integration/test_voice_brain_integration.py

class TestVoiceBrainIntegration:
    async def test_full_flow(self, voice_agent):
        """测试完整流程：音频 -> VAD -> ASR -> Brain -> TTS"""

    async def test_brain_service_failure(self, voice_agent):
        """测试 Brain Service 失败场景"""

    async def test_vad_no_speech(self, voice_agent):
        """测试 VAD 未检测到语音"""
```

---

## 十二、实施步骤

### 12.1 阶段一：接口抽象（1-2天）

- [ ] 创建共享 Schema 定义
- [ ] 定义错误码和错误处理
- [ ] 设计 HTTP API 接口文档

### 12.2 阶段二：Voice Service 抽取（3-5天）

- [ ] 创建 Voice Service 项目结构
- [ ] 迁移 VAD/ASR/TTS 服务
- [ ] 实现 Brain Client
- [ ] 改造 WebSocket 路由
- [ ] 编写单元测试

### 12.3 阶段三：Brain Service 抽取（3-5天）

- [ ] 创建 Brain Service 项目结构
- [ ] 迁移核心处理逻辑
- [ ] 实现 HTTP API
- [ ] 会话管理实现
- [ ] 编写单元测试

### 12.4 阶段四：集成测试（2-3天）

- [ ] 服务间通信测试
- [ ] 完整流程测试
- [ ] 错误场景测试
- [ ] 性能测试

### 12.5 阶段五：部署上线（2-3天）

- [ ] Docker 镜像构建
- [ ] Kubernetes 配置
- [ ] 监控配置
- [ ] 灰度发布

---

## 附录

### A. 配置示例

```yaml
# voice-service/config.yaml
service:
  name: voice-service
  port: 8001

brain_service:
  url: http://brain-service:8002
  timeout: 30
  max_retries: 3

tts:
  base_url: https://tts.example.com
  speaker: default

asr:
  app_id: your-asr-app-id

websocket:
  max_connections: 1000
  heartbeat_interval: 30
```

```yaml
# brain-service/config.yaml
service:
  name: brain-service
  port: 8002

backend:
  url: http://backend:8000
  timeout: 60

apps:
  judge_app_id: e4d13f457f7f486c99ca11b39a7b8347
  query_generator_app_id: c7a27bd4e3cf49008ae99fc69817f155
```

### B. Docker Compose 示例

```yaml
version: '3.8'

services:
  voice-service:
    build: ./voice-service
    ports:
      - "8001:8001"
    environment:
      - BRAIN_SERVICE_URL=http://brain-service:8002
    depends_on:
      - brain-service
      - redis

  brain-service:
    build: ./brain-service
    ports:
      - "8002:8002"
    environment:
      - BACKEND_API_URL=http://backend:8000
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### C. 参考链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [WebSocket 协议](https://websockets.readthedocs.io/)
- [Prometheus 指标](https://prometheus.io/docs/concepts/data_model/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)