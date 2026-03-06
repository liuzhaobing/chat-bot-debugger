# 语音厨电测试系统 - 技术方案 v2.1

> **项目定位**：一个完整的数字测试工程师，能够自主完成厨电设备语音控制能力的测试任务

> **更新说明**：v2.1 版本更新了设备协议格式，从 YAML 改为 JSON 格式（物模型协议），与 backend/device_protocols/protocols/ 下的实际协议文件保持一致。

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
└─────────────────────────────────────────────────────────────────┘
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
          {"value": "2", "text": "延时关机"},
          {"value": "3", "text": "待机"},
          {"value": "4", "text": "清洗锁定"},
          {"value": "5", "text": "挡风板拆除"}
        ]
      },
      "expands": {
        "source": "device",
        "type": ["report"]
      },
      "description": ""
    },
    {
      "id": "level",
      "name": "功率",
      "valueType": {
        "type": "enum",
        "elements": [
          {"value": "0", "text": "无风量"},
          {"value": "1", "text": "弱档"},
          {"value": "2", "text": "中档"},
          {"value": "3", "text": "强档"},
          {"value": "6", "text": "爆炒"}
        ]
      },
      "expands": {
        "source": "device",
        "type": ["report"]
      }
    },
    {
      "id": "lightStatus",
      "name": "灯开关",
      "valueType": {
        "type": "enum",
        "elements": [
          {"value": "0", "text": "关"},
          {"value": "1", "text": "开"}
        ]
      },
      "expands": {
        "source": "device",
        "type": ["report"]
      }
    }
  ],
  "functions": [
    {
      "id": "132",
      "name": "设置烟机工作状态",
      "async": false,
      "inputs": [
        {
          "id": "workStatus",
          "name": "工作状态",
          "valueType": {
            "type": "enum",
            "elements": [
              {"value": "0", "text": "关机"},
              {"value": "1", "text": "开机"},
              {"value": "3", "text": "待机状态 (预留)"},
              {"value": "4", "text": "清洗锁定状态"}
            ]
          },
          "expands": {"required": false}
        }
      ],
      "output": {
        "properties": [
          {
            "id": "rc",
            "name": "返回值",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "0", "text": "成功"},
                {"value": "1", "text": "失败"},
                {"value": "2", "text": "蓝牙配对失败"},
                {"value": "3", "text": "配网超时"},
                {"value": "4", "text": "配网取消/退出"},
                {"value": "32", "text": "OTA 包 ID 错误"},
                {"value": "33", "text": "OTA 数据校验错误"},
                {"value": "34", "text": "当前状态不允许 OTA"},
                {"value": "64", "text": "报警中（仅用于灶具）"},
                {"value": "65", "text": "灶具当前状态下不允许设置"}
              ]
            }
          }
        ],
        "type": "object"
      }
    },
    {
      "id": "134",
      "name": "设置烟机档位",
      "async": false,
      "inputs": [
        {
          "id": "level",
          "name": "功率",
          "valueType": {
            "type": "enum",
            "elements": [
              {"value": "0", "text": "关"},
              {"value": "1", "text": "小档"},
              {"value": "2", "text": "中档"},
              {"value": "3", "text": "大档"},
              {"value": "6", "text": "爆炒档"}
            ]
          },
          "expands": {"required": false}
        }
      ],
      "output": {
        "properties": [
          {
            "id": "rc",
            "name": "返回值",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "0", "text": "成功"},
                {"value": "1", "text": "失败"}
              ]
            }
          }
        ],
        "type": "object"
      }
    },
    {
      "id": "136",
      "name": "设置烟机灯",
      "async": false,
      "inputs": [
        {
          "id": "lightStatus",
          "name": "灯开关",
          "valueType": {
            "type": "enum",
            "elements": [
              {"value": "0", "text": "关"},
              {"value": "1", "text": "开"}
            ]
          },
          "expands": {"required": false}
        }
      ],
      "output": {
        "properties": [
          {
            "id": "rc",
            "name": "返回值",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "0", "text": "成功"},
                {"value": "1", "text": "失败"}
              ]
            }
          }
        ],
        "type": "object"
      }
    }
  ],
  "events": [
    {
      "id": "10",
      "name": "烟机开关 (机/电源) 控制事件",
      "expands": {"level": "ordinary"},
      "valueType": {
        "properties": [
          {
            "id": "eventParam",
            "name": "开关机状态",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "0", "text": "关机"},
                {"value": "1", "text": "开机"},
                {"value": "2", "text": "延时关机"}
              ]
            }
          },
          {
            "id": "controlTerminalType",
            "name": "控制端类型",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "10", "text": "Cloud"},
                {"value": "11", "text": "APP"},
                {"value": "13", "text": "MCU 按键/设备本机按键操作"},
                {"value": "14", "text": "语音魔盒"},
                {"value": "19", "text": "MCU 内部联动 (如蓝牙烟灶联动)"}
              ]
            }
          }
        ],
        "type": "object"
      }
    },
    {
      "id": "12",
      "name": "烟机功率/风量/档位调整事件",
      "expands": {"level": "ordinary"},
      "valueType": {
        "properties": [
          {
            "id": "eventParam",
            "name": "档位",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "0", "text": "关"},
                {"value": "1", "text": "弱档"},
                {"value": "2", "text": "中档"},
                {"value": "3", "text": "强档"},
                {"value": "6", "text": "爆炒"}
              ]
            }
          },
          {
            "id": "controlTerminalType",
            "name": "控制端类型",
            "valueType": {
              "type": "enum",
              "elements": [
                {"value": "10", "text": "Cloud"},
                {"value": "13", "text": "MCU 按键"},
                {"value": "14", "text": "语音魔盒"},
                {"value": "19", "text": "MCU 内部联动"}
              ]
            }
          }
        ],
        "type": "object"
      }
    }
  ],
  "tags": [
    {
      "id": "vendorID",
      "name": "厂商名",
      "valueType": {"type": "string"},
      "expands": {"type": ["report"]}
    },
    {
      "id": "modelName",
      "name": "设备型号",
      "valueType": {"type": "string"},
      "expands": {"type": ["report"]}
    },
    {
      "id": "macAddr",
      "name": "物理地址",
      "valueType": {"type": "string"},
      "expands": {"type": ["report"]}
    }
  ]
}
```

### 2.2 协议文件目录结构

```
backend/
├── device_protocols/
│   ├── __init__.py
│   ├── loader.py                  # 协议加载器
│   ├── parser.py                  # 协议解析器
│   ├── validator.py               # 协议验证器
│   └── protocols/                 # 协议文件目录
│       ├── 油烟机物模型协议.json    # 油烟机
│       ├── 一体机物模型协议.json    # 蒸烤炸一体机
│       ├── 燃气灶物模型协议.json    # 燃气灶
│       └── 自动翻炒锅物模型协议.json # 自动翻炒锅
```

### 2.3 协议加载器核心接口

```python
class DeviceProtocolLoader:
    def get_protocol(self, device_type: str) -> Optional[dict]
    def list_protocols(self) -> List[str]
    def get_capabilities(self, device_type: str) -> dict
    def match_device(self, device_name: str, device_model: str = None) -> Optional[str]
    def parse_function(self, function_id: str) -> dict
    def parse_property(self, property_id: str) -> dict
