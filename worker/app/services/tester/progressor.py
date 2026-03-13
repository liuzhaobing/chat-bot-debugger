"""
测试工程师服务 - 测试任务推进器

负责测试任务的推进逻辑，包括状态机管理、噪音重试、完成判断等。
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from .models import (
    TaskState,
    NextAction,
    TaskProgress,
    ProgressContext,
    JudgeResult,
    TesterConfig,
    TestCase,
    TestResultStatus,
    CompletionCheckResult,
)

logger = logging.getLogger(__name__)


class TaskProgressor:
    """测试任务推进器

    管理测试任务的执行状态和推进逻辑，包括：
    - 状态机管理
    - 噪音重试逻辑
    - 测试完成判断
    - 下一步行动决策
    - 大模型验证完成状态
    """

    # 用例完成验证 App ID
    COMPLETION_VERIFIER_APP_ID = "completion_verifier_app"

    def __init__(self, config: Optional[TesterConfig] = None, backend_service=None):
        """初始化推进器

        Args:
            config: 测试服务配置
            backend_service: 后端服务实例（用于调用 App）
        """
        self.config = config or TesterConfig()
        self.backend_service = backend_service
        self.state = TaskState.READY
        self.noise_retry_count = 0
        self.execution_retry_count = 0
        self.start_time: Optional[datetime] = None
        self.last_action_time: Optional[datetime] = None

    def initialize(self) -> None:
        """初始化推进器状态"""
        self.state = TaskState.READY
        self.noise_retry_count = 0
        self.execution_retry_count = 0
        self.start_time = datetime.now()
        self.last_action_time = datetime.now()
        logger.info("Task progressor initialized")

    def determine_next_action(self, context: ProgressContext) -> NextAction:
        """决定下一步行动

        根据当前上下文决定下一步应该做什么。
        注意：noise 重试由 on_noise_detected 方法单独处理，不在此方法中判断。

        Args:
            context: 推进上下文

        Returns:
            下一步行动
        """
        # 检查是否有错误
        if context.error:
            return self._handle_error(context.error)

        # 检查评判结果
        if context.last_result:
            if context.last_result.suggested_action == 'end_conversation':
                if context.current_case_index < context.total_cases - 1:
                    return NextAction.NEXT_CASE
                else:
                    return NextAction.STOP

            if not context.last_result.should_continue:
                if context.current_case_index < context.total_cases - 1:
                    return NextAction.NEXT_CASE
                else:
                    return NextAction.STOP

        # 检查是否全部完成
        if context.current_case_index >= context.total_cases - 1:
            return NextAction.STOP

        # 默认推进到下一个用例
        return NextAction.NEXT_CASE

    def _handle_error(self, error: Exception) -> NextAction:
        """处理错误

        Args:
            error: 异常对象

        Returns:
            下一步行动
        """
        error_str = str(error).lower()

        # 网络超时等临时性错误，可以重试
        if any(kw in error_str for kw in ['timeout', '超时', 'network', '网络']):
            if self.execution_retry_count < self.config.max_execution_retry:
                self.execution_retry_count += 1
                return NextAction.RETRY

        # 其他错误，跳过当前用例
        return NextAction.NEXT_CASE

    def should_retry_noise(self) -> bool:
        """判断是否应该重试噪音

        Returns:
            是否应该重试
        """
        return self.noise_retry_count < self.config.max_noise_retry

    def increment_noise_retry(self) -> int:
        """增加噪音重试计数

        Returns:
            当前重试次数
        """
        self.noise_retry_count += 1
        self.state = TaskState.RETRYING
        logger.info(f"Noise retry count: {self.noise_retry_count}/{self.config.max_noise_retry + 1}")
        return self.noise_retry_count

    def reset_noise_retry(self) -> None:
        """重置噪音重试计数"""
        self.noise_retry_count = 0
        logger.debug("Noise retry count reset")

    def can_retry_noise(self) -> bool:
        """检查是否还能重试噪音

        重试逻辑说明：
        - max_noise_retry = 2 表示最多重试 2 次
        - 判断条件是 noise_retry_count < max_noise_retry
        - 在 on_noise_detected 中会先判断再增加计数

        Returns:
            是否还能重试
        """
        return self.noise_retry_count < self.config.max_noise_retry

    def advance_to_next_case(self) -> bool:
        """推进到下一个用例

        Returns:
            推进后的噪音重试计数是否重置（总是True）
        """
        self.state = TaskState.EXECUTING
        self.noise_retry_count = 0
        self.execution_retry_count = 0
        self.last_action_time = datetime.now()
        logger.info("Advanced to next test case")
        return True

    def get_unexecuted_case_indices(
        self,
        test_cases: List[TestCase],
        current_index: int
    ) -> List[int]:
        """获取未执行用例的 index 列表（工程化判断）

        Args:
            test_cases: 测试用例列表
            current_index: 当前用例索引

        Returns:
            未执行用例的 index 列表（空列表表示全部完成）
        """
        unexecuted = []
        for i, case in enumerate(test_cases):
            if case.test_result == TestResultStatus.NOT_RUN:
                unexecuted.append(i)
        return unexecuted

    async def verify_completion_with_llm(
        self,
        test_cases: List[TestCase]
    ) -> Tuple[bool, List[int], str]:
        """大模型验证是否所有用例都已完成

        Args:
            test_cases: 测试用例列表

        Returns:
            (是否全部完成, 未执行索引列表, 分析结果)
        """
        # 构建 markdown 表格
        table = self._build_case_table(test_cases)

        # 调用大模型
        result = await self._call_verifier_app(table)

        return result

    def _build_case_table(self, test_cases: List[TestCase]) -> str:
        """构建测试用例 markdown 表格

        格式：
        | index | title | test_result |
        |-------|-------|-------------|
        | 0     | xxx   | Pass        |
        | 1     | xxx   | NotRun      |
        """
        lines = ["| index | title | test_result |", "|-------|-------|-------------|"]
        for i, case in enumerate(test_cases):
            lines.append(f"| {i} | {case.title} | {case.test_result.value} |")
        return "\n".join(lines)

    async def _call_verifier_app(self, table: str) -> Tuple[bool, List[int], str]:
        """调用大模型验证 App

        Args:
            table: 测试用例表格

        Returns:
            (是否全部完成, 未执行索引列表, 分析结果)
        """
        try:
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.COMPLETION_VERIFIER_APP_ID,
                    message=f"请分析以下测试用例执行情况，判断是否全部完成：\n\n{table}",
                    parameters={
                        "case_table": table,
                    }
                )

                if result.success and result.content:
                    try:
                        parsed_result = json.loads(result.content)
                        completed = parsed_result.get("completed", False)
                        unexecuted_indices = parsed_result.get("unexecuted_indices", [])
                        analysis = parsed_result.get("analysis", "")
                        return (completed, unexecuted_indices, analysis)
                    except json.JSONDecodeError:
                        logger.warning(f"Completion verifier returned non-JSON content")
                        return self._get_default_verification_result(table)
                else:
                    logger.warning(f"Completion verifier app call failed: {result.error}")
                    return self._get_default_verification_result(table)
            else:
                return self._get_default_verification_result(table)

        except Exception as e:
            logger.error(f"Completion verifier app call failed: {e}")
            return self._get_default_verification_result(table)

    def _get_default_verification_result(self, table: str) -> Tuple[bool, List[int], str]:
        """获取默认的验证结果（当 App 调用失败时）

        Args:
            table: 测试用例表格

        Returns:
            (是否全部完成, 未执行索引列表, 分析结果)
        """
        # 简单解析表格，检查是否有 NotRun 状态
        has_not_run = "NotRun" in table
        if has_not_run:
            # 尝试找出 NotRun 的索引
            unexecuted = []
            lines = table.split("\n")
            for line in lines[2:]:  # 跳过表头
                if "NotRun" in line:
                    parts = line.split("|")
                    if len(parts) > 1:
                        try:
                            idx = int(parts[1].strip())
                            unexecuted.append(idx)
                        except ValueError:
                            pass
            return (False, unexecuted, "默认验证：存在未执行的用例")
        else:
            return (True, [], "默认验证：所有用例已执行")

    def set_state(self, state: TaskState) -> None:
        """设置任务状态

        Args:
            state: 新状态
        """
        self.state = state
        logger.debug(f"Task state changed to: {state.value}")

    def get_state(self) -> TaskState:
        """获取当前状态

        Returns:
            当前状态
        """
        return self.state

    def create_progress(
        self,
        action: NextAction,
        current_index: int,
        total_cases: int,
        message: str = ""
    ) -> TaskProgress:
        """创建任务进度对象

        Args:
            action: 下一步行动
            current_index: 当前索引
            total_cases: 总用例数
            message: 进度消息

        Returns:
            任务进度对象
        """
        completed = action == NextAction.STOP or current_index >= total_cases

        return TaskProgress(
            action=action,
            current_case_index=current_index,
            total_cases=total_cases,
            message=message or self._get_default_message(action),
            state=self.state,
            completed=completed,
        )

    def _get_default_message(self, action: NextAction) -> str:
        """获取默认消息

        Args:
            action: 下一步行动

        Returns:
            默认消息
        """
        messages = {
            NextAction.RETRY: "重试当前测试步骤",
            NextAction.NEXT_CASE: "推进到下一个测试用例",
            NextAction.STOP: "测试任务已完成",
            NextAction.WAIT: "等待响应",
        }
        return messages.get(action, "")

    def stop(self) -> None:
        """停止任务"""
        self.state = TaskState.STOPPED
        logger.info("Task progressor stopped")

    def get_elapsed_seconds(self) -> float:
        """获取已用时间（秒）

        Returns:
            已用时间
        """
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            状态字典
        """
        return {
            "state": self.state.value,
            "noise_retry_count": self.noise_retry_count,
            "execution_retry_count": self.execution_retry_count,
            "elapsed_seconds": self.get_elapsed_seconds(),
        }