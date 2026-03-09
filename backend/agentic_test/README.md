# Agentic Test 模块 - 实现文档

## 概述

Agentic Test 是一个完整的数字测试工程师系统，能够自主完成厨电设备语音控制能力的测试任务。

## 核心功能

### 1. 智能测试Agent (SmartTestAgent)

完整的Planning能力，包括：

- ✅ 理解测试组长的宏观任务意图
- ✅ 自动定位和识别目标设备GUID
- ✅ 加载设备协议并分析能力边界
- ✅ 自动生成测试场景
- ✅ 执行测试并验证结果
- ✅ 生成完整的测试报告

**使用示例**:

```python
from agentic_test.smart_test_agent import SmartTestAgent

# 创建智能测试Agent
agent = SmartTestAgent(
    session_id="test_session_001",
    send_callback=websocket_send,
    iot_config={
        'token': 'your_iot_token',
        'familyId': 'your_family_id',
        'env': 'test'
    }
)

# 接受测试任务
await agent.accept_task("测试蒸烤炸一体机 CQ928 的语音控制能力")

# Agent会自动：
# 1. 分析任务意图
# 2. 定位CQ928设备
# 3. 加载一体机协议
# 4. 生成测试场景
# 5. 执行测试
# 6. 生成报告
```

### 2. 场景生成器 (ScenarioGenerator)

从IOT协议自动生成测试场景：

```python
from agentic_test.scenario_generator import ScenarioGenerator

generator = ScenarioGenerator()

# 生成测试场景
scenarios = generator.generate_scenarios_from_protocol(
    device_type="油烟机",
    test_focus="语音控制"
)

# 场景包含：
# - scenario_id: 场景唯一标识
# - scenario_name: 场景名称
# - query: 测试查询语句
# - expected_state_changes: 预期的设备状态变化
# - expected_keywords: 预期的语音响应关键词
# - priority: 优先级 (1-5)
# - category: 分类
```

### 3. 测试报告生成器 (ReportGenerator)

生成多层次的测试报告：

```python
from agentic_test.report_generator import ReportGenerator

generator = ReportGenerator()

# 生成报告
report = generator.generate_report(
    task_description="测试油烟机语音控制",
    device_info={
        'device_guid': 'xxx',
        'device_name': '智能油烟机',
        'device_type': '油烟机'
    },
    scenario_results=scenario_results,
    start_time="2026-03-09T10:00:00",
    end_time="2026-03-09T10:30:00"
)

# 导出为Markdown
generator.export_to_markdown(report, "test_report.md")

# 或获取JSON
report_json = report.to_json()
```

### 4. JudgeApp

判断ASR结果和设备状态变化：

**配置文件**: `backend/chat/apps/JudgeApp.yaml`

**功能**:
- 分析ASR识别的语音内容
- 对比设备状态变化
- 判断设备是否按预期响应
- 决定是否需要继续测试对话

**输出格式**:
```json
{
  "analysis": "对当前情况的分析",
  "confidence": 0.8,
  "should_continue": true,
  "suggested_action": "continue_conversation",
  "detected_intent": "设备控制",
  "device_mentioned": true,
  "device_response_valid": true
}
```

### 5. 设备GUID识别

从query中智能识别目标设备：

```python
# 在SmartTestAgent中使用
target_guid = agent.identify_target_device_guid(
    query="打开油烟机",
    devices=device_list
)

# 支持的设备关键词：
# - 油烟机: ['油烟机', '抽油烟机', '烟机']
# - 一体机: ['一体机', '蒸烤', '烤箱', 'cq928']
# - 洗碗机: ['洗碗机', 'w760']
# - 燃气灶: ['燃气灶', '灶具', '灶台']
# - 翻炒锅: ['翻炒锅', '炒锅']
```

### 6. Agent循环生态闭环

增强的agent_loop.py提供：

**错误处理**:
- 异步任务取消处理 (asyncio.CancelledError)
- 异常恢复机制
- 详细的错误日志
- 防止循环卡死

**监督支持**:
```python
# 测试组长可以通过intervention介入
await agent.handle_intervention("停止")  # 停止测试
await agent.handle_intervention("继续")  # 继续测试
await agent.handle_intervention("跳过")  # 跳过当前场景
await agent.handle_intervention("打开油烟机")  # 新的测试指令
```