```

### 2.4 协议结构说明

| 顶层字段 | 说明 | 用途 |
|---------|------|------|
| `properties` | 设备属性列表 | 定义设备可读写的状态属性（如工作状态、档位、灯开关） |
| `functions` | 设备功能列表 | 定义设备可执行的操作（如设置工作状态、设置档位） |
| `events` | 设备事件列表 | 定义设备上报的事件（如开关控制事件、档位调整事件） |
| `tags` | 设备标签列表 | 定义设备元数据（如厂商名、型号、MAC 地址） |

### 2.5 测试场景生成依据

Agent 根据协议中的 `functions` 和 `properties` 自主生成测试场景：

1. **读取 functions** → 了解设备支持的操作命令
2. **读取 properties** → 了解设备的状态属性和枚举值
3. **读取 events** → 了解设备上报的事件类型
4. **生成测试用例** → 针对每个 function 生成对应的测试场景和验证语句

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

- [x] 创建协议文件目录结构
- [ ] 实现协议加载器 (loader.py)
- [x] 创建示例设备协议 (油烟机物模型协议.json, 一体机物模型协议.json)
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
| 协议管理 | 静态 JSON 文件 | 存放在 device_protocols/protocols/ 中，Git 管理版本 |
| 协议格式 | JSON 物模型 | 使用标准物模型协议结构，包含 properties/functions/events/tags |
| 任务派发 | 宏观任务 | Agent 自主 Planning，不是工具 |

---

## 附录：现有协议文件清单

| 文件名 | 设备类型 | 说明 |
|-------|---------|------|
| `油烟机物模型协议.json` | RangeHood | 油烟机设备协议 |
| `一体机物模型协议.json` | IntegratedOven | 蒸烤炸一体机设备协议 |
| `燃气灶物模型协议.json` | GasStove | 燃气灶设备协议 |
| `自动翻炒锅物模型协议.json` | AutoStirFryPot | 自动翻炒锅设备协议 |

---

*文档版本：v2.1*  
*创建日期：2026-03-05*  
*更新说明：基于 v2.0 版本，将设备协议格式从 YAML 更新为 JSON 物模型协议格式，与 backend/device_protocols/protocols/ 下的实际协议文件保持一致*
