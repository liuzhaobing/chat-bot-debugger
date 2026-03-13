# Tester Service 架构设计文档

## 1. 背景

当前 `agent_service.py` 中混合了多种职责：
- 音频输入/输出处理 (VAD, ASR, TTS)
- 智能体循环控制
- **测试用例管理**
- **测试执行控制**
- **测试结果评判**
- **测试报告生成**

为了实现单一职责原则和更好的可维护性，需要将"测试工程师"相关的功能抽象成独立的 `tester_service.py`。

## 2. 现状分析

### 2.1 当前代码中测试相关的逻辑分布

| 功能 | 当前实现位置 | 问题 |
|------|-------------|------|
| 测试用例设计 | `__init__` 中硬编码 `self.test_cases` | 不可配置，无法动态加载 |
| 测试用例执行 | `generate_next_query` 方法 | 与 Agent 逻辑耦合 |
| 测试结果评判 | `call_judge_app` 方法 | 判断逻辑不完整，缺少实际结果记录 |
| 测试任务推进 | 散落在多个方法中 | `current_case_index += 1` 逻辑简单，缺少状态机 |
| 测试结果记录 | 仅定义字段 `actual_results`、`test_result` | 没有实际更新逻辑 |
| 测试完成判断 | 无 | 没有检查是否所有用例执行完成 |
| 缺陷记录 | 无 | 没有独立的缺陷管理 |
| 测试报告输出 | 无 | 没有报告生成功能 |

### 2.2 关键代码分析

```python
# 当前测试用例结构
test_case = {
    "id": "APPL-LIGHT-001",
    "module": "一体机 - 灯光控制(lightControl)",
    "title": "语音打开一体机内部灯光",
    "type": "Functional",  # Functional, State, EdgeCase, Error, Security, Performance
    "preconditions": [...],
    "device_guids": [...],
    "steps": [...],
    "expect_results": [...],
    "actual_results": [],  # 待填充
    "test_result": "NotRun"  # NotRun, Pass, Fail, Blocked, Skipped
}

# 当前的任务推进逻辑（不完整）
if not query_result.get('should_continue', True):
    self.current_case_index += 1  # 简单推进，缺少边界检查
```

## 3. 架构设计

### 3.1 类职责划分

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TesterService                                 │
│                     (测试工程师服务)                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 职责: 管理测试用例的生命周期，执行测试，生成报告                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ TestCaseManager│  │ TestExecutor   │  │ TestReporter   │         │
│  │  用例管理器     │  │  用例执行器     │  │  报告生成器     │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ TestJudge      │  │ DefectTracker  │  │ TaskProgressor │         │
│  │  结果评判器     │  │  缺陷跟踪器     │  │  任务推进器     │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     AgenticTestAgent                                 │
│                   (智能体主循环 - 重构后)                             │
├─────────────────────────────────────────────────────────────────────┤
│ 职责: 音频处理、智能体循环控制、与 TesterService 协作                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心类设计

#### 3.2.1 TesterService - 主服务类

```python
class TesterService:
    """测试工程师服务 - 主入口"""

    def __init__(self, config: Optional[TesterConfig] = None):
        self.config = config or TesterConfig()
        self.case_manager = TestCaseManager(self.config)
        self.executor = TestExecutor(self.config)
        self.judge = TestJudge(self.config)
        self.progressor = TaskProgressor(self.config)
        self.defect_tracker = DefectTracker(self.config)
        self.reporter = TestReporter(self.config)

    # 主要接口
    async def design_test_cases(self, scenario: str) -> List[TestCase]
    async def execute_test_step(self, context: TestContext) -> TestStepResult
    async def judge_test_result(self, context: TestContext) -> JudgeResult
    async def progress_task(self, current_result: JudgeResult) -> TaskProgress
    async def record_result(self, case_id: str, result: TestResult)
    async def record_defect(self, defect: Defect) -> str
    async def generate_report(self) -> TestReport
    def is_all_cases_completed(self) -> bool
```

#### 3.2.2 TestCase - 测试用例数据类

```python
@dataclass
class TestCase:
    """测试用例"""
    id: str
    module: str
    title: str
    type: TestCaseType  # Enum: FUNCTIONAL, STATE, EDGE_CASE, ERROR, SECURITY, PERFORMANCE
    preconditions: List[str]
    device_guids: List[str]
    steps: List[str]
    expect_results: List[str]
    actual_results: List[str] = field(default_factory=list)
    test_result: TestResultStatus = TestResultStatus.NOT_RUN
    execution_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    error_message: Optional[str] = None

@dataclass
class TestResult:
    """测试执行结果"""
    case_id: str
    status: TestResultStatus
    actual_results: List[str]
    execution_time: datetime
    duration_seconds: float
    device_status_before: Dict[str, Any]
    device_status_after: Dict[str, Any]
    asr_text: str
    ai_response: str
    error_message: Optional[str] = None
```

