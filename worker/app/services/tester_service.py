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
from app.services.app_ids import (
    JUDGE_APP_ID,
    QUERY_GENERATOR_APP_ID,
    TEST_POINT_EXTRACTOR_APP_ID,
)
from app.services.verifiers import TestJudge

from .tester.models import (
    # 数据类
    TestPoint,
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
    CompletionCheckResult,
)
from .tester.case_manager import TestCaseManager, DEFAULT_TEST_CASES
from .tester.executor import TestExecutor
from .tester.progressor import TaskProgressor
from .tester.defect_tracker import DefectTracker
from .tester.reporter import TestReporter

logger = logging.getLogger(__name__)

# 特殊标记：噪音重试耗尽后跳过当前轮次，直接生成下一个 query
SKIP_TO_NEXT_QUERY = "<skip_to_next_query>"


class TesterService:
    """测试工程师服务

    提供完整的测试工程师功能，包括：
    0. 测试点提取 - 从场景描述中提取需要验证的功能点
    1. 测试用例设计 - 针对每个测试点设计具体的测试用例
    2. 测试用例执行
    3. 测试执行结果评判
    4. 测试任务推进
    5. 测试结果记录
    6. 测试完成判断
    7. 缺陷记录
    8. 测试报告输出

    测试流程：
    1. 先提取测试点（extract_test_points）
    2. 再针对每个测试点设计测试用例（design_test_case_for_point 或 design_all_test_cases_from_points）
    3. 执行测试用例（generate_test_query -> evaluate_round_result）
    4. 生成测试报告（finalize）

    从 agent_service.py 剥离的功能：
    - 测试用例管理（test_cases, current_case_index, current_case）
    - 测试查询生成（produce_query_content, call_query_generator_app）
    - 测试结果评判（call_judge_app）
    - 任务推进逻辑（noise_retry_count, current_case_index 推进）
    - 对话历史管理（conversation_history）

    使用示例:
        tester = TesterService()
        await tester.initialize(session_id, iot_config)

        # 先提取测试点
        test_points = await tester.extract_test_points(scenario_description)

        # 再设计测试用例
        test_cases = await tester.design_all_test_cases_from_points()

        while True:
            # 检查测试完成状态
            result = await tester.check_testing_completion()
            if result.completed:
                break

            query = await tester.generate_test_query()
            # 执行测试...
            progress = await tester.evaluate_round_result(asr_text, before_status, after_status)

        report = await tester.finalize()
    """

    # App IDs - 从 app_ids.py 导入
    JUDGE_APP_ID = JUDGE_APP_ID
    QUERY_GENERATOR_APP_ID = QUERY_GENERATOR_APP_ID
    TEST_POINT_EXTRACTOR_APP_ID = TEST_POINT_EXTRACTOR_APP_ID

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
        self.progressor = TaskProgressor(self.config, backend_service)
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

        # 测试点管理
        self.test_points: List[TestPoint] = []
        self.current_test_point_index: int = 0

    # ========================================================================
    # 初始化和配置
    # ========================================================================

    async def initialize(
        self,
        session_id: str,
        iot_config: Optional[Dict[str, str]] = None,
        family_devices: Optional[Dict[str, Any]] = None,
        tester_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化测试服务

        Args:
            session_id: 会话ID
            iot_config: IOT配置
            family_devices: 家庭设备列表
            tester_config: 测试配置（从 init_config 消息传入）
        """
        self.session_id = session_id

        # 应用 tester_config（如果提供）
        if tester_config:
            # 更新配置
            if tester_config.get('name'):
                self.config.name = tester_config['name']
            if tester_config.get('prd_content'):
                self.config.prd_content = tester_config['prd_content']
            if tester_config.get('tts_voice_id'):
                self.config.tts_voice_id = tester_config['tts_voice_id']
            if tester_config.get('iot_protocol_id'):
                self.config.iot_protocol_id = tester_config['iot_protocol_id']
            # App IDs
            if tester_config.get('judge_app_id'):
                self.config.judge_app_id = tester_config['judge_app_id']
            else:
                self.config.judge_app_id = self.JUDGE_APP_ID
            if tester_config.get('query_generator_app_id'):
                self.config.query_generator_app_id = tester_config['query_generator_app_id']
            else:
                self.config.query_generator_app_id = self.QUERY_GENERATOR_APP_ID
            # 重试配置
            if tester_config.get('max_noise_retry'):
                self.config.max_noise_retry = tester_config['max_noise_retry']
            if tester_config.get('max_execution_retry'):
                self.config.max_execution_retry = tester_config['max_execution_retry']
            # 超时配置
            if tester_config.get('case_timeout_seconds'):
                self.config.case_timeout_seconds = tester_config['case_timeout_seconds']
            if tester_config.get('total_timeout_seconds'):
                self.config.total_timeout_seconds = tester_config['total_timeout_seconds']

            logger.info(f"Applied tester_config: {tester_config}")

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
        # 同时设置 judge 的家庭设备
        if self.judge:
            self.judge.set_family_devices(family_devices)

    async def initialize_judge_protocols(self) -> None:
        """初始化评判器的设备协议

        在设置家庭设备后调用，用于加载设备协议以便在评判时获取属性说明。
        """
        if self.judge:
            await self.judge.initialize_protocols()

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
    # 0. 测试点提取
    # ========================================================================

    async def extract_test_points(
        self,
        scenario: str,
        llm_service=None
    ) -> List[TestPoint]:
        """从场景描述中提取测试点

        测试点是对测试需求的细化分解，先提取测试点，再针对每个测试点设计测试用例。

        Args:
            scenario: 场景描述（可以是需求文档、用户故事、功能描述等）
            llm_service: LLM服务实例（可选，用于智能提取测试点）

        Returns:
            提取的测试点列表
        """
        # 获取家庭设备上下文
        family_devices_context = self._get_family_devices_context()

        # 调用测试点提取App
        try:
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.TEST_POINT_EXTRACTOR_APP_ID,
                    message=f"从以下场景中提取测试点：\n\n{scenario}",
                    parameters={
                        "scenario": scenario,
                        "family_devices": family_devices_context,
                    }
                )

                if result.success and result.content:
                    try:
                        parsed_result = json.loads(result.content)
                        test_points_data = parsed_result.get("test_points", [])
                        self.test_points = [
                            TestPoint.from_dict(tp) for tp in test_points_data
                        ]
                    except json.JSONDecodeError:
                        logger.warning(f"TestPoint extractor returned non-JSON content")
                        self.test_points = await self._extract_test_points_locally(scenario)
                else:
                    logger.warning(f"TestPoint extractor app call failed: {result.error}")
                    self.test_points = await self._extract_test_points_locally(scenario)
            else:
                # 本地提取
                self.test_points = await self._extract_test_points_locally(scenario)

        except Exception as e:
            logger.error(f"Error extracting test points: {e}")
            self.test_points = await self._extract_test_points_locally(scenario)

        await self._send_callback('test_points_extracted', {
            'count': len(self.test_points),
            'test_points': [tp.to_dict() for tp in self.test_points],
        })
        await self._log_event('test_points', json.dumps([tp.to_dict() for tp in self.test_points], ensure_ascii=False))

        return self.test_points

    async def _extract_test_points_locally(self, scenario: str) -> List[TestPoint]:
        """本地提取测试点（模拟或简单规则）"""
        # 简单的测试点提取逻辑，实际项目中应调用LLM
        test_points = [
            TestPoint(
                id="TP001",
                module="设备控制",
                feature="灯光控制",
                description="测试灯光的开关控制功能",
                priority="high",
                test_type="functional",
                preconditions=["设备在线", "设备已绑定"],
                related_devices=[],
                acceptance_criteria=["语音指令能正确打开灯", "语音指令能正确关闭灯"],
                source=scenario,
            ),
            TestPoint(
                id="TP002",
                module="设备控制",
                feature="空调控制",
                description="测试空调的温度调节和模式切换功能",
                priority="high",
                test_type="functional",
                preconditions=["设备在线", "设备已绑定"],
                related_devices=[],
                acceptance_criteria=["能设置指定温度", "能切换工作模式"],
                source=scenario,
            ),
        ]
        return test_points

    def get_test_points(self) -> List[TestPoint]:
        """获取所有测试点"""
        return self.test_points

    def get_current_test_point(self) -> Optional[TestPoint]:
        """获取当前测试点"""
        if 0 <= self.current_test_point_index < len(self.test_points):
            return self.test_points[self.current_test_point_index]
        return None

    def advance_to_next_test_point(self) -> bool:
        """推进到下一个测试点"""
        if self.current_test_point_index < len(self.test_points) - 1:
            self.current_test_point_index += 1
            return True
        return False

    async def design_test_case_for_point(
        self,
        test_point: TestPoint,
        llm_service=None
    ) -> TestCase:
        """针对单个测试点设计测试用例

        Args:
            test_point: 测试点
            llm_service: LLM服务实例

        Returns:
            设计的测试用例
        """
        # 调用用例设计App或本地设计
        test_case = await self.case_manager.design_case_for_test_point(test_point, llm_service)

        # 关联测试点ID
        test_case.test_point_id = test_point.id

        await self._send_callback('test_case_designed', {
            'test_point_id': test_point.id,
            'test_case': test_case.to_dict(),
        })

        return test_case

    async def design_all_test_cases_from_points(
        self,
        llm_service=None
    ) -> List[TestCase]:
        """根据所有测试点设计测试用例

        遍历所有测试点，为每个测试点设计对应的测试用例。

        Args:
            llm_service: LLM服务实例

        Returns:
            设计的测试用例列表
        """
        if not self.test_points:
            logger.warning("No test points available. Please extract test points first.")
            return []

        test_cases = []
        for test_point in self.test_points:
            test_case = await self.design_test_case_for_point(test_point, llm_service)
            test_cases.append(test_case)

        # 添加到用例管理器
        for case in test_cases:
            self.case_manager.add_case(case)

        await self._send_callback('test_cases_designed', {
            'count': len(test_cases),
            'test_cases': [tc.to_dict() for tc in test_cases],
        })

        return test_cases

    # ========================================================================
    # 1. 测试用例设计
    # ========================================================================

    async def design_test_cases(
        self,
        prd: str,
        functions_md: Optional[str] = None,
        devices_md: Optional[str] = None,
        backend_service=None
    ) -> List[TestCase]:
        """设计测试用例

        根据PRD（产品需求文档）、设备功能说明和家庭设备信息自动生成测试用例。

        Args:
            prd: 产品需求文档内容
            functions_md: 设备功能说明（Markdown格式，可选）
            devices_md: 家庭设备信息（Markdown格式，可选）
            backend_service: BackendService 实例（可选）

        Returns:
            生成的测试用例列表
        """
        cases = await self.case_manager.design_cases_from_prd(prd, functions_md, devices_md, backend_service)
        await self._send_callback('log', f'根据PRD生成了 {len(cases)} 个测试用例')

        return cases

    async def design_test_cases_stream(
        self,
        prd: str,
        functions_md: Optional[str] = None,
        devices_md: Optional[str] = None,
        backend_service=None
    ) -> List[TestCase]:
        """流式设计测试用例

        根据PRD（产品需求文档）、设备功能说明和家庭设备信息流式生成测试用例。
        实时将生成的内容发送到前端。

        Args:
            prd: 产品需求文档内容
            functions_md: 设备功能说明（Markdown格式，可选）
            devices_md: 家庭设备信息（Markdown格式，可选）
            backend_service: BackendService 实例（可选）

        Returns:
            生成的测试用例列表
        """
        logger.info("[STREAM] design_test_cases_stream called - using streaming path")

        # 定义流式回调，将生成的内容发送到前端
        async def stream_callback(content: str):
            await self._send_callback('test_case_stream', {
                'content': content,
            })

        cases = await self.case_manager.design_cases_from_prd_stream(
            prd, functions_md, devices_md, backend_service, stream_callback
        )

        # 发送完成事件
        await self._send_callback('test_cases_generated', {
            'count': len(cases),
            'test_cases': [tc.to_dict() for tc in cases],
        })

        await self._send_callback('log', f'根据PRD生成了 {len(cases)} 个测试用例')

        return cases

    async def generate_test_cases_from_config(
        self,
        devices_md: Optional[str] = None
    ) -> List[TestCase]:
        """根据配置生成测试用例

        如果配置中有 prd_content，则根据 PRD、设备功能说明和家庭设备信息生成测试用例。
        生成成功后，清空默认用例，使用新生成的用例。
        支持流式生成，实时将内容发送到前端。

        Args:
            devices_md: 家庭设备信息（Markdown格式，可选）

        Returns:
            生成的测试用例列表
        """
        if not self.config.prd_content:
            logger.info("No PRD content provided, using default test cases")
            return self.case_manager.get_all_cases()

        logger.info("Generating test cases from PRD...")

        # 获取设备功能说明
        functions_md = None
        if self.config.iot_protocol_id and self.backend_service:
            await self._send_callback('status', '正在获取设备功能说明...')
            protocol = await self.backend_service.get_device_protocol(
                self.config.iot_protocol_id
            )
            if protocol:
                functions_md = protocol.get('functions_md', '')
                if functions_md:
                    logger.info(f"Retrieved functions_md, length: {len(functions_md)}")
                else:
                    logger.warning(f"No functions_md in protocol: {self.config.iot_protocol_id}")
            else:
                logger.warning(f"Failed to retrieve protocol: {self.config.iot_protocol_id}")

        # 流式生成测试用例
        await self._send_callback('status', '正在生成测试用例...')
        await self._send_callback('test_case_generation_started', {
            'prd_length': len(self.config.prd_content),
        })

        cases = await self.design_test_cases_stream(
            prd=self.config.prd_content,
            functions_md=functions_md,
            devices_md=devices_md,
            backend_service=self.backend_service
        )

        if cases:
            # 清空默认用例，使用新生成的用例
            self.case_manager.test_cases = []
            self.case_manager._case_map = {}
            self.case_manager.current_index = 0

            for case in cases:
                self.case_manager.add_case(case)

            logger.info(f"Generated and loaded {len(cases)} test cases")
            await self._send_callback('status', f'已生成 {len(cases)} 个测试用例')
        else:
            logger.warning("Failed to generate test cases, using default test cases")
            await self._send_callback('log', '测试用例生成失败，使用默认测试用例')

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

    async def generate_test_query(self) -> Optional[str]:
        """生成测试查询语句

        职责：
        1. 定位当前用例（如果需要）
        2. 在当前用例内生成测试查询

        多轮对话说明：
        - 一个测试用例可能需要多轮对话才能完成
        - 每次调用此方法都会调用 _produce_query_content 来生成查询
        - _produce_query_content 内部会调用 QueryGenerator App，由 App 决定是否继续生成查询
        - 当 Judge App 返回 next_action='next_case' 时，表示当前用例完成
        - evaluate_round_result 根据评判结果更新用例状态并决定是否推进

        Returns:
            测试查询语句，如果没有更多用例或当前用例已完成则返回None
        """
        # 调试：打印所有用例的状态
        logger.info(f"[generate_test_query] 总用例数: {len(self.case_manager.test_cases)}")
        for i, case in enumerate(self.case_manager.test_cases):
            logger.info(f"[generate_test_query] 用例 {i}: {case.id}, test_result={case.test_result}, type={type(case.test_result)}")

        current_case = self.case_manager.get_current_case()
        logger.info(f"[generate_test_query] current_index={self.case_manager.current_index}, current_case={current_case}")

        # 判断是否需要定位新用例：
        # 1. 没有当前用例（current_index == -1）
        # 2. 当前用例已完成（test_result != NOT_RUN）
        need_locate_new_case = (
            not current_case or
            current_case.test_result != TestResultStatus.NOT_RUN
        )
        logger.info(f"[generate_test_query] need_locate_new_case={need_locate_new_case}, TestResultStatus.NOT_RUN={TestResultStatus.NOT_RUN}")

        if need_locate_new_case:
            # 定位到第一个未执行的用例
            next_index = self.get_next_case_index()
            logger.info(f"[generate_test_query] get_next_case_index returned: {next_index}")
            if next_index is None:
                logger.info("No more test cases to execute")
                return None

            # 设置当前用例
            self.case_manager.current_index = next_index
            current_case = self.case_manager.get_current_case()
            logger.info(f"[generate_test_query] Set current_index={next_index}, current_case={current_case.id if current_case else None}")
            if not current_case:
                logger.info("No more test cases to execute")
                return None

            logger.info(f"开始执行测试用例 {next_index + 1}/{len(self.case_manager.test_cases)}: {current_case.title}")
            await self._send_callback('log', f'开始执行测试用例 {next_index + 1}.{current_case.title}')

            # 新用例的第一个查询：从 steps 中提取，而不是调用 QueryGenerator App
            # 这样可以确保新用例一定能开始执行
            query = self._extract_first_query_from_case(current_case)
            logger.info(f"[generate_test_query] _extract_first_query_from_case returned: {query}")

            if query:
                self.total_queries_generated += 1
                if self.execution_context:
                    self.execution_context.current_query = query
                logger.info(f"Generated first query for new case {current_case.id}: {query}")
                await self._send_callback('test_query', {
                    'case_id': current_case.id,
                    'query': query,
                })
                return query

            # 如果 steps 中没有提取到，再尝试调用 QueryGenerator App
            query = await self._produce_query_content({'next_action': 'next_step'}, "")

            if query:
                self.total_queries_generated += 1
                if self.execution_context:
                    self.execution_context.current_query = query
                logger.info(f"Generated test query for case {current_case.id}: {query}")
                await self._send_callback('test_query', {
                    'case_id': current_case.id,
                    'query': query,
                })

            return query

        # 在当前用例内生成测试查询
        query = await self._produce_query_content({'next_action': 'next_step'}, "")

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
        else:
            # 当前用例已完成（next_action='next_case'），但没有生成查询
            logger.info(f"Current case {current_case.id} completed, no more queries")

        return query

    def _extract_first_query_from_case(self, test_case: TestCase) -> Optional[str]:
        """从测试用例的 steps 中提取第一个查询

        Args:
            test_case: 测试用例

        Returns:
            提取的查询语句，如果无法提取则返回 None
        """
        if not test_case.steps:
            return None

        # 从第一个步骤中提取语音指令
        # 格式通常为：通过语音发出指令："打开一体机灯"
        first_step = test_case.steps[0]

        # 尝试提取引号中的内容
        import re
        # 匹配中文或英文引号
        match = re.search(r'["""](.+?)["""]', first_step)
        if match:
            return match.group(1)

        # 如果没有引号，尝试提取 "语音指令：" 后面的内容
        match = re.search(r'语音指令[：:]\s*(.+)', first_step)
        if match:
            return match.group(1).strip()

        # 如果都无法提取，返回整个步骤
        return None

    async def _produce_query_content(
        self,
        judge_result: Dict[str, Any],
        asr_text: str
    ) -> str:
        """生成测试查询内容

        职责：调用 QueryGenerator App 生成下一轮测试查询

        Args:
            judge_result: 判断结果（包含 next_action 等信息）
            asr_text: ASR识别文本

        Returns:
            生成的查询语句，如果当前用例已完成则返回空字符串
        """
        current_case = self.case_manager.get_current_case()
        if not current_case:
            return ""

        try:
            # next_action='next_case' 表示当前用例完成，不需要生成新查询
            if judge_result.get('next_action') == 'next_case':
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

            # 检查是否应该继续（QueryGenerator App 可能返回自己的判断）
            if query_result.get('should_continue') is False:
                # 当前用例已完成，返回空字符串
                # 推进到下一个用例的逻辑由 evaluate_round_result 处理
                logger.info(f"Query generator indicates should_continue=False, current case completed")
                return ""

            next_query = query_result.get('user_input', '')

            return next_query

        except Exception as e:
            logger.error(f"Error producing query content: {e}")
            return "让我继续为您检查设备状态"

    async def _call_query_generator_app(self, message: Any) -> Dict[str, Any]:
        """调用DeviceControlGenerator APP生成下一轮测试query

        从 agent_service.py 迁移

        Args:
            message: 输入信息

        Returns:
            查询生成结果字典
        """
        if not self.backend_service:
            raise RuntimeError(
                f"[MOCK 已删除] QueryGenerator App 调用失败：backend_service 未初始化。"
                f"message={message}"
            )

        try:
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
                    raise RuntimeError(
                        f"[MOCK 已删除] QueryGenerator App 返回非 JSON 内容: {result.content[:100]}"
                    )
            else:
                raise RuntimeError(
                    f"[MOCK 已删除] QueryGenerator App 调用失败: {result.error}"
                )

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Query generator app call failed: {e}")
            raise RuntimeError(
                f"[MOCK 已删除] QueryGenerator App 调用异常: {e}"
            )

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
                actual_result="没有当前测试用例",
                next_action="next_case",
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

        # 评判结果 - 传入对话历史
        logger.info(f"[DEBUG] conversation_history before judge: {len(self.conversation_history)} messages, "
                   f"rounds={len(self.conversation_history) // 2}, content={self.conversation_history}")
        judge_result = await self.judge.judge(
            current_case,
            execution_result,
            before,
            after,
            conversation_history=self.conversation_history
        )

        logger.info(f"Judge result for {current_case.id}: {'PASS' if judge_result.is_pass else 'FAIL'}, next_action={judge_result.next_action}")
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

        注意：此方法已弃用，建议使用 TestJudge.judge() 方法

        Args:
            asr_text: ASR识别出的文本
            current_status: 当前设备状态
            previous_status: 之前的设备状态

        Returns:
            分析结果字典，包含：
            - actual_result: 用例实际执行情况记录
            - is_pass: 当前测试步骤是否通过
            - next_action: 枚举值 "next_step" 或 "next_case"
        """
        if not self.backend_service:
            raise RuntimeError(
                f"[MOCK 已删除] Judge App 调用失败：backend_service 未初始化。"
                f"asr_text={asr_text[:50] if asr_text else None}"
            )

        try:
            # 构建消息内容
            current_case = self.case_manager.get_current_case()
            message = self._build_judge_app_message(
                test_case=current_case,
                conversation_history=self.conversation_history,
                current_status=current_status,
                previous_status=previous_status
            )

            result = await self.backend_service.invoke_app(
                app_id=self.JUDGE_APP_ID,
                message=message,
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
                    raise RuntimeError(
                        f"[MOCK 已删除] Judge App 返回非 JSON 内容: {result.content[:100]}"
                    )
            else:
                raise RuntimeError(
                    f"[MOCK 已删除] Judge App 调用失败: {result.error}"
                )

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            raise RuntimeError(
                f"[MOCK 已删除] Judge App 调用异常: {e}"
            )

    def _build_judge_app_message(
        self,
        test_case,
        conversation_history: List[Dict[str, str]],
        current_status: Dict,
        previous_status: Dict
    ) -> str:
        """构建评判App的消息内容（Markdown格式）

        使用独立的格式化工具函数构建消息。

        Args:
            test_case: 测试用例
            conversation_history: 对话历史记录
            current_status: 当前设备状态
            previous_status: 之前设备状态

        Returns:
            格式化的消息内容
        """
        parts = []

        # 1. 当前测试用例
        parts.append("**当前测试用例**：")
        parts.append(TestCaseManager.format_test_case_table(test_case))
        parts.append("")

        # 2. 对话历史记录（最近10轮）
        parts.append("**对话历史记录**：")
        parts.append(TestJudge.format_conversation_history_table(conversation_history, max_rounds=10))
        parts.append("")

        # 3. 设备状态变更记录（只显示变化的部分）
        parts.append("**设备状态变更记录**：")
        if test_case and test_case.device_guids:
            parts.append(TestJudge.format_device_changes_table(previous_status, current_status, test_case.device_guids))
        else:
            parts.append("| 设备GUID | 状态有变更的参数键 | 变化前的值 | 变化后的值 | 参数键的含义说明 |")
            parts.append("|:---|:---|:---|:---|:---|")

        return "\n".join(parts)

    # ========================================================================
    # 4. 测试执行评估与推进
    # ========================================================================

    async def evaluate_round_result(
        self,
        asr_text: str,
        device_status_before: Optional[Dict] = None,
        device_status_after: Optional[Dict] = None
    ) -> TaskProgress:
        """评估本轮执行结果并推进任务

        流程闭环：
        1. actual_result 记录到用例执行结果中
        2. 收集当前 case 每个步骤的 is_pass
        3. 当 next_action='next_case' 时，判断所有步骤是否都通过，更新测试用例最终状态
        4. 当 is_pass=False 时，记录缺陷
        5. 当 next_action='next_step' 时，推进当前用例的下一轮 query 生成和执行
        6. 当 next_action='next_case' 时，推进下一条测试用例的执行

        Args:
            asr_text: ASR识别文本
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态

        Returns:
            任务进度
        """
        # 1. 评判结果
        judge_result = await self.judge_test_result(
            asr_text,
            device_status_before,
            device_status_after
        )

        # 2. 更新用例状态
        current_case = self.case_manager.get_current_case()
        if current_case:
            # 2.1 记录本轮执行结果（actual_result 追加到 actual_results）
            round_num = len(current_case.actual_results) + 1
            round_result = f"[轮次{round_num}] {'通过' if judge_result.is_pass else '失败'}: {judge_result.actual_result}"
            current_case.actual_results.append(round_result)

            # 2.2 收集每个步骤的 is_pass 状态
            current_case.step_pass_results.append(judge_result.is_pass)
            logger.info(f"用例 {current_case.id} 轮次{round_num} is_pass={judge_result.is_pass}, "
                       f"step_pass_results={current_case.step_pass_results}")

            # 3. 当 is_pass=False 时，记录缺陷
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
                    logger.info(f"已记录缺陷: {defect_id}")

            # 4. 当 next_action='next_case' 时，更新测试用例最终状态
            if judge_result.next_action == 'next_case':
                # 判断所有步骤是否都通过
                all_passed = current_case.is_all_steps_passed()

                if all_passed:
                    test_status = TestResultStatus.PASS
                    logger.info(f"用例 {current_case.id} 所有步骤通过，最终状态: PASS")
                else:
                    test_status = TestResultStatus.FAIL
                    failed_steps = [i+1 for i, passed in enumerate(current_case.step_pass_results) if not passed]
                    logger.info(f"用例 {current_case.id} 存在失败步骤 {failed_steps}，最终状态: FAIL")

                # 更新测试用例结果
                self.case_manager.update_case_result(
                    current_case.id,
                    test_status,
                    current_case.actual_results,
                    judge_result.actual_result if not all_passed else None
                )

                # 记录用例完成事件
                await self._send_callback('case_completed', {
                    'case_id': current_case.id,
                    'title': current_case.title,
                    'test_result': test_status.value,
                    'step_pass_results': current_case.step_pass_results,
                    'actual_results': current_case.actual_results,
                    'defects': judge_result.defects,
                })

        # 5. 决定下一步行动
        action = self._determine_next_action(judge_result)

        # 6. 执行推进
        progress = self._execute_progression(action, judge_result)

        # 7. 更新统计
        if judge_result.next_action == 'next_case':
            self.total_cases_executed += 1
            # 清空对话历史，为新用例做准备
            self.clear_conversation_history()

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
        """执行推进

        推进策略：
        - NEXT_CASE: 当前用例完成，将 current_index 设为 -1，下次 generate_test_query 时定位新用例
        - STOP: 所有用例完成，停止任务
        - RETRY: 重试当前步骤
        - WAIT: 等待下一步操作
        """
        current_index = self.case_manager.current_index
        total_cases = len(self.case_manager.test_cases)

        if action == NextAction.NEXT_CASE:
            # 不再简单地递增 current_index，而是设置为 -1
            # 让 generate_test_query 来定位下一个未执行的用例
            self.case_manager.current_index = -1
            self.progressor.advance_to_next_case()
            message = f"当前用例已完成，准备推进到下一个测试用例"

        elif action == NextAction.STOP:
            self.case_manager.current_index = -1
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

    async def check_testing_completion(self) -> CompletionCheckResult:
        """判断测试是否全部完成

        两阶段判断：
        1. 工程化判断：检查用例的 test_result 状态
        2. 大模型验证：当工程化判断返回空列表时，调用大模型验证

        Returns:
            CompletionCheckResult: 包含是否完成、未执行列表、验证方式等
        """
        # 第一阶段：工程化判断
        unexecuted_indices = self.progressor.get_unexecuted_case_indices(
            self.case_manager.test_cases,
            self.case_manager.current_index
        )

        if unexecuted_indices:
            # 还有未执行的用例
            return CompletionCheckResult(
                completed=False,
                unexecuted_indices=unexecuted_indices,
                verified_by_llm=False
            )

        # 第二阶段：大模型验证
        completed, llm_unexecuted, analysis = await self.progressor.verify_completion_with_llm(
            self.case_manager.test_cases
        )

        return CompletionCheckResult(
            completed=completed,
            unexecuted_indices=llm_unexecuted,
            verified_by_llm=True,
            llm_analysis=analysis
        )

    def get_next_case_index(self) -> Optional[int]:
        """获取下一个要执行的用例索引

        Returns:
            下一个用例索引，如果没有则返回 None
        """
        unexecuted = self.progressor.get_unexecuted_case_indices(
            self.case_manager.test_cases,
            self.case_manager.current_index
        )
        logger.info(f"[get_next_case_index] unexecuted indices: {unexecuted}, total cases: {len(self.case_manager.test_cases)}")

        if not unexecuted:
            return None

        # 返回第一个未执行的用例索引
        return unexecuted[0]

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

        logger.info(f"[DEBUG] add_to_conversation_history: role={role}, content={content[:50]}..., total messages={len(self.conversation_history)}")

    def _get_conversation_history_context(self) -> str:
        """获取对话历史的文本格式（用于 Query Generator）

        注意：此方法返回简单的文本格式，不限制轮次。
        如需 Markdown 表格格式并限制轮次，请使用 TestJudge.format_conversation_history_table。
        """
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
        """格式化当前测试用例为 markdown 表格

        使用公共工具函数 TestCaseManager.format_test_case_table。
        """
        current_case = self.case_manager.get_current_case()
        return TestCaseManager.format_test_case_table(current_case)

    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        logger.info(f"[DEBUG] clear_conversation_history called, previous history had {len(self.conversation_history)} messages")
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

    async def on_user_input(self, asr_text: str, device_changes: Dict[str, Any]) -> None:
        """用户输入回调（静默检测触发ASR后）

        Args:
            asr_text: ASR识别的用户输入文本
            device_changes: 设备状态变化字典
        """
        logger.info(f"[TesterService] User input received: '{asr_text}'")
        if device_changes:
            logger.info(f"[TesterService] Device changes detected: {len(device_changes)} devices")
        # 目前仅记录日志，后续可扩展处理逻辑

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
        self.test_points = []
        self.current_test_point_index = 0
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