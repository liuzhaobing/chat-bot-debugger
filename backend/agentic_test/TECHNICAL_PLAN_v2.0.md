# 语音厨电测试系统 - 技术方案 v2.0

> **项目定位**：一个完整的数字测试工程师，能够自主完成厨电设备语音控制能力的测试任务

---

## 1. 方案概述

### 1.1 背景

设计一款语音测试产品，承担测试工程师角色，验证第三方语音音响（如小爱音响）在厨电控制方面的能力。

### 1.2 核心目标

| 目标 | 说明 |
|------|------|
| **设备无关性** | 通过协议描述文件支持任意厨电设备，无需修改代码 |
| **场景自主生成** | Agent 根据 IOT 协议自主分析并设计测试场景 |
| **语音交互验证** | 通过扬声器/麦克风与音响进行语音交互 |
| **综合验证机制** | 结合 IOT 状态查询和语音响应进行双重验证 |
| **宏观任务理解** | 支持测试组长派发宏观任务（如"测试 CQ928 的语音控制能力"） |
| **自主 Planning** | Agent 具备任务规划、分解、执行能力 |

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
│   1. 理解任务意图                                                │
│   2. 查询设备列表，锁定目标设备 GUID                                │
│   3. 加载设备协议，了解能力边界                                    │
│   4. 制定测试计划（测哪些功能点）                                  │
│   5. 生成具体测试场景                                            │
│   6. 执行测试（TTS→音响→ASR→IOT 验证）                             │
│   7. 汇总结果，生成测试报告                                       │
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
│         │                              │  │   (execute_full   │  │     │
│         │                              │  │    _loop)         │  │     │
│         ▼                              │  └───────────────────┘  │     │
│  ┌─────────────┐                       │           │             │     │
│  │ 协议解析器   │                       │           ▼             │     │
│  │ (Protocol   │                       │  ┌───────────────────┐  │     │
│  │  Parser)    │                       │  │  验证器 (Verif-   │  │     │
│  └─────────────┘                       │  │  ier)             │  │     │
│                                        │  └───────────────────┘  │     │
│                                        └─────────────────────────┘     │
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

---

## 2. 设备协议定义系统

### 2.1 协议文件格式设计

采用 YAML 格式定义设备协议，类似 Claude Code Skills 的声明式方式：

```yaml
# device_protocols/RangeHood.yaml

device_type: RangeHood        # 设备类型
display_name: 油烟机
manufacturer: 老板电器         # 可选
model_pattern: "CQ928.*"      # 支持的型号正则，用于设备匹配

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

  timeout_seconds: 10
  retry_count: 3
```

### 2.2 协议文件目录结构

```
backend/
├── device_protocols/
│   ├── __init__.py
│   ├── loader.py                  # 协议加载器
│   ├── parser.py                  # 协议解析器
│   ├── validator.py               # 协议验证器
│   ├── protocols/                 # 协议文件目录
│   │   ├── RangeHood.yaml         # 油烟机
│   │   ├── Oven.yaml              # 蒸烤箱
│   │   ├── DishWasher.yaml        # 洗碗机
│   │   └── GasStove.yaml          # 燃气灶
│   └── templates/
│       └── device_template.yaml
```

### 2.3 协议加载器核心接口

```python
class DeviceProtocolLoader:
    def get_protocol(self, device_type: str) -> Optional[dict]
    def list_protocols(self) -> List[str]
    def get_capabilities(self, device_type: str) -> dict
    def match_device(self, device_name: str, device_model: str = None) -> Optional[str]
```

---

## 3. Agent 自主场景生成系统

### 3.1 场景生成器架构

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
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 场景生成 App

- **App ID**: `scenario_generator_app`
- **功能**: 根据设备 IOT 协议生成测试场景
- **输入**: device_protocol, device_guid, test_focus
- **输出**: JSON 格式测试场景列表

### 3.3 SmartTestAgent 核心方法

```python
class SmartTestAgent(AgenticTestAgent):
    async def accept_task(self, task_description: str)
    async def _analyze_task(self)
    async def _locate_device(self, device_name, device_model)
    async def _load_device_protocol(self, device_type)
    async def _generate_test_scenarios(self, test_focus)
    async def _start_test_execution(self)
    async def _execute_next_scenario(self)
    async def _execute_scenario(self, scenario)
    async def _verify_result(self, expected, actual, asr_text)
    async def _generate_test_report(self)
```

---

## 4. 验证系统设计

### 4.1 双重验证机制

- **IOT 状态验证器**: 状态字段比对、状态变化检测、超时重试
- **语音响应验证器**: 关键词匹配、语义理解验证、情感分析
- **综合判定器**: 合并两种验证结果，输出最终判定

### 4.2 验证器模块

```python
class IOTStateVerifier:
    async def verify_state_change(...)

class ResponseVerifier:
    def verify_response(...)

class CombinedValidator:
    async def verify(...)
```

---

## 5. 测试执行流程

```
1. 任务接收 → 2. 任务分析 → 3. 设备锁定 → 4. 协议加载 → 5. 场景生成
                                                              ↓
7. 报告生成 ← 6. 测试执行 (TTS→播放→采集→ASR→IOT 查询→验证)
```

---

## 6. WebSocket 消息协议

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| start_test | 前端→后端 | 派发测试任务 |
| task_analyzed | 后端→前端 | 任务分析完成 |
| device_located | 后端→前端 | 设备锁定 |
| protocol_loaded | 后端→前端 | 协议加载成功 |
| scenarios_generated | 后端→前端 | 场景生成完成 |
| test_step | 后端→前端 | 测试步骤执行 |
| verification_result | 后端→前端 | 验证结果 |
| test_report | 后端→前端 | 测试报告 |

---

## 7. 开发计划

### Phase 1 - 核心功能 (P0/P1)

- [ ] 创建协议文件目录结构
- [ ] 实现协议加载器 (loader.py)
- [ ] 创建示例设备协议 (RangeHood.yaml, Oven.yaml)
- [ ] 扩展 Agent 支持 Planning (SmartTestAgent)
- [ ] 实现场景生成 App
- [ ] 实现验证器模块 (verifiers.py)

### Phase 2 - 增强功能 (P2)

- [ ] 多设备联动测试
- [ ] 测试报告可视化
- [ ] 人工介入机制

### Phase 3 - 高级功能 (P3)

- [ ] 自动学习新设备协议
- [ ] 异常场景自动发现
- [ ] 持续回归测试

---

## 8. 关键设计决策

| 决策点 | 选择 | 说明 |
|--------|------|------|
| 设备匹配 | Agent 自主决策 | 不依赖自动匹配逻辑，Agent 查询后自行判断 |
| 协议管理 | 静态文件 | 存放在代码库中，Git 管理版本 |
| 任务派发 | 宏观任务 | Agent 自主 Planning，不是工具 |

---

*文档版本：v2.0*  
*创建日期：2026-03-03*  
*更新说明：基于原始方案，结合主人指示整理，明确 Agent 的数字员工定位*
