"""
测试工程师服务 - 数据模型定义

包含所有测试相关的数据类、枚举类型定义。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum


# ============================================================================
# 枚举类型定义
# ============================================================================

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
    CRITICAL = "critical"       # 致命
    MAJOR = "major"             # 严重
    NORMAL = "normal"           # 一般
    MINOR = "minor"             # 轻微
    SUGGESTION = "suggestion"   # 建议


# ============================================================================
# 配置类
# ============================================================================

@dataclass
class TesterConfig:
    """测试服务配置"""
    # 任务基本信息
    name: str = ""                      # 任务名称
    prd_content: str = ""               # PRD/需求描述

    # TTS 配置
    tts_voice_id: str = ""              # TTS音色ID

    # IOT 协议配置
    iot_protocol_id: str = ""           # IOT设备协议ID

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


# ============================================================================
# 测试点数据类
# ============================================================================

@dataclass
class TestPoint:
    """测试点

    测试点是对测试需求的细化分解，每个测试点代表一个需要验证的功能点或场景。
    先提取测试点，再针对每个测试点设计具体的测试用例。
    """
    id: str                              # 测试点ID，如 "TP001"
    module: str                          # 所属模块
    feature: str                         # 功能点名称
    description: str                     # 测试点描述
    priority: str = "normal"             # 优先级: high, normal, low
    test_type: str = "functional"        # 测试类型: functional, state, edge_case, error
    preconditions: List[str] = field(default_factory=list)  # 前置条件
    related_devices: List[str] = field(default_factory=list)  # 相关设备GUID
    acceptance_criteria: List[str] = field(default_factory=list)  # 验收标准
    parent_id: Optional[str] = None      # 父测试点ID（用于层级结构）
    source: str = ""                     # 来源：需求文档、用户故事等
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "module": self.module,
            "feature": self.feature,
            "description": self.description,
            "priority": self.priority,
            "test_type": self.test_type,
            "preconditions": self.preconditions,
            "related_devices": self.related_devices,
            "acceptance_criteria": self.acceptance_criteria,
            "parent_id": self.parent_id,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestPoint":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            module=data.get("module", ""),
            feature=data.get("feature", ""),
            description=data.get("description", ""),
            priority=data.get("priority", "normal"),
            test_type=data.get("test_type", "functional"),
            preconditions=data.get("preconditions", []),
            related_devices=data.get("related_devices", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            parent_id=data.get("parent_id"),
            source=data.get("source", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


# ============================================================================
# 测试用例数据类
# ============================================================================

@dataclass
class TestCase:
    """测试用例"""
    id: str
    module: str
    title: str
    type: TestCaseType
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
    test_point_id: Optional[str] = None  # 关联的测试点ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "module": self.module,
            "title": self.title,
            "type": self.type.value,
            "preconditions": self.preconditions,
            "device_guids": self.device_guids,
            "steps": self.steps,
            "expect_results": self.expect_results,
            "actual_results": self.actual_results,
            "test_result": self.test_result.value,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "duration_seconds": self.duration_seconds,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "test_point_id": self.test_point_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            module=data.get("module", ""),
            title=data.get("title", ""),
            type=TestCaseType(data.get("type", "Functional")),
            preconditions=data.get("preconditions", []),
            device_guids=data.get("device_guids", []),
            steps=data.get("steps", []),
            expect_results=data.get("expect_results", []),
            actual_results=data.get("actual_results", []),
            test_result=TestResultStatus(data.get("test_result", "NotRun")),
            execution_time=datetime.fromisoformat(data["execution_time"]) if data.get("execution_time") else None,
            duration_seconds=data.get("duration_seconds"),
            retry_count=data.get("retry_count", 0),
            error_message=data.get("error_message"),
            test_point_id=data.get("test_point_id"),
        )


# ============================================================================
# 测试结果数据类
# ============================================================================

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

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "case_id": self.case_id,
            "status": self.status.value,
            "actual_results": self.actual_results,
            "execution_time": self.execution_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "device_status_before": self.device_status_before,
            "device_status_after": self.device_status_after,
            "asr_text": self.asr_text,
            "ai_response": self.ai_response,
            "error_message": self.error_message,
        }


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    asr_text: str
    ai_response: str
    device_changes: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class JudgeResult:
    """评判结果"""
    case_id: str
    is_pass: bool
    confidence: float
    analysis: str
    detected_intent: Optional[str] = None
    should_continue: bool = True
    suggested_action: str = "continue_conversation"
    device_mentioned: bool = False
    defects: List[str] = field(default_factory=list)  # 缺陷ID列表

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "case_id": self.case_id,
            "is_pass": self.is_pass,
            "confidence": self.confidence,
            "analysis": self.analysis,
            "detected_intent": self.detected_intent,
            "should_continue": self.should_continue,
            "suggested_action": self.suggested_action,
            "device_mentioned": self.device_mentioned,
            "defects": self.defects,
        }


# ============================================================================
# 测试完成检查结果
# ============================================================================

@dataclass
class CompletionCheckResult:
    """测试完成检查结果"""
    completed: bool                           # 是否全部完成
    unexecuted_indices: List[int]             # 未执行用例的 index 列表
    verified_by_llm: bool = False             # 是否经过大模型验证
    llm_analysis: Optional[str] = None        # 大模型分析结果

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "completed": self.completed,
            "unexecuted_indices": self.unexecuted_indices,
            "verified_by_llm": self.verified_by_llm,
            "llm_analysis": self.llm_analysis,
        }


# ============================================================================
# 任务推进数据类
# ============================================================================

@dataclass
class TaskProgress:
    """任务推进结果"""
    action: NextAction
    current_case_index: int
    total_cases: int
    message: str
    state: TaskState
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "action": self.action.value,
            "current_case_index": self.current_case_index,
            "total_cases": self.total_cases,
            "message": self.message,
            "state": self.state.value,
            "completed": self.completed,
        }


# ============================================================================
# 缺陷数据类
# ============================================================================

@dataclass
class Defect:
    """缺陷"""
    id: str
    case_id: str
    defect_type: DefectType
    description: str
    severity: Severity
    device_guid: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "open"  # open, fixed, verified, closed

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "defect_type": self.defect_type.value,
            "description": self.description,
            "severity": self.severity.value,
            "device_guid": self.device_guid,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


# ============================================================================
# 报告数据类
# ============================================================================

@dataclass
class TestCaseStatistics:
    """测试用例统计"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0
    not_run: int = 0
    pass_rate: float = 0.0

    def calculate_pass_rate(self):
        """计算通过率"""
        executed = self.total - self.not_run
        if executed > 0:
            self.pass_rate = round(self.passed / executed * 100, 2)
        else:
            self.pass_rate = 0.0


