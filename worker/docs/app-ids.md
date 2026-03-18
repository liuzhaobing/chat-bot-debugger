
## 10. App 调用架构

### 10.1 App 调用概览

整个测试工程师服务架构需要调用以下 5 个 App，每个 App 承担特定的职责：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TesterService                                      │
│                        (测试工程师主服务)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ 测试点提取App    │    │ 测试用例设计App  │    │ 查询生成器App    │         │
│  │ test_point_     │    │ 43281a11...      │    │ c7a27bd4...     │         │
│  │ extractor       │    │                  │    │                  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                                │
│  │ 评判App          │    │ 完成验证App      │                                │
│  │ e4d13f45...      │    │ completion_      │                                │
│  │                  │    │ verifier_app     │                                │
│  └─────────────────┘    └─────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 App 详细说明

#### 10.2.1 测试点提取 App

| 属性 | 值 |
|------|-----|
| **App ID** | `test_point_extractor` |
| **定义位置** | `tester_service.py:106` |
| **调用位置** | `TesterService.extract_test_points()` |
| **作用** | 从场景描述/需求文档中提取需要验证的测试点 |

**入参：**
```python
{
    "message": str,  # 场景描述或需求文档内容
    "parameters": {
        "scenario": str,        # 场景描述
        "device_types": List[str],  # 相关设备类型（可选）
        "test_focus": str       # 测试重点（可选）
    }
}
```

**出参：**
```python
{
    "test_points": [
        {
            "id": str,                    # 测试点ID，如 "TP001"
            "module": str,                # 所属模块
            "feature": str,               # 功能点名称
            "description": str,           # 测试点描述
            "priority": str,              # 优先级: high, normal, low
            "test_type": str,             # 测试类型: functional, state, edge_case, error
            "preconditions": List[str],   # 前置条件
            "related_devices": List[str], # 相关设备GUID
            "acceptance_criteria": List[str]  # 验收标准
        }
    ]
}
```

**调用示例：**
```python
# tester_service.py:289
result = await self.backend_service.invoke_app(
    app_id=self.TEST_POINT_EXTRACTOR_APP_ID,
    message=scenario_description,
    parameters={
        "scenario": scenario_description,
    }
)
```

---

#### 10.2.2 测试用例设计 App

| 属性 | 值 |
|------|-----|
| **App ID** | `43281a11ed734cbc9ed7d1e1f18a1f99` |
| **定义位置** | `case_manager.py:201` |
| **调用位置** | `TestCaseManager.design_cases_from_prd()` |
| **作用** | 根据 PRD（产品需求文档）自动生成测试用例 |

**入参：**
```python
{
    "message": str  # PRD 内容或需求描述
}
```

**出参：**
```python
[
    {
        "id": str,                    # 用例ID，如 "APPL-LIGHT-001"
        "module": str,                # 所属模块
        "title": str,                 # 用例标题
        "type": str,                  # 类型: Functional, State, EdgeCase, Error, Security
        "preconditions": List[str],   # 前置条件
        "device_guids": List[str],    # 相关设备GUID列表
        "steps": List[str],           # 测试步骤
        "expect_results": List[str],  # 预期结果
        "actual_results": List[str],  # 实际结果（初始为空）
        "test_result": str            # 测试结果: NotRun
    }
]
```

**调用示例：**
```python
# case_manager.py:207
result = await service.invoke_app(
    app_id=TEST_CASE_DESIGNER_APP_ID,
    message=prd
)
```

---

#### 10.2.3 查询生成器 App

| 属性 | 值 |
|------|-----|
| **App ID** | `c7a27bd4e3cf49008ae99fc69817f155` |
| **定义位置** | `tester_service.py:105`, `models.py:92` |
| **调用位置** | `TesterService.generate_test_query()`, `TestExecutor.generate_test_query()` |
| **作用** | 根据测试用例和执行上下文生成下一个测试查询语句 |

**入参：**
```python
{
    "message": str,  # 格式化的上下文信息（Markdown格式）
    # message 包含:
    # - 当前测试用例（表格格式）
    # - 家庭设备列表（表格格式）
    # - 对话历史
    # - 当前设备状态（JSON格式）
}
```

