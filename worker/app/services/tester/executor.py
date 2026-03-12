"""
测试工程师服务 - 测试用例执行器

负责测试用例的执行，包括生成测试查询、记录设备状态等。
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    TestCase,
    TestResult,
    TestResultStatus,
    ExecutionResult,
    ExecutionContext,
    TesterConfig,
)

logger = logging.getLogger(__name__)


class TestExecutor:
    """测试用例执行器

    负责测试用例的执行逻辑，包括：
    - 生成测试查询语句
    - 记录设备状态（执行前后）
    - 构造测试数据
    """

    def __init__(
        self,
        config: Optional[TesterConfig] = None,
        backend_service=None
    ):
        """初始化执行器

        Args:
            config: 测试服务配置
            backend_service: 后端服务实例（用于调用App）
        """
        self.config = config or TesterConfig()
        self.backend_service = backend_service

    async def generate_test_query(
        self,
        test_case: TestCase,
        context: ExecutionContext
    ) -> str:
        """生成测试查询语句

        根据当前测试用例和执行上下文，生成下一个测试查询语句。

        Args:
            test_case: 当前测试用例
            context: 执行上下文

        Returns:
            生成的测试查询语句
        """
        try:
            # 格式化测试用例上下文
            case_context = self._format_case_context(test_case)

            # 格式化设备列表上下文
            devices_context = self._format_devices_context(context.family_devices)

            # 格式化对话历史上下文
            history_context = self._format_history_context(context.conversation_history)

            # 构建消息
            message = "\n\n".join([
                "**当前测试用例**：",
                case_context,
                "**家庭设备列表**：",
                devices_context,
                "**对话历史**：",
                history_context,
                "**当前设备状态**：",
                json.dumps(context.device_status, ensure_ascii=False, indent=2) if context.device_status else "无",
            ])

            # 调用查询生成器App
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.config.query_generator_app_id,
                    message=message,
                )

                if result.success and result.content:
                    try:
                        parsed = json.loads(result.content)
                        query = parsed.get('user_input', '')
                        if query:
                            logger.info(f"Generated query for case {test_case.id}: {query}")
                            return query
                    except json.JSONDecodeError:
                        logger.warning(f"Query generator returned non-JSON: {result.content[:100]}")

            # 如果App调用失败，使用默认逻辑
            return self._generate_default_query(test_case, context)

        except Exception as e:
            logger.error(f"Error generating test query: {e}")
            return self._generate_default_query(test_case, context)

    def _generate_default_query(
        self,
        test_case: TestCase,
        context: ExecutionContext
    ) -> str:
        """生成默认测试查询

        当App调用失败时使用简单的规则生成查询。

        Args:
            test_case: 当前测试用例
            context: 执行上下文

        Returns:
            默认查询语句
        """
        # 根据用例标题生成简单查询
        title = test_case.title

        if "打开" in title and "灯" in title:
            return "打开一体机灯"
        elif "关闭" in title and "灯" in title:
            return "关闭一体机灯"
        else:
            # 使用步骤中的第一条作为查询
            if test_case.steps:
                step = test_case.steps[0]
                # 提取引号中的内容
                import re
                match = re.search(r'"([^"]+)"', step)
                if match:
                    return match.group(1)

        return f"执行测试用例 {test_case.id}"

    async def record_device_status_before(
        self,
        device_guids: List[str],
        iot_service
    ) -> Dict[str, Any]:
        """执行前记录设备状态

        Args:
            device_guids: 设备GUID列表
            iot_service: IOT服务实例

        Returns:
            设备状态字典 {device_guid: status}
        """
        status = {}
        try:
            for device_guid in device_guids:
                result = await iot_service.get_device_status(
                    device_guid,
                    iot_service.token
                )
                if result.get('success') or result.get('rc') == 0:
                    status[device_guid] = result.get('data', [])
                    logger.debug(f"Recorded before status for device {device_guid}")
        except Exception as e:
            logger.error(f"Error recording device status before: {e}")

        return status

    async def record_device_status_after(
        self,
        device_guids: List[str],
        iot_service
    ) -> Dict[str, Any]:
        """执行后记录设备状态

        Args:
            device_guids: 设备GUID列表
            iot_service: IOT服务实例

        Returns:
            设备状态字典 {device_guid: status}
        """
        return await self.record_device_status_before(device_guids, iot_service)

    def construct_test_data(
        self,
        test_case: TestCase,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """构造测试数据

        Args:
            test_case: 当前测试用例
            context: 执行上下文

        Returns:
            测试数据字典
        """
        return {
            "case_id": test_case.id,
            "case_title": test_case.title,
            "case_type": test_case.type.value,
            "device_guids": test_case.device_guids,
            "expected_results": test_case.expect_results,
            "current_query": context.current_query,
            "loop_step": context.loop_step,
            "session_id": context.session_id,
        }

    def _format_case_context(self, test_case: TestCase) -> str:
        """格式化测试用例上下文"""
        headers = ["id", "module", "title", "type", "preconditions", "device_guids",
                   "steps", "expect_results", "actual_results", "test_result"]
        header_names = {
            "id": "用例ID",
            "module": "模块",
            "title": "标题",
            "type": "类型",
            "preconditions": "前置条件",
            "device_guids": "要操控设备的deviceGuid",
            "steps": "测试步骤",
            "expect_results": "预期结果",
            "actual_results": "实际结果",
            "test_result": "测试结果"
        }

        lines = ["| " + " | ".join([header_names.get(h, h) for h in headers]) + " |"]
        lines.append("|" + "|".join([":---" for _ in headers]) + "|")

        row_values = []
        for h in headers:
            value = getattr(test_case, h, 'N/A')
            if value is None:
                value = 'N/A'
            elif isinstance(value, list):
                value = '<br>'.join(str(v) for v in value)
            elif hasattr(value, 'value'):
                value = value.value
            else:
                value = str(value)
            row_values.append(value)
        lines.append("| " + " | ".join(row_values) + " |")

        return "\n".join(lines)

    def _format_devices_context(self, family_devices: Dict[str, Any]) -> str:
        """格式化设备列表上下文"""
        if not family_devices:
            return "无设备"

        lines = ["| 设备GUID | 设备类型 | 设备标准型号 | 设备昵称 | 设备状态 |",
                 "|:---------|:---------|:---------|:---------|:---------|"]

        for device_guid, device in family_devices.items():
            nick_name = device.get('nick_name', 'N/A') or 'N/A'
            category_name = device.get('category_name', 'N/A') or 'N/A'
            display_type = device.get('display_type', 'N/A') or 'N/A'
            device_status = device.get('device_status')
            device_status = '在线' if device_status else '离线'
            lines.append(f"| {device_guid} | {category_name} | {display_type} | {nick_name} | {device_status} |")

        return "\n".join(lines)

    def _format_history_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """格式化对话历史上下文"""
        if not conversation_history:
            return "无历史对话"

        lines = []
        for msg in conversation_history:
            role_name = "测试员" if msg.get('role') == 'user' else "被测系统"
            lines.append(f"- {role_name}: {msg.get('content', '')}")

        return "\n".join(lines)

    async def execute_step(
        self,
        test_case: TestCase,
        step_index: int,
        context: ExecutionContext
    ) -> ExecutionResult:
        """执行单个测试步骤

        Args:
            test_case: 当前测试用例
            step_index: 步骤索引
            context: 执行上下文

        Returns:
            执行结果
        """
        if step_index >= len(test_case.steps):
            return ExecutionResult(
                success=False,
                asr_text="",
                ai_response="",
                error_message=f"Step index {step_index} out of range"
            )

        # 生成当前步骤的查询
        query = await self.generate_test_query(test_case, context)

        return ExecutionResult(
            success=True,
            asr_text=query,  # 实际应该从Agent获取ASR结果
            ai_response="",   # 实际应该从Agent获取AI响应
        )

    def create_test_result(
        self,
        test_case: TestCase,
        execution_result: ExecutionResult,
        device_status_before: Dict,
        device_status_after: Dict,
        duration_seconds: float
    ) -> TestResult:
        """创建测试结果对象

        Args:
            test_case: 测试用例
            execution_result: 执行结果
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态
            duration_seconds: 执行时长

        Returns:
            测试结果对象
        """
        return TestResult(
            case_id=test_case.id,
            status=TestResultStatus.NOT_RUN,  # 待评判后更新
            actual_results=[],
            execution_time=datetime.now(),
            duration_seconds=duration_seconds,
            device_status_before=device_status_before,
            device_status_after=device_status_after,
            asr_text=execution_result.asr_text,
            ai_response=execution_result.ai_response,
            error_message=execution_result.error_message,
        )