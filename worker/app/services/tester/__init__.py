"""
测试工程师服务模块

提供测试用例管理、测试执行、结果评判、缺陷跟踪、报告生成等功能。
"""

from .models import (
    TestCase,
    TestCaseType,
    TestResult,
    TestResultStatus,
    TestReport,
    Defect,
    DefectType,
    Severity,
    JudgeResult,
    ExecutionResult,
    TaskProgress,
    TaskState,
    NextAction,
    TesterConfig,
    TestCaseStatistics,
    DefectStatistics,
    ExecutionContext,
    SessionInfo,
    ProgressContext,
)
from .case_manager import TestCaseManager, DEFAULT_TEST_CASES
from .executor import TestExecutor
from .judge import TestJudge
from .progressor import TaskProgressor
from .defect_tracker import DefectTracker
from .reporter import TestReporter

__all__ = [
    # 数据类
    "TestCase",
    "TestCaseType",
    "TestResult",
    "TestResultStatus",
    "TestReport",
    "Defect",
    "DefectType",
    "Severity",
    "JudgeResult",
    "ExecutionResult",
    "TaskProgress",
    "TaskState",
    "NextAction",
    "TesterConfig",
    "TestCaseStatistics",
    "DefectStatistics",
    "ExecutionContext",
    "SessionInfo",
    "ProgressContext",
    # 服务类
    "TestCaseManager",
    "TestExecutor",
    "TestJudge",
    "TaskProgressor",
    "DefectTracker",
    "TestReporter",
    # 常量
    "DEFAULT_TEST_CASES",
]