**message 结构示例：**
```markdown
**当前测试用例**：
| 用例ID | 模块 | 标题 | 类型 | 前置条件 | 要操控设备的deviceGuid | 测试步骤 | 预期结果 | 实际结果 | 测试结果 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| APPL-LIGHT-001 | 一体机 - 灯光控制 | 语音打开一体机内部灯光 | Functional | ... | 38-i750411c84f366 | ... | ... | | NotRun |

**家庭设备列表**：
| 设备GUID | 设备类型 | 设备标准型号 | 设备昵称 | 设备状态 |
|:---|:---|:---|:---|:---|
| 38-i750411c84f366 | 一体机 | CQ38-i7 | 厨房一体机 | 在线 |

**对话历史**：
- 测试员: 打开一体机灯
- 被测系统: 好的，已为您打开一体机灯

**当前设备状态**：
{
    "38-i750411c84f366": [{"name": "lightSwitch", "value": 1}]
}
```

**出参：**
```python
{
    "user_input": str,  # 生成的测试查询语句，如 "打开一体机灯"
    "reasoning": str,   # 推理过程（可选）
    "confidence": float # 置信度（可选）
}
```

**调用示例：**
```python
# tester_service.py:634
result = await self.backend_service.invoke_app(
    app_id=self.QUERY_GENERATOR_APP_ID,
    message=message,
)

# executor.py:87
result = await self.backend_service.invoke_app(
    app_id=self.config.query_generator_app_id,
    message=message,
)
```

---

#### 10.2.4 评判 App (JUDGE) 分析

| 属性 | 值 |
|------|-----|
| **App ID** | `e4d13f457f7f486c99ca11b39a7b8347` |
| **定义位置** | `tester_service.py:104`, `models.py:91` |
| **调用位置** | `TesterService.call_judge_app()`, `TestJudge.call_judge_app()` |

┌─────────────────┬────────────────────────────┐
│      作用       │            说明            │
├─────────────────┼────────────────────────────┤
│ 1. 判断步骤通过 │ 当前这一轮交互是否满足预期 │
├─────────────────┼────────────────────────────┤
│ 2. 决定是否继续 │ 当前用例是否还需要更多轮次 │
├─────────────────┼────────────────────────────┤
│ 3. 指导缺陷记录 │ 失败时用于触发自动创建缺陷记录   │
└─────────────────┴────────────────────────────┘

**三、输入数据**

```python
{
    "message": str,  # 格式化的上下文信息（Markdown格式）
    # message 包含:
    # 1. 当前测试用例（测试用例的表头字段）
    # 2. 对话历史记录（多轮对话的表头）
    # 3. 设备状态变更记录
}
```

**message 结构示例：**

```markdown
**当前测试用例**：
| 用例ID | 模块 | 标题 | 类型 | 前置条件 | 要操控设备的deviceGuid | 测试步骤 | 预期结果 | 实际结果 | 测试结果 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| APPL-LIGHT-001 | 一体机 - 灯光控制 | 语音打开一体机内部灯光 | Functional | ... | 38-i750411c84f366 | ... | ... | | NotRun |

**对话历史记录**：
> 注：当前正在评判的是第 3 轮对话（表格中最新的一轮）
> 注：仅显示最近 10 轮对话，更早的 5 条消息已省略

| 轮次 | 角色 | 内容 |
|:---|:---|:---|
| 2 | 测试员 | 打开一体机灯 |
| 2 | 被测系统 | 好的，已为您打开一体机灯 |

**设备状态变更记录**：
| 设备GUID | 状态有变更的参数键 | 变化前的值 | 变化后的值 | 参数键的含义说明 |
|:---|:---|:---|:---|:---|
| 38-i750411c84f366 | lightSwitch | 0 | 1 | 灯光开关状态 |
```

**对话历史限制说明：**

| 规则 | 说明 |
|------|------|
| 最多轮次 | 只传递最近 **10 轮** 对话（每轮包含用户和系统各1条，共20条消息） |
| 当前轮次标注 | 明确标注当前正在评判的是第几轮对话，避免模型误解 |
| 不足10轮 | 正常显示全部对话，不做额外处理 |
| 首轮测试 | 对话历史为空时，显示"当前是第 1 轮对话（首轮测试）" |

**四、输出数据 —— 标准JSON**

```python
{
    "actual_result": str,      # 用例实际执行情况记录，如 "用户请求打开灯，系统确认已打开，设备状态从关闭变为开启"
    "is_pass": bool,           # 当前测试步骤是否通过
    "next_action": str,        # 关键：判断当前测试用例是否执行完成，是否需要更多步骤继续完成当前用例的测试
                              # 枚举值: "next_step" 或 "next_case"
}
```

**调用示例：**
```python
# tester_service.py:756
result = await self.backend_service.invoke_app(
    app_id=self.JUDGE_APP_ID,
    message=message,  # 包含测试用例、对话历史、设备状态变更记录
)

# judge.py:132
result = await self.backend_service.invoke_app(
    app_id=self.config.judge_app_id,
    message=message,  # 包含测试用例、对话历史、设备状态变更记录
)
```