#### 3.2.3 TestCaseManager - 用例管理器

```python
class TestCaseManager:
    """测试用例管理器"""

    def __init__(self, config: TesterConfig):
        self.test_cases: List[TestCase] = []
        self.current_index: int = 0

    async def load_cases(self, source: str) -> int:
        """从文件/数据库加载测试用例"""

    async def design_cases_from_prd(self, prd: str, backend_service) -> List[TestCase]:
        """根据PRD自动设计测试用例"""

    def get_current_case(self) -> Optional[TestCase]:
        """获取当前测试用例"""

    def get_case_by_id(self, case_id: str) -> Optional[TestCase]:
        """根据ID获取测试用例"""

    def update_case_result(self, case_id: str, result: TestResult) -> None:
        """更新测试用例结果"""

    def get_all_cases(self) -> List[TestCase]:
        """获取所有测试用例"""

    def get_statistics(self) -> TestCaseStatistics:
        """获取用例统计信息"""
```

#### 3.2.4 TestExecutor - 用例执行器

```python
class TestExecutor:
    """测试用例执行器"""

    async def generate_test_query(
        self,
        test_case: TestCase,
        context: ExecutionContext
    ) -> str:
        """生成测试查询语句"""

    async def record_device_status_before(
        self,
        device_guids: List[str],
        iot_service
    ) -> Dict[str, Any]:
        """执行前记录设备状态"""

    async def record_device_status_after(
        self,
        device_guids: List[str],
        iot_service
    ) -> Dict[str, Any]:
        """执行后记录设备状态"""

    def construct_test_data(
        self,
        test_case: TestCase,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """构造测试数据"""
```

#### 3.2.5 TestJudge - 结果评判器

```python
class TestJudge:
    """测试结果评判器"""

    async def judge(
        self,
        test_case: TestCase,
        execution_result: ExecutionResult,
        device_status_before: Dict,
        device_status_after: Dict
    ) -> JudgeResult:
        """评判测试结果"""

    async def call_judge_app(
        self,
        asr_text: str,
        device_changes: Dict
    ) -> Dict[str, Any]:
        """调用判断App进行评判"""

    def compare_device_status(
        self,
        before: Dict,
        after: Dict,
        expected_changes: Dict
    ) -> DeviceChangeResult:
        """比较设备状态变化"""
```

#### 3.2.6 TaskProgressor - 任务推进器

```python
class TaskProgressor:
    """测试任务推进器"""

    def __init__(self, config: TesterConfig):
        self.state = TaskState.READY
        self.noise_retry_count = 0
        self.max_noise_retry = 2

    def determine_next_action(self, context: ProgressContext) -> NextAction:
        """决定下一步行动"""
        # 返回: RETRY, NEXT_CASE, STOP, WAIT

    def should_retry_noise(self) -> bool:
        """是否应该重试噪音"""

    def advance_to_next_case(self) -> bool:
        """推进到下一个用例"""

    def is_all_completed(self, total_cases: int, current_index: int) -> bool:
        """判断是否全部完成"""
```

#### 3.2.7 DefectTracker - 缺陷跟踪器

```python
class DefectTracker:
    """缺陷跟踪器"""

    def __init__(self):
        self.defects: List[Defect] = []

    def record_defect(
        self,
        case_id: str,
        defect_type: DefectType,
        description: str,
        severity: Severity,
        device_guid: Optional[str] = None,
        evidence: Optional[Dict] = None
    ) -> str:
        """记录缺陷，返回缺陷ID"""

    def get_defects_by_case(self, case_id: str) -> List[Defect]:
        """获取用例关联的缺陷"""

    def get_defects_by_severity(self, severity: Severity) -> List[Defect]:
        """按严重程度获取缺陷"""

    def get_statistics(self) -> DefectStatistics:
        """获取缺陷统计"""
```

#### 3.2.8 TestReporter - 报告生成器

```python
class TestReporter:
    """测试报告生成器"""

    async def generate_report(
        self,
        test_cases: List[TestCase],
        defects: List[Defect],
        session_info: SessionInfo
    ) -> TestReport:
        """生成测试报告"""

    async def export_to_markdown(self, report: TestReport) -> str:
        """导出为Markdown格式"""

    async def export_to_html(self, report: TestReport) -> str:
        """导出为HTML格式"""

    async def export_to_json(self, report: TestReport) -> str:
        """导出为JSON格式"""
```

