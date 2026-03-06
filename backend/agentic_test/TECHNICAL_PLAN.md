# 语音厨电测试系统 - 技术方案 v2.2

> **项目定位**：一个完整的数字测试工程师，能够自主完成厨电设备语音控制能力的测试任务

> **版本说明**：v0.2 是 v0.1版本的升级，梳理了已实现和未实现的功能模块，作为唯一保留的技术计划文档。

---

## 1. 方案概述

### 1.1 背景

设计一款语音测试产品，承担测试工程师角色，验证第三方语音音响（如小爱音响）在厨电控制方面的能力。

### 1.2 核心目标

| 目标 | 说明 | 状态 |
|------|------|------|
| **设备无关性** | 通过协议描述文件支持任意厨电设备，无需修改代码 | ✅ 已实现 |
| **场景自主生成** | Agent 根据 IOT 协议自主分析并设计测试场景 | ❌ 未实现 |
| **语音交互验证** | 通过扬声器/麦克风与音响进行语音交互 | ✅ 已实现 |
| **综合验证机制** | 结合 IOT 状态查询和语音响应进行双重验证 | ✅ 已实现 |
| **宏观任务理解** | 支持测试组长派发宏观任务（如"测试 CQ928 的语音控制能力"） | ❌ 未实现 |
| **自主 Planning** | Agent 具备任务规划、分解、执行能力 | ❌ 未实现 |

### 1.3 系统角色定位

```
┌─────────────────────────────────────────────────────────────────┐
│                        测试组长（人类）                          │
│                                                                 │
│   派发宏观任务：                                                  │
│   "测试蒸烤炸一体机 CQ928 的语音控制能力"                           │
│   "检查一下油烟机的语音控制好不好用"                               │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   数字测试工程师（Agent）                         │
│                                                                 │
│   【自主 Planning 能力】                                         │
│   1. 理解任务意图                    ← ❌ 未实现                  │
│   2. 查询设备列表，锁定目标设备 GUID    ← ❌ 未实现（部分实现）      │
│   3. 加载设备协议，了解能力边界        ← ✅ 已实现                  │
│   4. 制定测试计划（测哪些功能点）      ← ❌ 未实现                  │
│   5. 生成具体测试场景                ← ❌ 未实现                  │
│   6. 执行测试（TTS→音响→ASR→IOT 验证） ← ✅ 已实现（基础循环）      │
│   7. 汇总结果，生成测试报告           ← ❌ 未实现                  │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              输出测试报告，反馈给测试组长
```

### 1.4 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         测试系统 (Test System)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│  │ 设备协议库   │    │  场景生成器  │    │      测试执行引擎        │     │
│  │ (Device     │    │ (Scenario   │    │ (Test Execution Engine) │     │
│  │  Protocol   │───▶│  Generator) │───▶│                         │     │
│  │  Library)   │    │             │    │  ┌───────────────────┐  │     │
│  └─────────────┘    └─────────────┘    │  │   Agent Loop      │  │     │
│         │                 ▲            │  │   (execute_full   │  │     │
│         │                 │            │  │    _loop)         │  │     │
│         ▼                 │            │  └───────────────────┘  │     │
│  ┌─────────────┐          │            │           │             │     │
│  │ 协议解析器   │          │            │           ▼             │     │
│  │ (Protocol   │          │            │  ┌───────────────────┐  │     │
│  │  Parser)    │          │            │  │  验证器 (Verif-   │  │     │
│  └─────────────┘          │            │  │  ier)             │  │     │
│                           │            │  └───────────────────┘  │     │
│                           │            └─────────────────────────┘     │
│                           │                                              │
│                    ❌ 未实现                                              │
└─────────────────────────────────────────────────────────────────────────┘
              │                              │              │
              ▼                              ▼              ▼
       ┌─────────────┐               ┌─────────────┐ ┌─────────────┐
       │ IOT 平台    │               │  扬声器     │ │  麦克风     │
       │ (状态查询)  │               │  (TTS)     │ │  (ASR/VAD) │
       └─────────────┘               └─────────────┘ └─────────────┘
              │                              │              │
              ▼                              ▼              ▼
       ┌───────────────────────────────────────────────────────────┐
       │                    智能音响 (如小爱音响)                      │
       └───────────────────────────────────────────────────────────┘
              │
              ▼
       ┌───────────────────────────────────────────────────────────┐
       │                    厨电设备 (油烟机、蒸烤箱等)                 │
       └───────────────────────────────────────────────────────────┘