**六、流程闭环（TesterService.evaluate_round_result）**

评判结果返回后，TesterService 按以下流程闭环处理：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              评判结果处理流程                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. actual_result 记录到用例执行
   └─► current_case.actual_results.append(round_result)

2. 收集每个步骤的 is_pass 状态
   └─► current_case.step_pass_results.append(is_pass)

3. 判断 is_pass
   ├─► True:  继续流程
   └─► False: 记录缺陷 (defect_tracker.auto_create_from_test_result)

4. 判断 next_action
   │
   ├─► "next_step": 当前用例未完成
   │   └─► 推进当前用例的下一轮 query 生成和执行
   │
   └─► "next_case": 当前用例完成
       ├─► 判断所有步骤是否都通过: all(step_pass_results)
       │   ├─► True:  测试结果 = PASS
       │   └─► False: 测试结果 = FAIL
       └─► 推进下一条测试用例的执行
```

**流程闭环代码示例：**

```python
async def evaluate_round_result(self, asr_text, device_status_before, device_status_after):
    # 1. 评判结果
    judge_result = await self.judge_test_result(asr_text, device_status_before, device_status_after)

    current_case = self.case_manager.get_current_case()
    if current_case:
        # 2. actual_result 记录到用例执行
        round_result = f"[轮次{len(current_case.actual_results) + 1}] {'通过' if judge_result.is_pass else '失败'}: {judge_result.actual_result}"
        current_case.actual_results.append(round_result)

        # 3. 收集每个步骤的 is_pass 状态
        current_case.step_pass_results.append(judge_result.is_pass)

        # 4. is_pass=False 时，记录缺陷
        if not judge_result.is_pass:
            defect_id = self.defect_tracker.auto_create_from_test_result(current_case, {...})
            judge_result.defects.append(defect_id)

        # 5. next_action='next_case' 时，更新测试用例最终状态
        if judge_result.next_action == 'next_case':
            all_passed = all(current_case.step_pass_results)  # 判断所有步骤是否都通过
            test_status = TestResultStatus.PASS if all_passed else TestResultStatus.FAIL
            self.case_manager.update_case_result(current_case.id, test_status, ...)

    # 6. 执行推进
    action = self._determine_next_action(judge_result)
    progress = self._execute_progression(action, judge_result)
    return progress
```

---

#### 10.2.5 用例完成验证 App

| 属性 | 值 |
|------|-----|
| **App ID** | `completion_verifier_app` |
| **定义位置** | `progressor.py:39` |
| **调用位置** | `TaskProgressor._call_verifier_app()` |
| **作用** | 大模型验证是否所有测试用例都已完成执行 |

**入参：**
```python
{
    "message": str,  # 分析提示
    "parameters": {
        "case_table": str  # 测试用例执行状态表格（Markdown格式）
    }
}
```

**case_table 结构示例：**
```markdown
| index | title | test_result |
|-------|-------|-------------|
| 0     | 语音打开一体机内部灯光 | Pass |
| 1     | 语音关闭一体机内部灯光 | Pass |
| 2     | 语音重复打开：灯已开启时再次打开应幂等成功 | NotRun |
| 3     | 语音重复关闭：灯已关闭时再次关闭应幂等成功 | NotRun |
```

**出参：**
```python
{
    "completed": bool,              # 是否全部完成
    "unexecuted_indices": List[int], # 未执行用例的 index 列表
    "analysis": str                  # 分析结果说明
}
```

**调用示例：**
```python
# progressor.py:243
result = await self.backend_service.invoke_app(
    app_id=self.COMPLETION_VERIFIER_APP_ID,
    message=f"请分析以下测试用例执行情况，判断是否全部完成：\n\n{table}",
    parameters={
        "case_table": table,
    }
)
```

### 10.3 App 调用时序图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              测试执行流程                                     │
└──────────────────────────────────────────────────────────────────────────────┘

用户               AgenticTestAgent        TesterService           Backend/App
  │                      │                      │                       │
  │  1. 启动测试           │                      │                       │
  │─────────────────────▶│                      │                       │
  │                      │  initialize()        │                       │
  │                      │─────────────────────▶│                       │
  │                      │                      │                       │
  │                      │  2. 生成测试查询        │                       │
  │                      │─────────────────────▶│                       │
  │                      │                      │ invoke_app(查询生成器)  │
  │                      │                      │──────────────────────▶│
  │                      │                      │◀──────────────────────│
  │                      │◀─────────────────────│                       │
  │                      │                      │                       │
  │  3. TTS播放查询        │                      │                       │
  │◀─────────────────────│                      │                       │
  │                      │                      │                       │
  │  4. 用户/设备响应      │                      │                       │
  │─────────────────────▶│                      │                       │
  │                      │  5. 评判结果           │                       │
  │                      │─────────────────────▶│                       │
  │                      │                      │ invoke_app(评判App)    │
  │                      │                      │──────────────────────▶│
  │                      │                      │◀──────────────────────│
  │                      │◀─────────────────────│                       │
  │                      │                      │                       │
  │                      │  6. 检查完成状态       │                       │
  │                      │─────────────────────▶│                       │
  │                      │                      │ invoke_app(完成验证)   │
  │                      │                      │──────────────────────▶│
  │                      │                      │◀──────────────────────│
  │                      │◀─────────────────────│                       │
  │                      │                      │                       │
  │  ... 重复执行直到完成 ...                      │                       │
  │                      │                      │                       │
  │  7. 生成报告           │                      │                       │
  │                      │─────────────────────▶│                       │
  │◀─────────────────────│◀─────────────────────│                       │
```