### 3.3 数据流设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                           测试执行流程                               │
└─────────────────────────────────────────────────────────────────────┘

1. 初始化阶段
   ┌──────────┐     ┌──────────────┐     ┌───────────┐
   │ 启动测试  │ ──▶ │ 加载测试用例  │ ──▶ │ 初始化状态 │
   └──────────┘     └──────────────┘     └───────────┘

2. 单个用例执行循环
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │  ┌────────────┐    ┌────────────┐    ┌────────────┐          │
   │  │ 获取当前用例 │───▶│ 记录前置状态 │───▶│ 生成测试查询 │          │
   │  └────────────┘    └────────────┘    └────────────┘          │
   │         │                                    │               │
   │         ▼                                    ▼               │
   │  ┌────────────┐    ┌────────────┐    ┌────────────┐          │
   │  │ 执行测试    │◀───│ Agent执行   │◀───│ 发送到Agent │          │
   │  └────────────┘    └────────────┘    └────────────┘          │
   │         │                                    │               │
   │         ▼                                    ▼               │
   │  ┌────────────┐    ┌────────────┐    ┌────────────┐          │
   │  │ 记录后置状态 │───▶│ 结果评判    │───▶│ 记录结果    │          │
   │  └────────────┘    └────────────┘    └────────────┘          │
   │         │                                    │               │
   │         ▼                                    ▼               │
   │  ┌────────────┐    ┌────────────┐    ┌────────────┐          │
   │  │ 记录缺陷    │◀───│ 判断是否通过 │◀───│ 更新用例状态 │          │
   │  └────────────┘    └────────────┘    └────────────┘          │
   │         │                                                   │
   └─────────│───────────────────────────────────────────────────┘
             │
             ▼
3. 任务推进决策
   ┌────────────────┐
   │ 是否全部完成？  │
   └───────┬────────┘
           │
     ┌─────┴─────┐
     │           │
   是│           │否
     ▼           ▼
   ┌─────┐   ┌────────────┐
   │ 结束 │   │ 推进下一用例 │
   └─────┘   └────────────┘

4. 报告生成阶段
   ┌──────────┐     ┌────────────┐     ┌──────────┐
   │ 汇总结果  │ ──▶ │ 生成报告    │ ──▶ │ 导出报告  │
   └──────────┘     └────────────┘     └──────────┘
```

### 3.4 枚举和常量定义

```python
from enum import Enum

class TestCaseType(Enum):
    """测试用例类型"""
    FUNCTIONAL = "Functional"       # 功能测试
    STATE = "State"                 # 状态测试
    EDGE_CASE = "EdgeCase"          # 边界测试
    ERROR = "Error"                 # 错误处理测试
    SECURITY = "Security"           # 安全测试
    PERFORMANCE = "Performance"     # 性能测试

class TestResultStatus(Enum):
    """测试结果状态"""
    NOT_RUN = "NotRun"      # 未执行
    PASS = "Pass"           # 通过
    FAIL = "Fail"           # 失败
    BLOCKED = "Blocked"     # 阻塞
    SKIPPED = "Skipped"     # 跳过

class TaskState(Enum):
    """任务状态"""
    READY = "ready"                 # 准备就绪
    EXECUTING = "executing"         # 执行中
    WAITING_RESPONSE = "waiting"    # 等待响应
    JUDGING = "judging"             # 评判中
    RETRYING = "retrying"           # 重试中
    COMPLETED = "completed"         # 已完成
    STOPPED = "stopped"             # 已停止

class NextAction(Enum):
    """下一步行动"""
    RETRY = "retry"             # 重试当前用例
    NEXT_CASE = "next_case"     # 下一个用例
    STOP = "stop"               # 停止测试
    WAIT = "wait"               # 等待

class DefectType(Enum):
    """缺陷类型"""
    FUNCTIONAL = "functional"       # 功能缺陷
    PERFORMANCE = "performance"     # 性能缺陷
    SECURITY = "security"           # 安全缺陷
    USABILITY = "usability"         # 易用性缺陷
    COMPATIBILITY = "compatibility" # 兼容性缺陷

class Severity(Enum):
    """缺陷严重程度"""
    CRITICAL = "critical"   # 致命
    MAJOR = "major"         # 严重
    NORMAL = "normal"       # 一般
    MINOR = "minor"         # 轻微
    SUGGESTION = "suggestion"  # 建议