```

**图例说明**：
- ✅ 实线框：已实现的模块
- ❌ 虚线框/标注：未实现的模块

---

## 2. 设备协议定义系统

### 2.1 协议文件格式（已实现 ✅）

采用 **JSON 格式**定义设备协议，使用物模型协议结构，包含 properties（属性）、functions（功能）、events（事件）、tags（标签）四个核心部分：

```json
{
  "properties": [
    {
      "id": "workStatus",
      "name": "工作状态",
      "valueType": {
        "type": "enum",
        "elements": [
          {"value": "0", "text": "关机"},
          {"value": "1", "text": "开机"},
          {"value": "2", "text": "延时关机"}
        ]
      },
      "expands": {"source": "device", "type": ["report"]}
    }
  ],
  "functions": [
    {
      "id": "132",
      "name": "设置烟机工作状态",
      "inputs": [...],
      "output": {...}
    }
  ],
  "events": [...],
  "tags": [...]
}
```

### 2.2 协议文件目录结构（已实现 ✅）

```
backend/
├── device_protocols/
│   ├── __init__.py              ✅ 已实现
│   ├── loader.py                ✅ 已实现 - 协议加载器
│   ├── parser.py                ✅ 已实现 - 协议解析器
│   └── protocols/               ✅ 已实现 - 协议文件目录
│       ├── 油烟机物模型协议.json   ✅ 已实现
│       ├── 一体机物模型协议.json   ✅ 已实现
│       ├── 燃气灶物模型协议.json   ✅ 已实现
│       └── 自动翻炒锅物模型协议.json ✅ 已实现
```

### 2.3 协议加载器核心接口（已实现 ✅）

```python
class DeviceProtocolLoader:
    def get_protocol(self, device_type: str) -> Optional[dict]        # ✅ 已实现
    def list_protocols(self) -> List[str]                              # ✅ 已实现
    def get_properties(self, device_type: str) -> List[Dict]           # ✅ 已实现
    def get_property_by_id(self, device_type: str, property_id: str)   # ✅ 已实现
    def get_functions(self, device_type: str) -> List[Dict]            # ✅ 已实现
    def get_function_by_id(self, device_type: str, function_id: str)   # ✅ 已实现
    def extract_property_definitions(self, device_type: str, property_ids: List[str]) -> Dict  # ✅ 已实现
```

### 2.4 协议解析器（已实现 ✅）

```python
class ProtocolParser:
    @staticmethod
    def format_property_definition(property_def: Dict) -> str      # ✅ 已实现
    @staticmethod
    def format_property_definitions(property_defs: Dict) -> str    # ✅ 已实现
    @staticmethod
    def extract_enum_text(property_def: Dict, value: Any) -> str   # ✅ 已实现
    @staticmethod
    def format_property_change(property_id, property_def, old_value, new_value) -> str  # ✅ 已实现
```

### 2.5 协议结构说明

| 顶层字段 | 说明 | 用途 |
|---------|------|------|
| `properties` | 设备属性列表 | 定义设备可读写的状态属性（如工作状态、档位、灯开关） |
| `functions` | 设备功能列表 | 定义设备可执行的操作（如设置工作状态、设置档位） |
| `events` | 设备事件列表 | 定义设备上报的事件（如开关控制事件、档位调整事件） |
| `tags` | 设备标签列表 | 定义设备元数据（如厂商名、型号、MAC 地址） |

---

## 3. Agent 自主场景生成系统

### 3.1 场景生成器架构（未实现 ❌）

```
┌─────────────────────────────────────────────────────────────────┐
│                    场景生成器 (ScenarioGenerator)                 │
├─────────────────────────────────────────────────────────────────┤
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│   │ 协议分析器   │───▶│ 场景规划器   │───▶│ 测试用例生成器   │    │
│   └─────────────┘    └─────────────┘    └─────────────────┘    │
│         │                  │                    │               │
│         ▼                  ▼                    ▼               │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    LLM 驱动引擎                          │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│                         ❌ 未实现                                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 场景生成 App（未实现 ❌）

- **App ID**: `scenario_generator_app`
- **功能**: 根据设备 IOT 协议生成测试场景
- **输入**: device_protocol, device_guid, test_focus
- **输出**: JSON 格式测试场景列表
- **状态**: ❌ 未实现

### 3.3 现有 Agent 实现

目前实现了基础的 `AgenticTestAgent`，但不具备完整的 Planning 能力：

