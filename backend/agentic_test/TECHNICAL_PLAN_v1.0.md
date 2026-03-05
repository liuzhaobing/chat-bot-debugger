# 语音厨电测试系统技术方案

## 1. 方案概述

### 1.1 背景
设计一款语音测试产品，承担测试工程师角色，验证第三方语音音响（如小爱音响）在厨电控制方面的能力。

### 1.2 核心目标
- **设备无关性**：通过协议描述文件支持任意厨电设备，无需修改代码
- **场景自主生成**：Agent 根据 IOT 协议自主分析并设计测试场景
- **语音交互验证**：通过扬声器/麦克风与音响进行语音交互
- **综合验证机制**：结合 IOT 状态查询和语音响应进行双重验证

### 1.3 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         测试系统 (Test System)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │ 设备协议库   │    │  场景生成器  │    │      测试执行引擎        │  │
│  │ (Device     │    │ (Scenario   │    │ (Test Execution Engine) │  │
│  │  Protocol   │───▶│  Generator) │───▶│                         │  │
│  │  Library)   │    │             │    │  ┌───────────────────┐  │  │
│  └─────────────┘    └─────────────┘    │  │   Agent Loop      │  │  │
│         │                              │  │   (execute_full   │  │  │
│         ▼                              │  │    _loop)         │  │  │
│  ┌─────────────┐                       │  └───────────────────┘  │  │
│  │ 协议解析器   │                       │           │             │  │
│  │ (Protocol   │                       │           ▼             │  │
│  │  Parser)    │                       │  ┌───────────────────┐  │  │
│  └─────────────┘                       │  │  验证器 (Verif-   │  │  │
│                                        │  │  ier)             │  │  │
│                                        │  └───────────────────┘  │  │
│                                        └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
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

---

## 2. 设备协议定义系统

### 2.1 协议文件格式设计

采用 YAML 格式定义设备协议，类似 Claude Code Skills 的声明式方式：

```yaml
# device_protocols/RangeHood.yaml

device_type: RangeHood  # 设备类型
display_name: 油烟机
manufacturer: 老板电器  # 可选
model_pattern: ".*"     # 支持的型号正则

# 设备能力定义
capabilities:
  power_control:
    description: 电源开关控制
    commands:
      - name: "打开油烟机"
        action: "turn_on"
        expected_state:
          power: "on"
        test_phrases:
          - "打开油烟机"
          - "开启油烟机"
          - "把油烟机打开"

      - name: "关闭油烟机"
        action: "turn_off"
        expected_state:
          power: "off"
        test_phrases:
          - "关闭油烟机"
          - "关掉油烟机"
          - "把油烟机关了"

  fan_speed:
    description: 风档调节
    commands:
      - name: "设置低档"
        action: "set_speed"
        params:
          speed: "low"
        expected_state:
          fan_speed: 1
        test_phrases:
          - "油烟机调到低档"
          - "把油烟机开小一点"

      - name: "设置中档"
        action: "set_speed"
        params:
          speed: "medium"
        expected_state:
          fan_speed: 2

      - name: "设置高档"
        action: "set_speed"
        params:
          speed: "high"
        expected_state:
          fan_speed: 3
        test_phrases:
          - "油烟机调到最大"
          - "把油烟机开大一点"

  light_control:
    description: 照明灯控制
    commands:
      - name: "打开照明灯"
        action: "light_on"
        expected_state:
          light: "on"

# IOT 状态映射
iot_state_mapping:
  # IOT 平台返回的状态字段 -> 内部状态映射
  power_status:
    field: "power"
    values:
      "1": "on"
      "0": "off"

  fan_level:
    field: "fan_speed"
    values:
      "1": "low"
      "2": "medium"
      "3": "high"

# 验证规则
validation_rules:
  response_keywords:
    success:
      - "好的"
      - "已为您"
      - "没问题"
    failure:
      - "无法"
      - "失败"
      - "不支持"

  timeout_seconds: 10  # 等待设备状态变化超时
  retry_count: 3       # 查询重试次数
```

### 2.2 协议文件目录结构

```
backend/
├── device_protocols/              # 设备协议库
│   ├── __init__.py
│   ├── loader.py                  # 协议加载器
│   ├── parser.py                  # 协议解析器
│   ├── validator.py               # 协议验证器
│   ├── protocols/                 # 协议文件目录
│   │   ├── RangeHood.yaml         # 油烟机
│   │   ├── Oven.yaml              # 蒸烤箱
│   │   ├── DishWasher.yaml        # 洗碗机
│   │   ├── GasStove.yaml          # 燃气灶
│   │   └── ...                    # 其他设备
│   └── templates/                 # 协议模板
│       └── device_template.yaml
```