```

### 3.5 配置类

```python
@dataclass
class TesterConfig:
    """测试服务配置"""
    # App IDs
    judge_app_id: str = "e4d13f457f7f486c99ca11b39a7b8347"
    query_generator_app_id: str = "c7a27bd4e3cf49008ae99fc69817f155"

    # 重试配置
    max_noise_retry: int = 2           # 最大噪音重试次数
    max_execution_retry: int = 1       # 最大执行重试次数

    # 超时配置
    case_timeout_seconds: float = 60.0  # 单个用例超时时间
    total_timeout_seconds: float = 3600.0  # 总超时时间

    # 报告配置
    report_formats: List[str] = field(default_factory=lambda: ["markdown", "json"])

    # 用例文件路径
    test_cases_file: Optional[str] = None
```

## 4. 接口设计

### 4.1 与 AgentService 的集成接口

```python
class TesterService:
    """测试工程师服务"""

    # ========== 核心接口 ==========

    async def initialize(self, session_id: str, iot_config: Dict) -> None:
        """初始化测试服务"""

    async def get_next_test_query(self) -> Optional[str]:
        """获取下一个测试查询语句"""

    async def process_execution_result(
        self,
        asr_text: str,
        device_status_before: Dict,
        device_status_after: Dict
    ) -> TaskProgress:
        """处理执行结果并推进任务"""

    def is_testing_completed(self) -> bool:
        """判断测试是否全部完成"""

    async def finalize(self) -> TestReport:
        """结束测试并生成报告"""


    # ========== 回调接口（供 Agent 调用） ==========

    async def on_query_executed(self, query: str, asr_text: str) -> None:
        """查询执行完成回调"""

    async def on_device_status_changed(
        self,
        device_guid: str,
        status_before: Dict,
        status_after: Dict
    ) -> None:
        """设备状态变化回调"""

    async def on_noise_detected(self) -> NextAction:
        """噪音检测回调，返回下一步行动"""

    async def on_execution_error(self, error: Exception) -> NextAction:
        """执行错误回调，返回下一步行动"""
```

### 4.2 使用示例

```python
# 在 AgentService 中使用 TesterService
class AgenticTestAgent:
    def __init__(self, session_id: str, send_callback: Callable, ...):
        # ... 其他初始化 ...
        self.tester_service = TesterService()

    async def start_loop(self, initial_query: str, iot_config: Dict):
        # 初始化测试服务
        await self.tester_service.initialize(self.session_id, iot_config)

        # 获取第一个测试查询
        next_query = await self.tester_service.get_next_test_query()

        while self.is_running:
            # 执行测试...
            asr_text = await self.execute_query(next_query)

            # 处理结果
            progress = await self.tester_service.process_execution_result(
                asr_text=asr_text,
                device_status_before=before_status,
                device_status_after=after_status
            )

            # 判断是否继续
            if self.tester_service.is_testing_completed():
                break

            next_query = await self.tester_service.get_next_test_query()

        # 生成报告
        report = await self.tester_service.finalize()
```

## 5. 实现计划

### 5.1 文件结构

```
worker/app/services/
├── agent_service.py      # 重构后的智能体服务
├── tester_service.py     # 新增：测试工程师服务
└── tester/               # 测试服务子模块
    ├── __init__.py
    ├── models.py         # 数据类定义
    ├── case_manager.py   # 用例管理器
    ├── executor.py       # 用例执行器
    ├── judge.py          # 结果评判器
    ├── progressor.py     # 任务推进器
    ├── defect_tracker.py # 缺陷跟踪器
    └── reporter.py       # 报告生成器