```python
class AgenticTestAgent:
    """现有 Agent 实现 - 基础测试循环"""

    async def start_loop(initial_query, iot_config)         # ✅ 已实现
    async def execute_full_loop()                            # ✅ 已实现 - TTS→播放→等待→采集
    async def process_audio(audio_data, audio_format)        # ✅ 已实现 - VAD→ASR→IOT查询→判断
    async def call_judge_app(asr_text, current_status, previous_status)  # ✅ 已实现
    async def call_query_generator_app(test_scenario, conversation_history)  # ✅ 已实现
    async def generate_next_query(judge_result, asr_text)   # ✅ 已实现
    async def update_device_status()                         # ✅ 已实现
    async def handle_intervention(message)                   # ✅ 已实现
```

### 3.4 SmartTestAgent 规划（未实现 ❌）

需要的完整智能测试 Agent：

```python
class SmartTestAgent(AgenticTestAgent):
    """智能测试 Agent - 支持协议驱动和自主场景生成"""

    # ❌ 未实现 - 任务接收与分析
    async def accept_task(self, task_description: str)
    async def _analyze_task(self)

    # ❌ 未实现 - 设备定位
    async def _locate_device(self, device_name, device_model)

    # ✅ 已有基础实现 - 协议加载
    async def _load_device_protocol(self, device_type)

    # ❌ 未实现 - 场景生成
    async def _generate_test_scenarios(self, test_focus)

    # ❌ 未实现 - 测试执行管理
    async def _start_test_execution(self)
    async def _execute_next_scenario(self)
    async def _execute_scenario(self, scenario)

    # ⚠️ 部分实现 - 验证（验证器已实现，但未完整集成）
    async def _verify_result(self, expected, actual, asr_text)

    # ❌ 未实现 - 报告生成
    async def _generate_test_report(self)
```

---

## 4. 验证系统设计

### 4.1 双重验证机制（已实现 ✅）

```
┌─────────────────────────────────────────────────────────────────┐
│                      验证器 (Verifier)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐      ┌─────────────────────────────┐ │
│   │   IOT 状态验证器     │      │     语音响应验证器           │ │
│   │   IOTStateVerifier  │      │     ResponseVerifier        │ │
│   │                     │      │                             │ │
│   │  ✅ 状态字段比对     │      │  ✅ 关键词匹配               │ │
│   │  ✅ 状态变化检测     │      │  ✅ 正则模式匹配             │ │
│   │  ✅ 超时重试机制     │      │                             │ │
│   │  ✅ jsondiff对比     │      │                             │ │
│   │  ✅ 智能验证App调用  │      │                             │ │
│   └─────────────────────┘      └─────────────────────────────┘ │
│              │                              │                   │
│              └──────────┬───────────────────┘                   │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │    综合判定器        │                            │
│              │  CombinedValidator  │                            │
│              │                     │                            │
│              │  ✅ 已实现          │                            │
│              └─────────────────────┘                            │
│                         │                                       │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │    验证报告生成      │                            │
│              │    ❌ 未实现        │                            │
│              └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 IOTStateVerifier（已实现 ✅）

```python
class IOTStateVerifier:
    """IOT设备状态验证器"""

    async def verify_state_change(
        device_guid, before_properties, after_properties,
        device_type, query, expectation, expected_changes
    ) -> VerificationResult                                    # ✅ 已实现

    async def verify_with_iot_query(
        device_guid, expected_changes, before_properties,
        token, max_retries, retry_interval, timeout
    ) -> VerificationResult                                    # ✅ 已实现

    def compare_properties(before, after) -> Dict              # ✅ 已实现
    def check_specific_properties(properties, expected)        # ✅ 已实现
```

**特性**：
- 使用 `jsondiff` 对比控制前后的 properties JSON
- 支持从物模型协议提取属性定义
- 支持调用验证App进行智能判断
- 带重试机制的IOT查询验证

### 4.3 ResponseVerifier（已实现 ✅）

```python
class ResponseVerifier:
    """语音响应验证器"""

    def verify_response(
        asr_text, expected_keywords, expected_patterns
    ) -> Dict[str, Any]                                        # ✅ 已实现
```

### 4.4 CombinedValidator（已实现 ✅）

```python
class CombinedValidator:
    """综合验证器"""

    async def verify(
        device_guid, before_properties, after_properties,
        asr_text, expected_state_changes, expected_keywords
    ) -> Dict[str, Any]                                        # ✅ 已实现
