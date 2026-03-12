"""
测试工程师服务 - 主服务类

提供统一的测试工程师服务接口，协调各个子模块完成测试任务。
从 agent_service.py 中剥离测试相关功能。
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from app.config import settings

from .tester.models import (
    # 数据类
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
from .tester.case_manager import TestCaseManager, DEFAULT_TEST_CASES
from .tester.executor import TestExecutor
from .tester.judge import TestJudge
from .tester.progressor import TaskProgressor
from .tester.defect_tracker import DefectTracker
from .tester.reporter import TestReporter

logger = logging.getLogger(__name__)

# 特殊标记：噪音重试耗尽后跳过当前轮次，直接生成下一个 query
SKIP_TO_NEXT_QUERY = "<skip_to_next_query>"


class TesterService:
    """测试工程师服务

    提供完整的测试工程师功能，包括：
    1. 测试用例设计
    2. 测试用例执行
    3. 测试执行结果评判
    4. 测试任务推进
    5. 测试结果记录
    6. 测试完成判断
    7. 缺陷记录
    8. 测试报告输出

    从 agent_service.py 剥离的功能：
    - 测试用例管理（test_cases, current_case_index, current_case）
    - 测试查询生成（generate_next_query, call_query_generator_app）
    - 测试结果评判（call_judge_app）
    - 任务推进逻辑（noise_retry_count, current_case_index 推进）
    - 对话历史管理（conversation_history）

    使用示例:
        tester = TesterService()
        await tester.initialize(session_id, iot_config)

        while not tester.is_testing_completed():
            query = await tester.get_next_test_query()
            # 执行测试...
            progress = await tester.process_execution_result(asr_text, before_status, after_status)

        report = await tester.finalize()
    """

    # App IDs - 从 agent_service.py 迁移
    JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"
    QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

    def __init__(
        self,
        config: Optional[TesterConfig] = None,
        backend_service=None,
        send_callback: Optional[Callable] = None,
        log_event_callback: Optional[Callable] = None
    ):
        """初始化测试工程师服务

        Args:
            config: 测试服务配置
            backend_service: 后端服务实例（用于调用App）
            send_callback: 消息发送回调函数
            log_event_callback: 日志事件回调函数
        """
        self.config = config or TesterConfig()
        self.backend_service = backend_service
        self.send_callback = send_callback or (lambda *args: None)
        self.log_event_callback = log_event_callback or (lambda *args: None)

        # 初始化子模块
        self.case_manager = TestCaseManager(self.config)
        self.executor = TestExecutor(self.config, backend_service)
        self.judge = TestJudge(self.config, backend_service)
        self.progressor = TaskProgressor(self.config)
        self.defect_tracker = DefectTracker()
        self.reporter = TestReporter()

        # 会话信息
        self.session_id: Optional[str] = None
        self.session_info: Optional[SessionInfo] = None

        # 设备状态
        self.device_status_before: Dict[str, Any] = {}
        self.device_status_after: Dict[str, Any] = {}

        # 执行上下文
        self.execution_context: Optional[ExecutionContext] = None

        # 执行统计
        self.total_queries_generated: int = 0
        self.total_cases_executed: int = 0

        # 对话历史管理（从 agent_service.py 迁移）
        self.conversation_history: List[Dict[str, str]] = []
        self.max_conversation_history_length = 20

        # 家庭设备列表（从 agent_service.py 迁移）
        self.family_devices: Dict[str, Any] = {}

    # ========================================================================
    # 初始化和配置
    # ========================================================================

    async def initialize(
        self,
        session_id: str,
        iot_config: Optional[Dict[str, str]] = None,
        family_devices: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化测试服务

        Args:
            session_id: 会话ID
            iot_config: IOT配置
            family_devices: 家庭设备列表
        """
        self.session_id = session_id

        # 初始化会话信息
        self.session_info = SessionInfo(
            session_id=session_id,
            start_time=datetime.now(),
            iot_env=iot_config.get('env', 'test') if iot_config else 'test',
        )

        # 初始化推进器
        self.progressor.initialize()

        # 初始化执行上下文
        self.execution_context = ExecutionContext(
            session_id=session_id,
            conversation_history=[],
            family_devices=family_devices or {},
            device_status={},
        )

        # 设置家庭设备
        self.family_devices = family_devices or {}

        logger.info(f"TesterService initialized for session {session_id}")
        await self._send_callback('status', '测试服务已初始化')

    def set_family_devices(self, family_devices: Dict[str, Any]) -> None:
        """设置家庭设备列表

        Args:
            family_devices: 家庭设备字典
        """
        self.family_devices = family_devices
        if self.execution_context:
            self.execution_context.family_devices = family_devices

    async def load_test_cases(self, source: str) -> int:
        """加载测试用例

        Args:
            source: 用例文件路径

        Returns:
            加载的用例数量
        """
        count = await self.case_manager.load_cases(source)
        await self._send_callback('log', f'加载了 {count} 个测试用例')
        return count

    # ========================================================================
    # 1. 测试用例设计
    # ========================================================================

    async def design_test_cases(
        self,
        scenario: str,
        llm_service=None
    ) -> List[TestCase]:
        """设计测试用例

        根据场景描述自动生成测试用例。

        Args:
            scenario: 场景描述
            llm_service: LLM服务实例

        Returns:
            生成的测试用例列表
        """
        cases = await self.case_manager.design_cases_from_scenario(scenario, llm_service)
        await self._send_callback('log', f'根据场景 "{scenario}" 生成了 {len(cases)} 个测试用例')
        return cases

    def get_test_cases(self) -> List[TestCase]:
        """获取所有测试用例

        Returns:
            测试用例列表
        """
        return self.case_manager.get_all_cases()

    def get_current_test_case(self) -> Optional[TestCase]:
        """获取当前测试用例

        Returns:
            当前测试用例
        """
        return self.case_manager.get_current_case()

    def get_current_case_index(self) -> int:
        """获取当前测试用例索引

        Returns:
            当前索引
        """
        return self.case_manager.current_index

    # ========================================================================
    # 2. 测试用例执行
    # ========================================================================

    async def get_next_test_query(self) -> Optional[str]:
        """获取下一个测试查询语句

        Returns:
            测试查询语句，如果没有更多用例则返回None
        """
        current_case = self.case_manager.get_current_case()
        if not current_case:
            logger.info("No more test cases to execute")
            return None

        # 生成测试查询
        query = await self._generate_next_query({'should_continue': True}, "")

        if query:
            self.total_queries_generated += 1

            # 更新执行上下文
            if self.execution_context:
                self.execution_context.current_query = query

            logger.info(f"Generated test query for case {current_case.id}: {query}")
            await self._send_callback('test_query', {
                'case_id': current_case.id,
                'query': query,
            })

        return query

    async def _generate_next_query(
        self,
        judge_result: Dict[str, Any],
        asr_text: str
    ) -> str:
        """根据判断结果生成下一个查询

        从 agent_service.py 的 generate_next_query 迁移

        Args:
            judge_result: 判断结果
            asr_text: ASR识别文本

        Returns:
            生成的查询语句
        """
        current_case = self.case_manager.get_current_case()
        if not current_case:
            return ""

        try:
            if not judge_result.get('should_continue', True):
                return ""

            suggested_action = judge_result.get('suggested_action', '')
            if suggested_action == 'end_conversation':
                return ""

            # 使用全局对话历史
            conversation_history_context = self._get_conversation_history_context()

            # 使用家庭设备列表上下文
            family_devices_context = self._get_family_devices_context()

            # 格式化当前测试用例为 markdown 表格
            current_case_context = self._format_current_case_context()

            query_result = await self._call_query_generator_app(
                message="\n\n".join([
                    "**当前测试用例**：", current_case_context,
                    "**家庭设备列表**：", family_devices_context,
                    "**对话历史**：", conversation_history_context,
                    "**当前设备状态**：", "[]"
                ])
            )

            await self._log_event('query_generated', json.dumps(query_result, ensure_ascii=False), {
                'app_id': self.QUERY_GENERATOR_APP_ID,
            })

            await self._send_callback('query_generated', query_result)

            if not query_result.get('should_continue', True):
                # 推进到下一个用例
                advanced = self.case_manager.advance_to_next_case()
                if advanced:
                    next_case = self.case_manager.get_current_case()
                    await self._send_callback('log', f'准备加载下一条测试用例：{self.case_manager.current_index + 1}.{next_case.title if next_case else ""}')

            next_query = query_result.get('user_input', '')

            return next_query

        except Exception as e:
            logger.error(f"Error generating next query: {e}")
            return "让我继续为您检查设备状态"

    async def _call_query_generator_app(self, message: Any) -> Dict[str, Any]:
        """调用DeviceControlGenerator APP生成下一轮测试query

        从 agent_service.py 迁移

        Args:
            message: 输入信息

        Returns:
            查询生成结果字典
        """
        try:
            # 使用 BackendService 调用 QueryGenerator App
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.QUERY_GENERATOR_APP_ID,
                    message=message,
                )

                if result.success and result.content:
                    try:
                        parsed_result = json.loads(result.content)
                        await self._log_event('app_call', json.dumps(parsed_result, ensure_ascii=False), {
                            'app_id': self.QUERY_GENERATOR_APP_ID,
                            'latency_ms': result.latency_ms
                        })
                        return parsed_result
                    except json.JSONDecodeError:
                        logger.warning(f"QueryGenerator app returned non-JSON content: {result.content[:100]}")
                        return await self._get_mock_query_result(message)
                else:
                    logger.warning(f"QueryGenerator app call failed: {result.error}")
                    return await self._get_mock_query_result(message)
            else:
                return await self._get_mock_query_result(message)

        except Exception as e:
            logger.error(f"Query generator app call failed: {e}")
            return await self._get_mock_query_result(message)

    async def _get_mock_query_result(self, test_scenario: str) -> Dict[str, Any]:
        """生成模拟的query生成结果"""
        return {
            'user_input': '打开一体机灯',
            'target_device_guid': '38-i750411c84f366',
            'target_device_name': '一体机',
            'expected_device_changes': {
                'lightSwitch': '1',
                'lightSwitch_text': '开灯'
            },
            'expected_response_keywords': ['已打开', '灯', '开启'],
            'expected_response_semantic': '确认灯已经打开',
            'test_intent': '测试灯光控制功能',
            'should_continue': True,
            'reasoning': '使用模拟数据生成测试query'
        }

    # ========================================================================
    # 3. 测试执行结果评判
    # ========================================================================

    async def judge_test_result(
        self,
        asr_text: str,
        device_status_before: Optional[Dict] = None,
        device_status_after: Optional[Dict] = None
    ) -> JudgeResult:
        """评判测试结果

        Args:
            asr_text: ASR识别文本
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态

        Returns:
            评判结果
        """
        current_case = self.case_manager.get_current_case()
        if not current_case:
            return JudgeResult(
                case_id="",
                is_pass=False,
                confidence=0.0,
                analysis="没有当前测试用例",
                should_continue=False,
            )

        # 使用传入的状态或实例状态
        before = device_status_before or self.device_status_before
        after = device_status_after or self.device_status_after

        # 构建执行结果
        execution_result = ExecutionResult(
            success=True,
            asr_text=asr_text,
            ai_response="",
        )

        # 评判结果
        judge_result = await self.judge.judge(
            current_case,
            execution_result,
            before,
            after
        )

        logger.info(f"Judge result for {current_case.id}: {'PASS' if judge_result.is_pass else 'FAIL'}")
        await self._send_callback('judge_result', judge_result.to_dict())

        return judge_result

    async def call_judge_app(
        self,
        asr_text: str,
        current_status: Dict,
        previous_status: Dict
    ) -> Dict[str, Any]:
        """调用判断App分析ASR结果和设备状态变化

        从 agent_service.py 迁移

        Args:
            asr_text: ASR识别出的文本
            current_status: 当前设备状态
            previous_status: 之前的设备状态

        Returns:
            分析结果字典
        """
        try:
            # 检查是否使用 mock 模式
            if settings.dev_mock_external_services:
                return await self._get_mock_judge_result(asr_text)

            # 使用 BackendService 调用 Judge App
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.JUDGE_APP_ID,
                    message=f"分析用户语音: {asr_text}",
                    parameters={
                        "asr_text": asr_text,
                        "current_device_status": current_status or {},
                        "previous_device_status": previous_status or {}
                    }
                )

                if result.success and result.content:
                    try:
                        parsed_result = json.loads(result.content)
                        await self._log_event('app_call', json.dumps(parsed_result, ensure_ascii=False), {
                            'app_id': self.JUDGE_APP_ID,
                            'latency_ms': result.latency_ms
                        })
                        return parsed_result
                    except json.JSONDecodeError:
                        logger.warning(f"Judge app returned non-JSON content: {result.content[:100]}")
                        return await self._get_mock_judge_result(asr_text)
                else:
                    logger.warning(f"Judge app call failed: {result.error}")
                    return await self._get_mock_judge_result(asr_text)
            else:
                return await self._get_mock_judge_result(asr_text)

        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return await self._get_mock_judge_result(asr_text)

    async def _get_mock_judge_result(self, asr_text: str) -> Dict[str, Any]:
        """生成模拟的判断结果"""
        return {
            'analysis': f'分析用户语音: {asr_text}',
            'confidence': 0.75,
            'should_continue': True,
            'suggested_action': 'continue_conversation',
            'detected_intent': 'device_query',
            'device_mentioned': True
        }

    # ========================================================================
    # 4. 测试任务推进
    # ========================================================================

    async def process_execution_result(
        self,
        asr_text: str,
        device_status_before: Optional[Dict] = None,
        device_status_after: Optional[Dict] = None
    ) -> TaskProgress:
        """处理执行结果并推进任务

        这是核心方法，完成：评判 -> 记录 -> 推进

        Args:
            asr_text: ASR识别文本
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态

        Returns:
            任务进度
        """
        # 评判结果
        judge_result = await self.judge_test_result(
            asr_text,
            device_status_before,
            device_status_after
        )

        # 更新用例状态
        current_case = self.case_manager.get_current_case()
        if current_case:
            # 确定实际结果
            actual_results = []
            if judge_result.is_pass:
                actual_results = [f"测试通过: {judge_result.analysis}"]
            else:
                actual_results = [f"测试失败: {judge_result.analysis}"]

            # 更新用例结果
            test_status = self.judge.determine_test_status(judge_result)
            self.case_manager.update_case_result(
                current_case.id,
                test_status,
                actual_results,
                judge_result.analysis if not judge_result.is_pass else None
            )

            # 如果失败，记录缺陷
            if not judge_result.is_pass:
                defect_id = self.defect_tracker.auto_create_from_test_result(
                    current_case,
                    {
                        'asr_text': asr_text,
                        'judge_result': judge_result.to_dict(),
                        'device_status_before': device_status_before,
                        'device_status_after': device_status_after,
                    }
                )
                if defect_id:
                    judge_result.defects.append(defect_id)

        # 决定下一步行动
        action = self._determine_next_action(judge_result)

        # 执行推进
        progress = self._execute_progression(action, judge_result)

        self.total_cases_executed += 1

        await self._send_callback('task_progress', progress.to_dict())
        return progress

    def _determine_next_action(self, judge_result: JudgeResult) -> NextAction:
        """决定下一步行动"""
        context = ProgressContext(
            current_case_index=self.case_manager.current_index,
            total_cases=len(self.case_manager.test_cases),
            noise_retry_count=self.progressor.noise_retry_count,
            current_state=self.progressor.state,
            last_result=judge_result,
        )
        return self.progressor.determine_next_action(context)

    def _execute_progression(
        self,
        action: NextAction,
        judge_result: JudgeResult
    ) -> TaskProgress:
        """执行推进"""
        current_index = self.case_manager.current_index
        total_cases = len(self.case_manager.test_cases)

        if action == NextAction.NEXT_CASE:
            self.case_manager.advance_to_next_case()
            self.progressor.advance_to_next_case()
            current_index = self.case_manager.current_index
            message = f"推进到下一个测试用例 ({current_index + 1}/{total_cases})"

        elif action == NextAction.STOP:
            self.progressor.stop()
            message = "所有测试用例已完成"

        elif action == NextAction.RETRY:
            # RETRY 分支：noise 重试由 on_noise_detected 单独处理
            # 这里只设置消息，不再重复增加计数
            message = f"重试当前测试步骤 ({self.progressor.noise_retry_count}/{self.config.max_noise_retry + 1})"

        else:
            message = "等待下一步操作"

        return self.progressor.create_progress(
            action,
            current_index,
            total_cases,
            message
        )

    # ========================================================================
    # 5. 测试结果记录
    # ========================================================================

    async def record_result(
        self,
        case_id: str,
        status: TestResultStatus,
        actual_results: List[str],
        error_message: Optional[str] = None
    ) -> bool:
        """记录测试结果"""
        success = self.case_manager.update_case_result(
            case_id,
            status,
            actual_results,
            error_message
        )

        if success:
            await self._send_callback('test_result', {
                'case_id': case_id,
                'status': status.value,
                'actual_results': actual_results,
            })

        return success

    # ========================================================================
    # 6. 测试完成判断
    # ========================================================================

    def is_testing_completed(self) -> bool:
        """判断测试是否全部完成"""
        return self.progressor.is_all_completed(
            len(self.case_manager.test_cases),
            self.case_manager.current_index
        )

    def has_more_cases(self) -> bool:
        """检查是否还有更多测试用例"""
        return self.case_manager.has_more_cases()

    # ========================================================================
    # 7. 缺陷记录
    # ========================================================================

    async def record_defect(
        self,
        case_id: str,
        defect_type: DefectType,
        description: str,
        severity: Severity,
        device_guid: Optional[str] = None,
        evidence: Optional[Dict] = None
    ) -> str:
        """记录缺陷"""
        defect_id = self.defect_tracker.record_defect(
            case_id,
            defect_type,
            description,
            severity,
            device_guid,
            evidence
        )

        await self._send_callback('defect', {
            'defect_id': defect_id,
            'case_id': case_id,
            'type': defect_type.value,
            'severity': severity.value,
            'description': description,
        })

        return defect_id

    def get_defects(self) -> List[Defect]:
        """获取所有缺陷"""
        return self.defect_tracker.defects

    def get_defects_by_case(self, case_id: str) -> List[Defect]:
        """获取用例关联的缺陷"""
        return self.defect_tracker.get_defects_by_case(case_id)

    # ========================================================================
    # 8. 测试报告输出
    # ========================================================================

    async def generate_report(self) -> TestReport:
        """生成测试报告"""
        if self.session_info:
            self.session_info.end_time = datetime.now()
            self.session_info.duration_seconds = (
                self.session_info.end_time - self.session_info.start_time
            ).total_seconds()

        report = await self.reporter.generate_report(
            self.case_manager.get_all_cases(),
            self.defect_tracker.defects,
            self.session_info
        )

        logger.info(f"Generated test report for session {self.session_id}")
        return report

    async def export_report(self, format: str = "markdown") -> str:
        """导出测试报告"""
        report = await self.generate_report()
        return await self.reporter.export_report(report, format)

    async def save_report(self, file_path: str, format: str = "markdown") -> bool:
        """保存测试报告到文件"""
        report = await self.generate_report()
        return await self.reporter.save_report(report, file_path, format)

    # ========================================================================
    # 对话历史管理（从 agent_service.py 迁移）
    # ========================================================================

    def add_to_conversation_history(self, role: str, content: str) -> None:
        """添加一条消息到对话历史

        Args:
            role: 消息角色 ('user' 或 'assistant')
            content: 消息内容
        """
        if not content or not content.strip():
            return

        self.conversation_history.append({
            'role': role,
            'content': content.strip()
        })

        # 保持对话历史不超过最大长度
        if len(self.conversation_history) > self.max_conversation_history_length:
            excess = len(self.conversation_history) - self.max_conversation_history_length
            self.conversation_history = self.conversation_history[excess:]

        # 同步到执行上下文
        if self.execution_context:
            self.execution_context.conversation_history = self.conversation_history.copy()

        logger.debug(f"Conversation history updated: {len(self.conversation_history)} messages")

    def _get_conversation_history_context(self) -> str:
        """获取对话历史的文本格式"""
        if not self.conversation_history:
            return "无历史对话"

        lines = []
        for msg in self.conversation_history:
            role_name = "测试员" if msg['role'] == 'user' else "被测系统"
            lines.append(f"- {role_name}: {msg['content']}")

        return "\n".join(lines)

    def _get_family_devices_context(self) -> str:
        """获取家庭设备列表的文本格式"""
        if not self.family_devices:
            return "无设备"

        lines = ["| 设备GUID | 设备类型 | 设备标准型号 | 设备昵称 | 设备状态 |", "|:---------|:---------|:---------|:---------|:---------|"]
        for device_guid, device in self.family_devices.items():
            nick_name = device.get('nick_name', 'N/A') or 'N/A'
            category_name = device.get('category_name', 'N/A') or 'N/A'
            display_type = device.get('display_type', 'N/A') or 'N/A'
            device_status = device.get('device_status')
            device_status = '在线' if device_status else '离线'
            lines.append(f"| {device_guid} | {category_name} | {display_type} | {nick_name} | {device_status} |")

        return "\n".join(lines)

    def _format_current_case_context(self) -> str:
        """格式化当前测试用例为 markdown 表格"""
        current_case = self.case_manager.get_current_case()
        if not current_case:
            return "无用例"

        # 定义表格列
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

        # 构建表头
        lines = ["| " + " | ".join([header_names.get(h, h) for h in headers]) + " |"]
        lines.append("|" + "|".join([":---" for _ in headers]) + "|")

        # 构建数据行
        row_values = []
        for h in headers:
            value = getattr(current_case, h, None)
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

    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []
        if self.execution_context:
            self.execution_context.conversation_history = []
        logger.info(f"Conversation history cleared for session {self.session_id}")

    # ========================================================================
    # 回调接口（供 Agent 调用）
    # ========================================================================

    async def on_noise_detected(self) -> NextAction:
        """噪音检测回调"""
        if self.progressor.can_retry_noise():
            self.progressor.increment_noise_retry()
            await self._send_callback('status', f"检测到噪音，准备重试 ({self.progressor.noise_retry_count}/{self.config.max_noise_retry + 1})")
            return NextAction.RETRY
        else:
            await self._send_callback('status', "噪音重试次数已用完，跳过当前用例")
            return NextAction.NEXT_CASE

    async def on_execution_error(self, error: Exception) -> NextAction:
        """执行错误回调"""
        logger.error(f"Execution error: {error}")
        await self._send_callback('error', f"执行错误: {str(error)}")

        error_str = str(error).lower()
        if any(kw in error_str for kw in ['timeout', '超时']):
            if self.progressor.execution_retry_count < self.config.max_execution_retry:
                self.progressor.execution_retry_count += 1
                return NextAction.RETRY

        return NextAction.NEXT_CASE

    async def on_query_executed(self, query: str, asr_text: str) -> None:
        """查询执行完成回调"""
        self.add_to_conversation_history('user', query)
        self.add_to_conversation_history('assistant', asr_text)

    # ========================================================================
    # 噪音重试相关（从 agent_service.py 迁移）
    # ========================================================================

    def get_noise_retry_count(self) -> int:
        """获取噪音重试次数"""
        return self.progressor.noise_retry_count

    def get_max_noise_retry(self) -> int:
        """获取最大噪音重试次数"""
        return self.config.max_noise_retry

    def can_retry_noise(self) -> bool:
        """是否还能重试噪音"""
        return self.progressor.can_retry_noise()

    def reset_noise_retry(self) -> None:
        """重置噪音重试计数"""
        self.progressor.reset_noise_retry()

    # ========================================================================
    # 统计信息
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        case_stats = self.case_manager.get_statistics()
        defect_stats = self.defect_tracker.get_statistics()

        return {
            'cases': {
                'total': case_stats.total,
                'passed': case_stats.passed,
                'failed': case_stats.failed,
                'blocked': case_stats.blocked,
                'skipped': case_stats.skipped,
                'not_run': case_stats.not_run,
                'pass_rate': case_stats.pass_rate,
            },
            'defects': {
                'total': defect_stats.total,
                'critical': defect_stats.critical,
                'major': defect_stats.major,
                'normal': defect_stats.normal,
                'minor': defect_stats.minor,
            },
            'execution': {
                'queries_generated': self.total_queries_generated,
                'cases_executed': self.total_cases_executed,
                'elapsed_seconds': self.progressor.get_elapsed_seconds(),
            },
            'progress': self.progressor.to_dict(),
        }

    # ========================================================================
    # 结束和清理
    # ========================================================================

    async def finalize(self) -> TestReport:
        """结束测试并生成报告"""
        logger.info(f"Finalizing test session {self.session_id}")

        report = await self.generate_report()

        stats = self.get_statistics()
        await self._send_callback('final_statistics', stats)

        return report

    async def stop(self) -> None:
        """停止测试服务"""
        self.progressor.stop()
        self.clear_conversation_history()
        logger.info(f"TesterService stopped for session {self.session_id}")
        await self._send_callback('status', '测试服务已停止')

    def reset(self) -> None:
        """重置测试服务状态"""
        self.case_manager.reset()
        self.defect_tracker.clear()
        self.progressor.initialize()
        self.device_status_before = {}
        self.device_status_after = {}
        self.total_queries_generated = 0
        self.total_cases_executed = 0
        self.clear_conversation_history()
        logger.info("TesterService reset")

    # ========================================================================
    # 内部方法
    # ========================================================================

    async def _send_callback(self, event_type: str, data: Any = None) -> None:
        """发送回调消息"""
        try:
            if self.send_callback:
                if asyncio.iscoroutinefunction(self.send_callback):
                    await self.send_callback(event_type, data)
                else:
                    self.send_callback(event_type, data)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    async def _log_event(self, log_type: str, content: str, metadata: Optional[dict] = None) -> None:
        """记录事件日志"""
        try:
            if self.log_event_callback:
                if asyncio.iscoroutinefunction(self.log_event_callback):
                    await self.log_event_callback(log_type, content, metadata)
                else:
                    self.log_event_callback(log_type, content, metadata)
        except Exception as e:
            logger.error(f"Log event error: {e}")