### 2.3 协议加载与解析

```python
# backend/device_protocols/loader.py

import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path

class DeviceProtocolLoader:
    """设备协议加载器 - 类似 Skills 加载机制"""

    def __init__(self, protocols_dir: str = None):
        self.protocols_dir = protocols_dir or os.path.join(
            os.path.dirname(__file__), 'protocols'
        )
        self._protocols: Dict[str, dict] = {}
        self._load_all_protocols()

    def _load_all_protocols(self):
        """加载所有协议文件"""
        protocols_path = Path(self.protocols_dir)
        for yaml_file in protocols_path.glob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    protocol = yaml.safe_load(f)
                    device_type = protocol.get('device_type')
                    if device_type:
                        self._protocols[device_type] = protocol
            except Exception as e:
                logging.error(f"Failed to load protocol {yaml_file}: {e}")

    def get_protocol(self, device_type: str) -> Optional[dict]:
        """获取指定设备类型的协议"""
        return self._protocols.get(device_type)

    def list_protocols(self) -> List[str]:
        """列出所有支持的设备类型"""
        return list(self._protocols.keys())

    def get_capabilities(self, device_type: str) -> dict:
        """获取设备能力定义"""
        protocol = self.get_protocol(device_type)
        return protocol.get('capabilities', {}) if protocol else {}
```

---

## 3. Agent 自主场景生成系统

### 3.1 场景生成器架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    场景生成器 (ScenarioGenerator)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│   │ 协议分析器   │───▶│ 场景规划器   │───▶│ 测试用例生成器   │    │
│   │ Protocol    │    │ Scenario    │    │ Test Case       │    │
│   │ Analyzer    │    │ Planner     │    │ Generator       │    │
│   └─────────────┘    └─────────────┘    └─────────────────┘    │
│         │                  │                    │               │
│         ▼                  ▼                    ▼               │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    LLM 驱动引擎                          │  │
│   │  (使用现有 App 模型，通过 prompt 引导生成测试场景)         │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 场景生成 App 设计

创建专门的场景生成 App，利用现有 App 模型：

```yaml
# App: ScenarioGenerator
name: GenerateTestScenarios
description: 根据设备IOT协议生成测试场景
app_type: Agent 2.0

system_prompt: |
  你是一个专业的厨电测试工程师。根据提供的设备IOT协议，生成全面且合理的测试场景。

  ## 输入参数
  - device_protocol: 设备IOT协议定义
  - test_focus: 测试重点 (可选: basic_control, edge_cases, error_handling)

  ## 输出要求
  生成 JSON 格式的测试场景列表，每个场景包含：
  1. scenario_name: 场景名称
  2. description: 场景描述
  3. test_steps: 测试步骤列表
  4. expected_results: 预期结果
  5. priority: 优先级 (high/medium/low)

  ## 测试场景设计原则
  1. 覆盖所有设备能力
  2. 包含正常流程和异常流程
  3. 考虑边界条件
  4. 考虑语音表达多样性

parameters:
  type: object
  properties:
    device_protocol:
      type: object
      description: 设备IOT协议JSON对象
    test_focus:
      type: string
      enum: [basic_control, edge_cases, error_handling, all]
      default: all
  required:
    - device_protocol
```

### 3.3 测试执行器增强

扩展现有的 `AgenticTestAgent`：