@dataclass
class DefectStatistics:
    """缺陷统计"""
    total: int = 0
    critical: int = 0
    major: int = 0
    normal: int = 0
    minor: int = 0
    suggestion: int = 0
    open_count: int = 0
    fixed_count: int = 0
    closed_count: int = 0


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    iot_env: str = "test"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "iot_env": self.iot_env,
        }


@dataclass
class TestReport:
    """测试报告"""
    session_info: SessionInfo
    case_statistics: TestCaseStatistics
    defect_statistics: DefectStatistics
    test_cases: List[TestCase]
    defects: List[Defect]
    generated_at: datetime = field(default_factory=datetime.now)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_info": self.session_info.to_dict(),
            "case_statistics": {
                "total": self.case_statistics.total,
                "passed": self.case_statistics.passed,
                "failed": self.case_statistics.failed,
                "blocked": self.case_statistics.blocked,
                "skipped": self.case_statistics.skipped,
                "not_run": self.case_statistics.not_run,
                "pass_rate": self.case_statistics.pass_rate,
            },
            "defect_statistics": {
                "total": self.defect_statistics.total,
                "critical": self.defect_statistics.critical,
                "major": self.defect_statistics.major,
                "normal": self.defect_statistics.normal,
                "minor": self.defect_statistics.minor,
                "suggestion": self.defect_statistics.suggestion,
            },
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "defects": [d.to_dict() for d in self.defects],
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
        }


# ============================================================================
# 上下文数据类
# ============================================================================

@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: str
    conversation_history: List[Dict[str, str]]
    family_devices: Dict[str, Any]
    device_status: Dict[str, Any]
    loop_step: int = 0
    current_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "conversation_history": self.conversation_history,
            "family_devices": self.family_devices,
            "device_status": self.device_status,
            "loop_step": self.loop_step,
            "current_query": self.current_query,
        }


@dataclass
class ProgressContext:
    """推进上下文"""
    current_case_index: int
    total_cases: int
    noise_retry_count: int
    current_state: TaskState
    last_result: Optional[JudgeResult] = None
    error: Optional[Exception] = None