**生命周期管理**:
- 循环启动前的设备状态检查
- 发送query前的目标设备识别
- 循环步骤计数和最大步骤限制
- 资源清理和状态重置

## 模块结构

```
backend/agentic_test/
├── __init__.py
├── admin.py                    # Django admin配置
├── agent_loop.py               # ✅ Agent主循环（增强版）
├── apps.py                     # Django app配置
├── audio_utils.py              # 音频处理工具
├── consumers.py                # WebSocket消费者
├── models.py                   # 数据模型
├── report_generator.py         # ✅ 测试报告生成器
├── routing.py                  # WebSocket路由
├── scenario_generator.py       # ✅ 场景生成器
├── serializers.py              # 序列化器
├── services.py                 # 服务层（TTS/ASR/VAD/IOT）
├── smart_test_agent.py         # ✅ 智能测试Agent
├── urls.py                     # HTTP路由
├── verifiers.py                # 验证器
├── views.py                    # 视图
├── TECHNICAL_PLAN.md           # 技术方案文档
├── FEASIBILITY_ANALYSIS.md     # 可行性分析
└── README.md                   # 本文档
```

## 测试流程

### 完整测试流程

```
1. 任务接收
   ↓
2. 任务分析（识别设备类型和型号）
   ↓
3. 设备定位（查询设备列表，匹配目标设备）
   ↓
4. 协议加载（加载设备物模型协议）
   ↓
5. 场景生成（从协议自动生成测试场景）
   ↓
6. 测试执行（循环执行每个场景）
   ├── 6.1 TTS生成测试语音
   ├── 6.2 扬声器播放
   ├── 6.3 等待音响响应
   ├── 6.4 麦克风采集
   ├── 6.5 VAD语音检测
   ├── 6.6 ASR语音识别
   ├── 6.7 IOT状态查询
   ├── 6.8 结果验证
   └── 6.9 生成下一个查询
   ↓
7. 报告生成（汇总所有测试结果）
```

### 单个场景执行流程

```
场景开始
   ↓
获取控制前设备状态
   ↓
执行Agent循环（TTS→播放→采集→ASR→验证）
   ↓
获取控制后设备状态
   ↓
验证结果（IOT状态 + 语音响应）
   ↓
记录场景结果
   ↓
场景结束
```

## 配置说明

### IOT配置

```python
iot_config = {
    'token': 'your_iot_token',      # IOT认证token
    'familyId': 'your_family_id',   # 家庭ID
    'env': 'test'                   # 环境：test/prod
}
```

### Agent配置

```python
# 在agent_loop.py中
self.max_loop_steps = 10  # 最大循环步骤数，防止无限循环

# 在smart_test_agent.py中
# 场景执行间延迟
await asyncio.sleep(2.0)  # 场景间延迟2秒
```

## API接口

### WebSocket消息类型

**客户端→服务端**:
- `start_test`: 开始测试
- `stop_test`: 停止测试
- `audio_data`: 发送音频数据
- `intervention`: 人工干预
- `update_iot_config`: 更新IOT配置

**服务端→客户端**:
- `connection_status`: 连接状态
- `status`: 状态更新
- `task_received`: 任务已接收
- `task_analyzed`: 任务分析完成
- `device_located`: 设备已定位
- `protocol_loaded`: 协议加载成功
- `scenarios_generated`: 场景生成完成
- `test_step`: 测试步骤执行
- `scenario_result`: 场景执行结果
- `test_report`: 测试报告
- `audio_play`: 播放TTS音频
- `vad_result`: VAD结果
- `transcript_final`: ASR最终结果
- `device_status_update`: 设备状态更新
- `query_generated`: 生成的查询

### HTTP API

```python
# 测试IOT连接
POST /api/agentic-test/test-iot-connection/
{
    "iot_token": "xxx",
    "family_id": "xxx",
    "env": "test"
}

# 获取家庭设备列表
POST /api/agentic-test/get-family-devices/
{
    "iot_token": "xxx",
    "family_id": "xxx",
    "env": "test"
}

# 获取设备状态
POST /api/agentic-test/get-device-status/
{
    "iot_token": "xxx",
    "device_guid": "xxx",
    "env": "test"
}
```