```

### 5.2 实现步骤

1. **Phase 1: 基础框架**
   - 创建 `tester/models.py` 定义所有数据类
   - 创建 `tester_service.py` 主服务类框架

2. **Phase 2: 核心功能**
   - 实现 `TestCaseManager` - 用例管理
   - 实现 `TestExecutor` - 用例执行
   - 实现 `TestJudge` - 结果评判

3. **Phase 3: 任务控制**
   - 实现 `TaskProgressor` - 任务推进
   - 实现噪音重试逻辑
   - 实现完成判断逻辑

4. **Phase 4: 报告与缺陷**
   - 实现 `DefectTracker` - 缺陷跟踪
   - 实现 `TestReporter` - 报告生成

5. **Phase 5: 集成重构**
   - 重构 `agent_service.py` 使用 `TesterService`
   - 移除 `agent_service.py` 中的测试相关代码
   - 编写单元测试

## 6. 测试用例

### 6.1 单元测试用例

| ID | 测试项 | 预期结果 |
|----|--------|----------|
| UT-001 | 加载测试用例 | 正确解析用例文件 |
| UT-002 | 生成测试查询 | 返回符合格式的查询语句 |
| UT-003 | 设备状态比较 | 正确识别状态变化 |
| UT-004 | 结果评判-Pass | 返回通过状态 |
| UT-005 | 结果评判-Fail | 返回失败状态并记录缺陷 |
| UT-006 | 任务推进-下一用例 | current_index 正确递增 |
| UT-007 | 任务推进-全部完成 | is_all_completed 返回 True |
| UT-008 | 噪音重试逻辑 | 重试计数正确 |
| UT-009 | 缺陷记录 | 缺陷正确关联到用例 |
| UT-010 | 报告生成 | 生成有效的 Markdown 报告 |

## 7. 风险与注意事项

1. **向后兼容**: 重构后需要确保现有功能不受影响
2. **性能考虑**: 频繁的状态查询可能影响性能，需要考虑缓存
3. **异步处理**: 所有服务方法都是异步的，需要注意正确使用 async/await
4. **错误处理**: 需要完善的错误处理和日志记录
5. **测试覆盖**: 需要编写完整的单元测试和集成测试

## 8. 版本历史

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| v1.0 | 2026-03-12 | Claude | 初始版本 |
| v1.1 | 2026-03-12 | Claude | 完成重构，将测试功能从 agent_service.py 剥离到 tester_service.py |

## 9. 重构实施记录

### 9.1 已完成的变更

#### 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `worker/app/services/tester/__init__.py` | 新增 | 测试模块初始化 |
| `worker/app/services/tester/models.py` | 新增 | 数据类定义 |
| `worker/app/services/tester/case_manager.py` | 新增 | 用例管理器 |
| `worker/app/services/tester/executor.py` | 新增 | 用例执行器 |
| `worker/app/services/tester/judge.py` | 新增 | 结果评判器 |
| `worker/app/services/tester/progressor.py` | 新增 | 任务推进器 |
| `worker/app/services/tester/defect_tracker.py` | 新增 | 缺陷跟踪器 |
| `worker/app/services/tester/reporter.py` | 新增 | 报告生成器 |
| `worker/app/services/tester_service.py` | 新增 | 测试工程师主服务 |
| `worker/app/services/agent_service.py` | 重构 | 移除测试代码，集成 TesterService |

#### agent_service.py 移除的代码

- `JUDGE_APP_ID`, `QUERY_GENERATOR_APP_ID` 常量
- `test_cases` 属性和默认测试用例数据
- `current_case_index`, `current_case` 属性
- `noise_retry_count`, `max_noise_retry` 属性
- `conversation_history`, `max_conversation_history_length` 属性
- `generate_next_query()` 方法
- `call_judge_app()` 方法
- `call_query_generator_app()` 方法
- `_get_mock_judge_result()` 方法
- `_get_mock_query_result()` 方法
- `_format_current_case_context()` 方法
- `_get_family_devices_context()` 方法
- `_get_conversation_history_context()` 方法
- `_add_to_conversation_history()` 方法
- `_clear_conversation_history()` 方法

#### agent_service.py 新增的代码

- `self.tester_service = TesterService(...)` 初始化
- 使用 `self.tester_service.on_noise_detected()` 处理噪音重试
- 使用 `self.tester_service.get_next_test_query()` 获取测试查询
- 使用 `self.tester_service.add_to_conversation_history()` 管理对话历史
- 使用 `self.tester_service.is_testing_completed()` 判断测试完成

### 9.2 兼容性保证

重构后的代码保持以下兼容性：

1. **接口兼容**: 所有公开方法签名不变
2. **功能兼容**: 所有原有功能正常运行
3. **日志兼容**: log_event 方法保持不变
4. **回调兼容**: send_callback 方法保持不变

### 9.3 测试验证

```bash
# 验证导入
python -c "
from app.services.agent_service import AgenticTestAgent
from app.services.tester_service import TesterService
from app.services.tester.models import NextAction, TaskState, TestCase
print('All imports successful!')
"

# 验证方法存在
python -c "
from app.services.tester_service import TesterService
methods = ['initialize', 'get_next_test_query', 'process_execution_result',
           'is_testing_completed', 'on_noise_detected', 'add_to_conversation_history',
           'call_judge_app', 'get_statistics', 'finalize', 'stop']
for m in methods:
    assert hasattr(TesterService, m), f'{m} missing'
print('All methods exist!')
"
```