```python
# backend/agentic_test/smart_test_agent.py

class SmartTestAgent(AgenticTestAgent):
    """智能测试 Agent - 支持协议驱动和自主场景生成"""

    def __init__(self, session_id: str, send_callback: Callable,
                 protocol_loader: DeviceProtocolLoader):
        super().__init__(session_id, send_callback)
        self.protocol_loader = protocol_loader
        self.current_device_protocol = None
        self.test_scenarios = []
        self.scenario_generator_app_id = "scenario_gen_app_id"  # 场景生成App

    async def load_device_protocol(self, device_type: str):
        """加载设备协议"""
        self.current_device_protocol = self.protocol_loader.get_protocol(device_type)
        if not self.current_device_protocol:
            raise ValueError(f"Unknown device type: {device_type}")

        await self.send_callback('protocol_loaded', {
            'device_type': device_type,
            'capabilities': list(self.current_device_protocol.get('capabilities', {}).keys())
        })

    async def generate_test_scenarios(self, test_focus: str = 'all'):
        """基于协议自主生成测试场景"""
        if not self.current_device_protocol:
            raise ValueError("No device protocol loaded")

        # 调用场景生成 App
        result = await self.call_app(
            self.scenario_generator_app_id,
            {
                "device_protocol": self.current_device_protocol,
                "test_focus": test_focus
            }
        )

        self.test_scenarios = result.get('scenarios', [])
        await self.send_callback('scenarios_generated', {
            'count': len(self.test_scenarios),
            'scenarios': self.test_scenarios
        })

        return self.test_scenarios

    async def execute_full_loop(self):
        """执行完整的测试循环 - 增强版"""
        if not self.test_scenarios:
            # 如果没有预设场景，自动生成
            await self.generate_test_scenarios()

        # 按优先级排序并执行
        for scenario in sorted(self.test_scenarios,
                               key=lambda x: x.get('priority', 'medium')):
            await self.execute_scenario(scenario)

    async def execute_scenario(self, scenario: dict):
        """执行单个测试场景"""
        scenario_name = scenario.get('scenario_name')
        await self.log_event('scenario_start', scenario_name)

        for step in scenario.get('test_steps', []):
            # Step 1: 生成语音指令
            test_phrase = step.get('test_phrase')
            await self.send_callback('status', f'执行: {test_phrase}')

            # Step 2: TTS 合成并发送
            tts_result = await self.tts_service.generate_speech(test_phrase)
            await self.send_callback('audio_play', tts_result)

            # Step 3: 等待音响响应
            await asyncio.sleep(3.0)  # 等待音响处理

            # Step 4: 采集音响语音响应
            # (通过 WebSocket 接收前端麦克风数据)

            # Step 5: 查询 IOT 设备状态
            device_status = await self.query_device_status()

            # Step 6: 验证结果
            verification = await self.verify_result(
                expected=step.get('expected_state'),
                actual=device_status,
                asr_text=self.last_asr_result
            )

            # Step 7: 记录结果
            await self.log_event('step_result', {
                'step': step,
                'verification': verification,
                'passed': verification.get('passed', False)
            })
```

---

## 4. 验证系统设计

### 4.1 双重验证机制

```
┌─────────────────────────────────────────────────────────────────┐
│                      验证器 (Verifier)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐      ┌─────────────────────────────┐ │
│   │   IOT 状态验证器     │      │     语音响应验证器           │ │
│   │   IOTStateVerifier  │      │     ResponseVerifier        │ │
│   │                     │      │                             │ │
│   │  • 状态字段比对      │      │  • 关键词匹配               │ │
│   │  • 状态变化检测      │      │  • 语义理解验证             │ │
│   │  • 超时重试机制      │      │  • 情感分析(成功/失败)       │ │
│   └─────────────────────┘      └─────────────────────────────┘ │
│              │                              │                   │
│              └──────────┬───────────────────┘                   │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │    综合判定器        │                            │
│              │  CombinedValidator  │                            │
│              └─────────────────────┘                            │
│                         │                                       │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │    验证报告生成      │                            │
│              └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 验证器实现

```python
# backend/agentic_test/verifiers.py