```

**权重分配**：
- IOT状态验证：70%
- 语音响应验证：30%

---

## 5. 测试执行流程

### 5.1 完整测试流程对比

```
【已实现部分】
1. 初始化阶段
   ├── ✅ 加载设备协议 (device_protocols/*.json)
   ├── ✅ 发现在线设备 (IOT API: get_family_devices)
   └── ⚠️ 匹配设备与协议（手动指定，非自动匹配）

2. 测试执行阶段（基础循环）
   ├── ✅ 选择测试场景（手动指定）
   ├── ✅ TTS 生成测试语音
   ├── ✅ 扬声器播放 → 音响接收
   ├── ✅ 等待音响响应
   ├── ✅ 麦克风采集音响语音
   ├── ✅ ASR 识别语音内容
   ├── ✅ 查询 IOT 设备状态
   ├── ✅ 验证结果 (IOT状态 + 语音响应)
   └── ✅ 生成下一个查询（通过QueryGenerator App）

【未实现部分】
1. 任务分析阶段
   ├── ❌ 理解宏观任务意图
   ├── ❌ 任务分解为测试步骤
   └── ❌ 制定测试计划

2. 场景生成阶段
   ├── ❌ 基于协议自动生成测试场景
   └── ❌ 场景优先级排序

3. 报告生成阶段
   ├── ❌ 汇总测试结果
   ├── ❌ 生成测试报告
   └── ❌ 记录失败案例详情
```

### 5.2 规划执行流程

```
1. 任务接收 → 2. 任务分析 → 3. 设备锁定 → 4. 协议加载 → 5. 场景生成
                                                              ↓
7. 报告生成 ← 6. 测试执行 (循环每个场景: TTS→播放→采集→ASR→IOT查询→验证)
```

---

## 6. WebSocket 消息协议

### 6.1 已实现的消息类型

| 消息类型 | 方向 | 说明 | 状态 |
|---------|------|------|------|
| start_test | 前端→后端 | 派发测试任务 | ✅ 已实现 |
| stop_test | 前端→后端 | 停止测试 | ✅ 已实现 |
| audio_data | 前端→后端 | 发送音频数据 | ✅ 已实现 |
| intervention | 前端→后端 | 人工干预 | ✅ 已实现 |
| update_iot_config | 前端→后端 | 更新IOT配置 | ✅ 已实现 |
| connection_status | 后端→前端 | 连接状态 | ✅ 已实现 |
| status | 后端→前端 | 状态更新 | ✅ 已实现 |
| audio_play | 后端→前端 | 播放TTS音频 | ✅ 已实现 |
| vad_result | 后端→前端 | VAD结果 | ✅ 已实现 |
| transcript_final | 后端→前端 | ASR最终结果 | ✅ 已实现 |
| device_status_update | 后端→前端 | 设备状态更新 | ✅ 已实现 |
| query_generated | 后端→前端 | 生成的查询 | ✅ 已实现 |

### 6.2 未实现的消息类型

| 消息类型 | 方向 | 说明 | 状态 |
|---------|------|------|------|
| task_analyzed | 后端→前端 | 任务分析完成 | ❌ 未实现 |
| device_located | 后端→前端 | 设备锁定 | ❌ 未实现 |
| protocol_loaded | 后端→前端 | 协议加载成功 | ❌ 未实现 |
| scenarios_generated | 后端→前端 | 场景生成完成 | ❌ 未实现 |
| test_step | 后端→前端 | 测试步骤执行 | ❌ 未实现 |
| verification_result | 后端→前端 | 验证结果 | ⚠️ 部分实现 |
| test_report | 后端→前端 | 测试报告 | ❌ 未实现 |

---

## 7. 代码模块清单

### 7.1 已实现的模块

```
backend/
├── device_protocols/                    # ✅ 设备协议系统
│   ├── __init__.py                      # ✅ 模块导出
│   ├── loader.py                        # ✅ 协议加载器
│   ├── parser.py                        # ✅ 协议解析器
│   └── protocols/                       # ✅ 协议文件目录
│       ├── 油烟机物模型协议.json
│       ├── 一体机物模型协议.json
│       ├── 燃气灶物模型协议.json
│       └── 自动翻炒锅物模型协议.json
│
├── agentic_test/
│   ├── models.py                        # ✅ 数据模型
│   ├── consumers.py                     # ✅ WebSocket消费者
│   ├── agent_loop.py                    # ✅ Agent主循环
│   ├── services.py                      # ✅ TTS/ASR/VAD/IOT服务
│   ├── verifiers.py                     # ✅ 验证器模块
│   ├── audio_utils.py                   # ✅ 音频处理工具
│   ├── routing.py                       # ✅ WebSocket路由
│   └── urls.py                          # ✅ HTTP路由
```

### 7.2 未实现的模块

```
backend/
├── agentic_test/
│   ├── smart_test_agent.py              # ❌ 智能测试Agent（Planning能力）
│   └── scenario_generator.py            # ❌ 场景生成器
│
├── chat/
│   └── apps/                            # ❌ 测试相关App
│       ├── ScenarioGenerator.yaml       # ❌ 场景生成App
│       └── TestReportGenerator.yaml     # ❌ 测试报告生成App
```

---

## 8. 开发计划

### Phase 1 - 核心功能 (P0/P1)

| 功能 | 状态 | 优先级 |
|------|------|--------|
| 创建协议文件目录结构 | ✅ 已实现 | P0 |
| 实现协议加载器 (loader.py) | ✅ 已实现 | P0 |
| 实现协议解析器 (parser.py) | ✅ 已实现 | P0 |
| 创建示例设备协议 | ✅ 已实现 | P0 |
| 实现验证器模块 (verifiers.py) | ✅ 已实现 | P0 |
| 实现 Agent 基础循环 | ✅ 已实现 | P1 |
| 扩展 Agent 支持 Planning (SmartTestAgent) | ❌ 未实现 | P0 |
| 实现场景生成 App | ❌ 未实现 | P1 |
| 实现测试报告生成 | ❌ 未实现 | P1 |

### Phase 2 - 增强功能 (P2)

| 功能 | 状态 | 优先级 |
|------|------|--------|
| 多设备联动测试 | ❌ 未实现 | P2 |
| 测试报告可视化 | ❌ 未实现 | P2 |
| 人工介入机制 | ⚠️ 部分实现 | P2 |
| 设备自动匹配 | ❌ 未实现 | P2 |

### Phase 3 - 高级功能 (P3)

| 功能 | 状态 | 优先级 |
|------|------|--------|
| 自动学习新设备协议 | ❌ 未实现 | P3 |
| 异常场景自动发现 | ❌ 未实现 | P3 |
| 持续回归测试 | ❌ 未实现 | P3 |

---

## 9. 关键设计决策

| 决策点 | 选择 | 说明 |
|--------|------|------|
| 设备匹配 | Agent 自主决策 | 不依赖自动匹配逻辑，Agent 查询后自行判断 |
| 协议管理 | 静态 JSON 文件 | 存放在 device_protocols/protocols/ 中，Git 管理版本 |
| 协议格式 | JSON 物模型 | 使用标准物模型协议结构，包含 properties/functions/events/tags |
| 任务派发 | 宏观任务 | Agent 自主 Planning，不是工具 |
| 验证方式 | 双重验证 | IOT状态验证（70%）+ 语音响应验证（30%） |

---

## 10. 与原方案差异分析

### 10.1 实现差异

| 模块 | 原方案预期 | 实际实现 | 差异说明 |
|------|-----------|---------|---------|
| 协议格式 | YAML | JSON | v2.1已更新为JSON格式 |
| 协议加载 | 完整实现 | ✅ 完整实现 | 无差异 |
| 协议解析 | 完整实现 | ✅ 完整实现 | 无差异 |
| Agent类型 | SmartTestAgent | AgenticTestAgent | 未实现Planning能力 |
| 场景生成 | App驱动 | 未实现 | 核心功能缺失 |
| 验证器 | 双重验证 | ✅ 完整实现 | 无差异 |
| 测试报告 | 自动生成 | 未实现 | 需要实现 |

### 10.2 架构差异

原方案设计的 `SmartTestAgent` 具备完整的 Planning 能力，但实际只实现了基础的 `AgenticTestAgent`，具备：
- ✅ 基本的测试循环（TTS→播放→采集→ASR→验证）
- ✅ 调用判断App和QueryGenerator App
- ❌ 宏观任务理解能力
- ❌ 自主场景生成能力
- ❌ 测试报告生成能力

---

## 附录 A：现有协议文件清单

| 文件名 | 设备类型 | 说明 |
|-------|---------|------|
| `油烟机物模型协议.json` | RangeHood | 油烟机设备协议 |
| `一体机物模型协议.json` | IntegratedOven | 蒸烤炸一体机设备协议 |
| `燃气灶物模型协议.json` | GasStove | 燃气灶设备协议 |
| `自动翻炒锅物模型协议.json` | AutoStirFryPot | 自动翻炒锅设备协议 |

---

## 附录 B：验证App配置

| App名称 | App ID | 用途 |
|--------|--------|------|
| IotStateVerification | `3b5c603a388541f7942396adec9a57ce` | IOT状态智能验证 |
| DeviceControlQueryGenerator | `c7a27bd4e3cf49008ae99fc69817f155` | 生成下一个测试查询 |
| JudgeApp | `988988` | 判断ASR结果和设备状态 |

---

*文档版本：v0.2*
*创建日期：2026-03-06*
*更新说明：综合 v0.1 版本，梳理已实现和未实现的功能模块，作为唯一保留的技术计划文档*