## 错误处理

### 异常类型

1. **asyncio.CancelledError**: 任务被取消
   - 处理：优雅退出，清理资源

2. **IOT API错误**: 设备查询失败
   - 处理：使用模拟数据，记录警告日志

3. **ASR识别失败**: 语音识别返回空
   - 处理：等待新的音频输入

4. **循环超时**: 达到最大循环步骤
   - 处理：终止循环，生成报告

### 错误恢复策略

```python
# 在agent_loop.py中
try:
    # 执行循环步骤
    await self.execute_full_loop()
except asyncio.CancelledError:
    # 任务取消，优雅退出
    logger.info("Agent loop cancelled")
    break
except Exception as e:
    # 其他异常，尝试恢复
    logger.error(f"Agent loop step error: {e}")
    if self.loop_step < self.max_loop_steps:
        await self.send_callback('status', '尝试恢复循环...')
        await asyncio.sleep(2.0)
        continue
    else:
        break
```

## 日志记录

### 日志级别

- `INFO`: 正常流程信息
- `DEBUG`: 调试信息
- `WARNING`: 警告信息（如使用模拟数据）
- `ERROR`: 错误信息

### 日志示例

```python
logger.info(f"SmartTestAgent initialized for session {session_id}")
logger.debug(f"Audio buffer: {len(combined_audio)} bytes")
logger.warning("IOT配置不完整，使用模拟数据")
logger.error(f"Task analysis failed: {e}", exc_info=True)
```

## 性能优化建议

1. **并发执行场景**
   - 当前是串行执行，可以改为并发执行多个独立场景

2. **设备状态缓存**
   - 减少IOT查询频率
   - 使用缓存机制

3. **场景优先级调度**
   - 优先执行高优先级场景
   - 支持场景跳过

4. **音频处理优化**
   - 使用音频流式处理
   - 减少音频缓冲延迟

## 已知限制

1. **设备识别**
   - 当前使用简单的关键词匹配
   - 建议：使用LLM进行更智能的设备识别

2. **场景生成**
   - 当前基于协议规则生成
   - 建议：结合LLM生成更自然的测试查询

3. **报告格式**
   - 当前支持JSON和Markdown
   - 建议：增加HTML、PDF等格式

4. **多设备联动**
   - 当前只支持单设备测试
   - 建议：支持多设备协同测试

## 开发指南

### 添加新的设备类型

1. 在`device_protocols/protocols/`目录下添加新的协议JSON文件
2. 在`scenario_generator.py`中添加设备关键词映射
3. 在`smart_test_agent.py`中更新设备识别逻辑

### 扩展验证器

1. 在`verifiers.py`中添加新的验证器类
2. 实现`verify`方法
3. 在`smart_test_agent.py`中集成新验证器

### 自定义报告格式

1. 在`report_generator.py`中添加新的导出方法
2. 实现格式转换逻辑
3. 更新`TestReport`类

## 故障排查

### 问题：Agent循环卡死

**原因**: 可能是异步任务阻塞或死循环

**解决**:
1. 检查`max_loop_steps`设置
2. 查看日志中的循环步骤计数
3. 使用`intervention`发送停止指令

### 问题：设备状态查询失败

**原因**: IOT token过期或网络问题

**解决**:
1. 检查IOT配置是否正确
2. 测试IOT连接
3. 查看IOT API返回的错误信息

### 问题：场景生成为空

**原因**: 协议文件不存在或格式错误

**解决**:
1. 检查协议文件是否存在
2. 验证JSON格式是否正确
3. 查看协议加载日志

## 更新日志

### v0.3 (2026-03-09)

- ✅ 实现SmartTestAgent完整Planning能力
- ✅ 实现ScenarioGenerator场景生成器
- ✅ 实现ReportGenerator报告生成器
- ✅ 实现JudgeApp判断应用
- ✅ 实现设备GUID识别
- ✅ 增强Agent循环错误处理和监督支持

### v0.2 (2026-03-06)

- ✅ 实现基础Agent循环
- ✅ 实现验证器模块
- ✅ 实现协议加载和解析

### v0.1 (初始版本)

- ✅ 项目架构设计
- ✅ 基础模块实现

## 联系方式

如有问题或建议，请联系开发团队。