class IOTStateVerifier:
    """IOT 状态验证器"""

    def __init__(self, iot_service: IOTService, protocol: dict):
        self.iot_service = iot_service
        self.protocol = protocol
        self.state_mapping = protocol.get('iot_state_mapping', {})
        self.validation_rules = protocol.get('validation_rules', {})

    async def verify_state_change(self, device_guid: str,
                                   expected_state: dict,
                                   timeout: float = 10.0) -> dict:
        """验证设备状态变化"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            # 查询当前状态
            current_status = await self.iot_service.get_device_status(
                device_guid, self.iot_service.token
            )

            # 映射并比对状态
            mapped_state = self._map_iot_state(current_status)
            match_result = self._compare_states(expected_state, mapped_state)

            if match_result['matched']:
                return {
                    'passed': True,
                    'actual_state': mapped_state,
                    'verification_time': asyncio.get_event_loop().time() - start_time
                }

            await asyncio.sleep(0.5)  # 短暂等待后重试

        # 超时
        return {
            'passed': False,
            'reason': 'timeout',
            'expected': expected_state,
            'actual': mapped_state
        }

    def _map_iot_state(self, raw_status: dict) -> dict:
        """映射 IOT 原始状态到内部状态"""
        mapped = {}
        for iot_field, mapping in self.state_mapping.items():
            internal_field = mapping['field']
            value_mapping = mapping.get('values', {})
            raw_value = str(raw_status.get(iot_field, ''))
            mapped[internal_field] = value_mapping.get(raw_value, raw_value)
        return mapped

    def _compare_states(self, expected: dict, actual: dict) -> dict:
        """比对状态"""
        matched = True
        differences = []

        for key, expected_value in expected.items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                matched = False
                differences.append({
                    'field': key,
                    'expected': expected_value,
                    'actual': actual_value
                })

        return {'matched': matched, 'differences': differences}


class ResponseVerifier:
    """语音响应验证器"""

    def __init__(self, protocol: dict):
        self.protocol = protocol
        self.validation_rules = protocol.get('validation_rules', {})

    def verify_response(self, asr_text: str, expected_intent: str) -> dict:
        """验证语音响应内容"""
        if not asr_text:
            return {'passed': False, 'reason': 'no_response'}

        keywords = self.validation_rules.get('response_keywords', {})
        success_keywords = keywords.get('success', [])
        failure_keywords = keywords.get('failure', [])

        # 关键词匹配
        has_success_keyword = any(kw in asr_text for kw in success_keywords)
        has_failure_keyword = any(kw in asr_text for kw in failure_keywords)

        # 判定结果
        if has_failure_keyword:
            return {
                'passed': False,
                'reason': 'failure_keyword_detected',
                'response': asr_text
            }
        elif has_success_keyword:
            return {
                'passed': True,
                'reason': 'success_keyword_detected',
                'response': asr_text
            }
        else:
            # 无明确关键词，需要 LLM 语义判断
            return {
                'passed': None,  # 需要进一步判断
                'reason': 'needs_semantic_analysis',
                'response': asr_text
            }


class CombinedValidator:
    """综合判定器"""

    def __init__(self, iot_verifier: IOTStateVerifier,
                 response_verifier: ResponseVerifier,
                 llm_app_id: str):
        self.iot_verifier = iot_verifier
        self.response_verifier = response_verifier
        self.llm_app_id = llm_app_id

    async def verify(self, device_guid: str, expected_state: dict,
                     asr_text: str, expected_intent: str) -> dict:
        """综合验证"""
        # 并行执行两种验证
        iot_task = self.iot_verifier.verify_state_change(device_guid, expected_state)
        response_task = asyncio.create_task(
            asyncio.coroutine(lambda: self.response_verifier.verify_response(asr_text, expected_intent))()
        )

        iot_result = await iot_task
        response_result = await response_task

        # 综合判定逻辑
        # 1. IOT 状态验证通过 -> 直接通过
        # 2. IOT 状态验证失败，但响应表示成功 -> 可能是延迟，需要重试
        # 3. 两者都失败 -> 确认失败
        # 4. 响应需要语义分析 -> 调用 LLM

        final_result = {
            'iot_verification': iot_result,
            'response_verification': response_result,
            'final_passed': False,
            'confidence': 0.0
        }

        if iot_result['passed']:
            final_result['final_passed'] = True
            final_result['confidence'] = 1.0
        elif response_result['passed'] is None:
            # 需要 LLM 语义分析
            semantic_result = await self._semantic_analysis(asr_text, expected_intent)
            final_result['semantic_verification'] = semantic_result
            final_result['final_passed'] = semantic_result.get('success', False)
            final_result['confidence'] = semantic_result.get('confidence', 0.5)
        else:
            final_result['final_passed'] = False
            final_result['confidence'] = 0.0

        return final_result

    async def _semantic_analysis(self, asr_text: str, expected_intent: str) -> dict:
        """调用 LLM 进行语义分析"""
        # 使用现有 App 机制
        result = await self.call_app(self.llm_app_id, {
            "asr_text": asr_text,
            "expected_intent": expected_intent,
            "task": "verify_response_semantic"
        })
        return result
```

---

## 5. 与现有系统集成

### 5.1 利用现有模块

| 现有模块 | 用途 | 复用方式 |
|---------|------|---------|
| `agentic_test/agent_loop.py` | Agent 主循环 | 继承扩展为 `SmartTestAgent` |
| `agentic_test/services.py` | TTS/ASR/VAD 服务 | 直接复用 |
| `agentic_test/consumers.py` | WebSocket 消费者 | 扩展支持协议加载消息 |
| `agentic_test/models.py` | 数据模型 | 扩展 `DeviceStatus` 关联协议 |
| `chat/models.py` - App | LLM 应用 | 创建场景生成/验证 App |
| `dial/views.py` - ScenarioTestRunner | 场景测试执行 | 参考 AI USER/JUDGER 模式 |

### 5.2 新增模块

```
backend/
├── device_protocols/          # 新增：设备协议系统
│   ├── __init__.py
│   ├── loader.py              # 协议加载器
│   ├── parser.py              # 协议解析器
│   ├── validator.py           # 协议验证器
│   └── protocols/             # 协议文件目录
│       └── *.yaml
│
├── agentic_test/
│   ├── smart_test_agent.py    # 新增：智能测试 Agent
│   ├── verifiers.py           # 新增：验证器模块
│   ├── scenario_generator.py  # 新增：场景生成器
│   └── ...existing files...
│
└── chat/
    └── apps/                  # 新增测试相关 App
        ├── ScenarioGenerator.yaml
        └── ResponseVerifier.yaml
```

---

## 6. 测试执行流程

### 6.1 完整测试流程

```
1. 初始化阶段
   ├── 加载设备协议 (device_protocols/*.yaml)
   ├── 发现在线设备 (IOT API: get_family_devices)
   ├── 匹配设备与协议 (根据 device_type)
   └── 生成测试场景 (LLM App: ScenarioGenerator)

2. 测试执行阶段 (循环每个场景)
   ├── 选择测试场景
   ├── TTS 生成测试语音
   ├── 扬声器播放 → 音响接收
   ├── 等待音响响应
   ├── 麦克风采集音响语音
   ├── ASR 识别语音内容
   ├── 查询 IOT 设备状态
   └── 验证结果 (IOT状态 + 语音响应)

3. 报告生成阶段
   ├── 汇总测试结果
   ├── 生成测试报告
   └── 记录失败案例详情
```

### 6.2 WebSocket 消息协议扩展

```json
// 加载设备协议
{
  "type": "load_protocol",
  "device_type": "RangeHood"
}

// 协议加载成功
{
  "type": "protocol_loaded",
  "content": {
    "device_type": "RangeHood",
    "capabilities": ["power_control", "fan_speed", "light_control"]
  }
}

// 场景生成请求
{
  "type": "generate_scenarios",
  "test_focus": "basic_control"
}

// 场景生成结果
{
  "type": "scenarios_generated",
  "content": {
    "count": 10,
    "scenarios": [...]
  }
}

// 测试步骤执行
{
  "type": "test_step",
  "content": {
    "step_id": 1,
    "action": "打开油烟机",
    "phrase": "小爱同学，打开油烟机"
  }
}

// 验证结果
{
  "type": "verification_result",
  "content": {
    "passed": true,
    "iot_verification": {...},
    "response_verification": {...}
  }
}
```

---

## 7. 部署与配置

### 7.1 环境变量配置

```bash
# .env

# IOT 平台配置
IOT_PLATFORM_URL=https://iot.example.com/api
IOT_TOKEN=your_token
IOT_FAMILY_ID=your_family_id

# 现有 TTS/ASR 配置 (复用)
TTS_BASE_URL=...
ASR_SERVICE_URL=...

# 新增配置
DEVICE_PROTOCOLS_DIR=/path/to/device_protocols
SCENARIO_GENERATOR_APP_ID=xxx
RESPONSE_VERIFIER_APP_ID=xxx
```

### 7.2 协议文件管理

- 通过 Git 管理协议文件版本
- 支持热加载新协议（无需重启服务）
- 提供协议文件校验工具

---

## 8. 后续扩展方向

### 8.1 Phase 1 (当前方案)
- 支持单设备测试
- 基础控制场景验证
- IOT + 语音双重验证

### 8.2 Phase 2 (扩展)
- 多设备联动测试
- 复杂场景测试（如烹饪场景）
- 测试报告可视化

### 8.3 Phase 3 (高级)
- 自动学习新设备协议
- 异常场景自动发现
- 持续回归测试

---

## 9. 待讨论问题

1. **协议文件管理方式**：是放在代码库中，还是支持动态上传？
2. **设备匹配逻辑**：如何从 IOT 设备列表自动识别设备类型？
3. **测试并发控制**：是否需要支持多设备并行测试？
4. **失败重试策略**：测试失败后的自动重试和人工介入机制？
5. **报告格式需求**：测试报告需要包含哪些信息和格式？

---

*文档版本: v1.0*
*创建日期: 2026-03-03*