### 10.4 App ID 配置汇总

所有 App ID 已统一管理，定义在 `app/services/app_ids.py` 文件中。

| App 名称 | 变量名 | 默认值 |
|----------|--------|--------|
| 测试点提取 | `TEST_POINT_EXTRACTOR_APP_ID` | `test_point_extractor` |
| 测试用例设计 | `TEST_CASE_DESIGNER_APP_ID` | `43281a11ed734cbc9ed7d1e1f18a1f99` |
| 查询生成器 | `QUERY_GENERATOR_APP_ID` | `c7a27bd4e3cf49008ae99fc69817f155` |
| 评判 | `JUDGE_APP_ID` | `e4d13f457f7f486c99ca11b39a7b8347` |
| 完成验证 | `COMPLETION_VERIFIER_APP_ID` | `completion_verifier_app` |

**导入方式：**

```python
from app.services.app_ids import (
    JUDGE_APP_ID,
    QUERY_GENERATOR_APP_ID,
    TEST_POINT_EXTRACTOR_APP_ID,
    TEST_CASE_DESIGNER_APP_ID,
    COMPLETION_VERIFIER_APP_ID,
)
```

**配置覆盖方式：**

可在初始化 `TesterService` 时通过 `tester_config` 参数覆盖默认 App ID：

```python
tester_config = {
    'judge_app_id': 'your_custom_judge_app_id',
    'query_generator_app_id': 'your_custom_query_generator_app_id',
}

tester_service = TesterService(
    backend_service=backend_service,
    send_callback=send_callback,
    log_event_callback=log_event,
    tester_config=tester_config
)
```

### 10.5 错误处理与降级策略

当 App 调用失败时，各模块都有对应的降级策略：

| App | 失败场景 | 降级策略 |
|-----|----------|----------|
| 测试点提取 | 无法解析场景 | 返回空列表，使用默认测试点 |
| 测试用例设计 | PRD 解析失败 | 返回空列表，使用预置测试用例 |
| 查询生成器 | 无法生成查询 | 使用 `_generate_default_query()` 基于规则生成 |
| 评判 App | 无法评判结果 | 使用 `_get_default_judge_result()` 返回默认评判 |
| 完成验证 | 无法验证完成状态 | 使用 `_get_default_verification_result()` 基于表格解析 |

### 10.6 调试工具

项目提供了 App 调试脚本，位于 `worker/scripts/debug_apps.py`，可以独立测试各个 App 的调用。

**使用方式：**

```bash
# 激活虚拟环境
conda activate chat-bot-debugger

# 运行调试脚本
cd worker
python scripts/debug_apps.py

# 或指定后端 URL
BACKEND_URL=http://localhost:8000 python scripts/debug_apps.py
```

**功能菜单：**

1. 评判 App - 测试评判结果
2. 查询生成器 App - 测试查询生成
3. 测试点提取 App - 测试测试点提取
4. 测试用例设计 App - 测试用例设计
5. 完成验证 App - 测试完成验证
6. 列出所有 App ID

**编程调用示例：**

```python
import asyncio
from scripts.debug_apps import (
    debug_judge_app,
    debug_query_generator_app,
    debug_test_point_extractor_app,
)

async def main():
    # 调试评判 App
    result = await debug_judge_app(
        asr_text="好的，已为您打开一体机灯",
        backend_url="http://localhost:8000"
    )
    print(result.content)

asyncio.run(main())
```
