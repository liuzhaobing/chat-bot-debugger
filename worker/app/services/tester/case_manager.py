"""
测试工程师服务 - 测试用例管理器

负责测试用例的加载、存储、查询和状态更新。
"""

import json
import logging
from typing import AsyncGenerator, Callable, Optional, Dict, Any, List, Tuple
from datetime import datetime

from .models import (
    TestPoint,
    TestCase,
    TestCaseType,
    TestResultStatus,
    TestCaseStatistics,
    TesterConfig,
)
from app.services.backend_service import BackendService, StreamChunk
from app.services.app_ids import TEST_CASE_DESIGNER_APP_ID

logger = logging.getLogger(__name__)


# ============================================================================
# 默认测试用例
# ============================================================================


# 默认测试用例 - 灯光控制测试套件
DEFAULT_TEST_CASES = [
    {
        "id": "APPL-LIGHT-001",
        "module": "一体机 - 灯光控制(lightControl)",
        "title": "语音打开一体机内部灯光",
        "type": "Functional",
        "preconditions": [
            "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
            "语音端（如App/音箱/眼镜）账号已绑定该设备并具备控制权限",
            "设备当前无故障告警（如门故障/控制板故障）"
        ],
        "device_guids": ["38-i750411c84f366"],
        "steps": [
            "通过语音发出指令：\"打开一体机灯\"（或\"打开烤箱灯/打开内部照明\"），识别到目标设备为CQ38-i7",
            "等待语音平台下发物模型指令 lightControl，参数 lightSwitch=1，controlTerminalType=语音端类型（如有）",
            "调用查询状态接口（如设备状态查询/灯状态上报）或通过设备面板/摄像观察确认灯光状态"
        ],
        "expect_results": [
            "语音识别成功并命中设备CQ38-i7",
            "下发 lightControl(lightSwitch=1) 成功，平台返回成功/设备ACK成功",
            "一体机内部照明灯点亮，灯状态从0变为1（或等效状态上报）"
        ],
        "actual_results": [],
        "test_result": "NotRun"
    },
    {
        "id": "APPL-LIGHT-002",
        "module": "一体机 - 灯光控制(lightControl)",
        "title": "语音关闭一体机内部灯光",
        "type": "Functional",
        "preconditions": [
            "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
            "语音端账号已绑定该设备并具备控制权限",
            "一体机内部灯当前为开启状态（lightSwitch=1）"
        ],
        "device_guids": ["38-i750411c84f366"],
        "steps": [
            "通过语音发出指令：\"关闭一体机灯\"（或\"关闭烤箱灯/关闭内部照明\"）",
            "等待语音平台下发物模型指令 lightControl，参数 lightSwitch=0",
            "查询/观察确认灯光状态"
        ],
        "expect_results": [
            "语音识别成功并命中设备CQ38-i7",
            "下发 lightControl(lightSwitch=0) 成功",
            "一体机内部照明灯熄灭，灯状态从1变为0（或等效状态上报）"
        ],
        "actual_results": [],
        "test_result": "NotRun"
    },
    {
        "id": "APPL-LIGHT-003",
        "module": "一体机 - 灯光控制(lightControl)",
        "title": "语音重复打开：灯已开启时再次打开应幂等成功",
        "type": "State",
        "preconditions": [
            "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
            "语音端账号已绑定该设备并具备控制权限",
            "灯已开启（lightSwitch=1）"
        ],
        "device_guids": ["38-i750411c84f366"],
        "steps": [
            "语音指令：\"打开一体机灯\"",
            "观察平台返回与设备状态上报"
        ],
        "expect_results": [
            "下发 lightControl(lightSwitch=1) 成功或返回已是目标状态（均视为成功）",
            "灯保持开启状态不闪烁、不重启、不出现异常告警",
            "状态上报保持 lightSwitch=1（或等效）"
        ],
        "actual_results": [],
        "test_result": "NotRun"
    },
    {
        "id": "APPL-LIGHT-004",
        "module": "一体机 - 灯光控制(lightControl)",
        "title": "语音重复关闭：灯已关闭时再次关闭应幂等成功",
        "type": "State",
        "preconditions": [
            "设备 CQ38-i7 在线（deviceGuid=38-i750411c84f366）",
            "语音端账号已绑定该设备并具备控制权限",
            "灯已关闭（lightSwitch=0）"
        ],
        "device_guids": ["38-i750411c84f366"],
        "steps": [
            "语音指令：\"关闭一体机灯\"",
            "观察平台返回与设备状态上报"
        ],
        "expect_results": [
            "下发 lightControl(lightSwitch=0) 成功或返回已是目标状态（均视为成功）",
            "灯保持关闭状态",
            "状态上报保持 lightSwitch=0（或等效）"
        ],
        "actual_results": [],
        "test_result": "NotRun"
    },
]


class TestCaseManager:
    """测试用例管理器

    负责测试用例的生命周期管理，包括加载、查询、更新和统计。
    """

    def __init__(self, config: Optional[TesterConfig] = None):
        """初始化用例管理器

        Args:
            config: 测试服务配置
        """
        self.config = config or TesterConfig()
        self.test_cases: List[TestCase] = []
        self.current_index: int = 0
        self._case_map: Dict[str, TestCase] = {}  # 用例ID到用例的映射

        # 加载默认测试用例
        self._load_default_cases()

    @staticmethod
    def format_test_case_table(test_case, headers: List[str] = None) -> str:
        """将测试用例格式化为 Markdown 表格

        Args:
            test_case: 测试用例对象（TestCase 或 dict）
            headers: 要显示的字段列表，默认显示全部字段

        Returns:
            Markdown 格式的表格字符串
        """
        if test_case is None:
            return "无用例"

        # 默认表头
        default_headers = [
            "id", "module", "title", "type", "preconditions", "device_guids",
            "steps", "expect_results", "actual_results", "test_result"
        ]
        headers = headers or default_headers

        # 表头映射
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

        # 支持 TestCase 对象或 dict
        def get_value(obj, key):
            if hasattr(obj, key):
                return getattr(obj, key, None)
            elif isinstance(obj, dict):
                return obj.get(key)
            return None

        # 构建表头
        lines = ["| " + " | ".join([header_names.get(h, h) for h in headers]) + " |"]
        lines.append("|" + "|".join([":---" for _ in headers]) + "|")

        # 构建数据行
        row_values = []
        for h in headers:
            value = get_value(test_case, h)
            if value is None:
                value = ''
            elif isinstance(value, list):
                value = '; '.join(str(v) for v in value) if value else ''
            elif hasattr(value, 'value'):  # Enum 类型
                value = value.value
            else:
                value = str(value)
            row_values.append(value)

        lines.append("| " + " | ".join(row_values) + " |")

        return "\n".join(lines)

    def _load_default_cases(self):
        """加载默认测试用例"""
        for case_data in DEFAULT_TEST_CASES:
            case = TestCase.from_dict(case_data)
            self.test_cases.append(case)
            self._case_map[case.id] = case

        logger.info(f"Loaded {len(self.test_cases)} default test cases")

    def _build_test_case_prompt(
        self,
        prd: str,
        functions_md: Optional[str] = None,
        devices_md: Optional[str] = None
    ) -> str:
        """构建测试用例设计的提示词

        将 PRD、设备功能说明和家庭设备信息整合成一个完整的提示词，用于测试用例设计 App。

        Args:
            prd: 产品需求文档内容
            functions_md: 设备功能说明（Markdown格式）
            devices_md: 家庭设备信息（Markdown格式）

        Returns:
            构建好的提示词
        """
        prompt_parts = []

        # 添加设备功能说明
        if functions_md:
            prompt_parts.append("## IOT 设备功能说明 - 支持语音控制设备的能力列表")
            prompt_parts.append(functions_md)

        # 添加家庭设备信息
        if devices_md:
            prompt_parts.append("## 家庭设备列表 - 当前家庭中实际存在的设备")
            prompt_parts.append(devices_md)

        # 添加 PRD 部分
        if prd:
            prompt_parts.append("## 任务要求")
            prompt_parts.append("请基于以下需求，设计一套完整的测试用例集。测试场景聚焦语音对话交互（涵盖厨电控制、状态查询等）。请以结构化的 JSON 格式输出：")
            prompt_parts.append(prd)

        return "\n\n".join(prompt_parts)

    async def load_cases(self, source: str) -> int:
        """从文件加载测试用例

        Args:
            source: 用例文件路径（JSON格式）

        Returns:
            加载的用例数量
        """
        try:
            with open(source, 'r', encoding='utf-8') as f:
                cases_data = json.load(f)

            # 清空现有用例
            self.test_cases = []
            self._case_map = {}

            for case_data in cases_data:
                case = TestCase.from_dict(case_data)
                self.test_cases.append(case)
                self._case_map[case.id] = case

            logger.info(f"Loaded {len(self.test_cases)} test cases from {source}")
            return len(self.test_cases)

        except Exception as e:
            logger.error(f"Failed to load test cases from {source}: {e}")
            return 0

    async def design_cases_from_prd(
        self,
        prd: str,
        functions_md: Optional[str] = None,
        devices_md: Optional[str] = None,
        backend_service: Optional[BackendService] = None
    ) -> List[TestCase]:
        """根据PRD（产品需求文档）自动设计测试用例

        通过调用后端的测试用例设计 APP，根据 PRD 内容、设备功能说明和家庭设备信息自动生成测试用例。

        Args:
            prd: 产品需求文档内容
            functions_md: 设备功能说明（Markdown格式）
            devices_md: 家庭设备信息（Markdown格式）
            backend_service: BackendService 实例（可选，不传则自动创建）

        Returns:
            生成的测试用例列表
        """
        logger.info(f"Designing test cases from PRD, length: {len(prd)}")
        logger.info("[NON-STREAM] Using invoke_app for test case generation")
        if functions_md:
            logger.info(f"Functions MD provided, length: {len(functions_md)}")
        if devices_md:
            logger.info(f"Devices MD provided, length: {len(devices_md)}")

        # 使用从 app_ids 导入的常量
        service = backend_service or BackendService()

        # 构建完整的提示词，包含 PRD、设备功能说明和家庭设备信息
        prompt = self._build_test_case_prompt(prd, functions_md, devices_md)

        try:
            result = await service.invoke_app(
                app_id=TEST_CASE_DESIGNER_APP_ID,
                message=prompt,
                timeout=600,
            )

            if not result.success:
                logger.error(f"Failed to invoke test case designer app: {result.error}")
                return []

            # 解析返回的测试用例
            content = result.content
            logger.info(f"Test case designer returned {len(content)} chars")

            # 解析 JSON 格式的用例
            import json
            try:
                # 尝试解析 JSON 格式的用例
                cases_data = json.loads(content)
                test_cases = []
                for case_data in cases_data:
                    case = TestCase.from_dict(case_data)
                    test_cases.append(case)
                    self._case_map[case.id] = case
                # 注意：不再自动添加到 self.test_cases，由调用方决定
                logger.info(f"Generated {len(test_cases)} test cases from PRD")
                return test_cases
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，记录原始内容
                logger.warning("Test case designer returned non-JSON content, returning empty list")
                logger.debug(f"Content: {content[:500]}...")
                return []

        except Exception as e:
            logger.error(f"Error designing test cases from PRD: {e}", exc_info=True)
            return []

    async def design_cases_from_prd_stream(
        self,
        prd: str,
        functions_md: Optional[str] = None,
        devices_md: Optional[str] = None,
        backend_service: Optional[BackendService] = None,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> List[TestCase]:
        """根据PRD（产品需求文档）流式设计测试用例

        通过调用后端的测试用例设计 APP，流式生成测试用例。
        支持 stream_callback 回调，实时将生成的文本发送给前端。

        Args:
            prd: 产品需求文档内容
            functions_md: 设备功能说明（Markdown格式）
            devices_md: 家庭设备信息（Markdown格式）
            backend_service: BackendService 实例
            stream_callback: 流式文本回调函数，用于实时发送生成内容

        Returns:
            生成的测试用例列表
        """
        logger.info(f"Designing test cases from PRD (streaming), length: {len(prd)}")
        logger.info("[STREAM] Using invoke_app_stream for test case generation")
        if functions_md:
            logger.info(f"Functions MD provided, length: {len(functions_md)}")
        if devices_md:
            logger.info(f"Devices MD provided, length: {len(devices_md)}")

        service = backend_service or BackendService()

        # 构建完整的提示词
        prompt = self._build_test_case_prompt(prd, functions_md, devices_md)

        # 收集完整的生成内容
        full_content = ""
        usage = None

        try:
            async for chunk in service.invoke_app_stream(
                app_id=TEST_CASE_DESIGNER_APP_ID,
                message=prompt,
                timeout=600,
            ):
                if chunk.is_error:
                    logger.error(f"Stream error: {chunk.error}")
                    break

                # 收集内容
                if chunk.content:
                    full_content += chunk.content

                    # 通过回调发送给前端
                    if stream_callback:
                        await stream_callback(chunk.content)

                # 收集 usage
                if chunk.usage:
                    usage = chunk.usage

                if chunk.is_done:
                    break

            logger.info(f"Test case designer returned {len(full_content)} chars")
            if usage:
                logger.info(f"Token usage: {usage}")

            # 解析生成的测试用例
            test_cases = self._parse_test_cases_content(full_content)

            # 添加到映射
            for case in test_cases:
                self._case_map[case.id] = case

            logger.info(f"Generated {len(test_cases)} test cases from PRD")
            return test_cases

        except Exception as e:
            logger.error(f"Error designing test cases from PRD (streaming): {e}", exc_info=True)
            return []

    def _parse_test_cases_content(self, content: str) -> List[TestCase]:
        """解析测试用例生成内容

        支持两种格式：
        1. 纯 JSON 数组
        2. Markdown 代码块中的 JSON

        Args:
            content: 生成的内容

        Returns:
            解析出的测试用例列表
        """
        import re

        # 尝试直接解析 JSON
        try:
            cases_data = json.loads(content)
            if isinstance(cases_data, list):
                test_cases = []
                for case_data in cases_data:
                    case = TestCase.from_dict(case_data)
                    test_cases.append(case)
                return test_cases
        except json.JSONDecodeError:
            pass

        # 尝试从 Markdown 代码块中提取 JSON
        json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        matches = re.findall(json_pattern, content, re.DOTALL)

        for match in matches:
            try:
                cases_data = json.loads(match)
                if isinstance(cases_data, list):
                    test_cases = []
                    for case_data in cases_data:
                        case = TestCase.from_dict(case_data)
                        test_cases.append(case)
                    return test_cases
            except json.JSONDecodeError:
                continue

        logger.warning("Failed to parse test cases content")
        logger.debug(f"Content: {content[:500]}...")
        return []

    async def design_case_for_test_point(
        self,
        test_point: TestPoint,
        llm_service=None
    ) -> TestCase:
        """针对单个测试点设计测试用例

        根据测试点的信息，设计具体的测试步骤和预期结果。

        Args:
            test_point: 测试点对象
            llm_service: LLM服务实例（可选）

        Returns:
            设计的测试用例
        """
        # 根据测试类型映射
        type_mapping = {
            "functional": TestCaseType.FUNCTIONAL,
            "state": TestCaseType.STATE,
            "edge_case": TestCaseType.EDGE_CASE,
            "error": TestCaseType.ERROR,
        }
        case_type = type_mapping.get(test_point.test_type, TestCaseType.FUNCTIONAL)

        # 生成测试用例ID
        case_id = f"TC-{test_point.id}"

        # TODO: 如果有 llm_service，可以调用LLM生成更详细的测试步骤
        # 这里使用简单的模板生成
        steps = []
        expect_results = []

        # 根据验收标准生成测试步骤和预期结果
        for i, criteria in enumerate(test_point.acceptance_criteria, 1):
            steps.append(f"步骤{i}: 验证 {criteria}")
            expect_results.append(criteria)

        # 如果没有验收标准，使用测试点描述
        if not steps:
            steps = [f"验证 {test_point.description}"]
            expect_results = [f"{test_point.description} 正常工作"]

        test_case = TestCase(
            id=case_id,
            module=test_point.module,
            title=f"{test_point.feature} - {test_point.description}",
            type=case_type,
            preconditions=test_point.preconditions.copy() if test_point.preconditions else [],
            device_guids=test_point.related_devices.copy() if test_point.related_devices else [],
            steps=steps,
            expect_results=expect_results,
            test_point_id=test_point.id,
        )

        logger.info(f"Designed test case {case_id} for test point {test_point.id}")
        return test_case

    def get_current_case(self) -> Optional[TestCase]:
        """获取当前测试用例

        Returns:
            当前测试用例，如果没有更多用例则返回 None
        """
        if 0 <= self.current_index < len(self.test_cases):
            return self.test_cases[self.current_index]
        return None

    def get_case_by_id(self, case_id: str) -> Optional[TestCase]:
        """根据ID获取测试用例

        Args:
            case_id: 用例ID

        Returns:
            测试用例，未找到则返回 None
        """
        return self._case_map.get(case_id)

    def update_case_result(
        self,
        case_id: str,
        status: TestResultStatus,
        actual_results: List[str],
        error_message: Optional[str] = None
    ) -> bool:
        """更新测试用例结果

        Args:
            case_id: 用例ID
            status: 测试状态
            actual_results: 实际结果列表
            error_message: 错误信息

        Returns:
            是否更新成功
        """
        case = self._case_map.get(case_id)
        if not case:
            logger.warning(f"Test case not found: {case_id}")
            return False

        case.test_result = status
        case.actual_results = actual_results
        case.execution_time = datetime.now()
        case.error_message = error_message

        logger.info(f"Updated test case {case_id}: {status.value}")
        return True

    def get_all_cases(self) -> List[TestCase]:
        """获取所有测试用例

        Returns:
            测试用例列表
        """
        return self.test_cases.copy()

    def get_statistics(self) -> TestCaseStatistics:
        """获取用例统计信息

        Returns:
            用例统计对象
        """
        stats = TestCaseStatistics(total=len(self.test_cases))

        for case in self.test_cases:
            if case.test_result == TestResultStatus.PASS:
                stats.passed += 1
            elif case.test_result == TestResultStatus.FAIL:
                stats.failed += 1
            elif case.test_result == TestResultStatus.BLOCKED:
                stats.blocked += 1
            elif case.test_result == TestResultStatus.SKIPPED:
                stats.skipped += 1
            else:
                stats.not_run += 1

        stats.calculate_pass_rate()
        return stats

    def advance_to_next_case(self) -> bool:
        """推进到下一个测试用例

        Returns:
            是否成功推进（False表示没有更多用例）
        """
        if self.current_index < len(self.test_cases) - 1:
            self.current_index += 1
            logger.info(f"Advanced to test case {self.current_index + 1}/{len(self.test_cases)}")
            return True
        return False

    def has_more_cases(self) -> bool:
        """检查是否还有更多测试用例

        Returns:
            是否还有未执行的用例
        """
        return self.current_index < len(self.test_cases)

    def reset(self):
        """重置所有测试用例状态"""
        self.current_index = 0
        for case in self.test_cases:
            case.test_result = TestResultStatus.NOT_RUN
            case.actual_results = []
            case.execution_time = None
            case.duration_seconds = None
            case.retry_count = 0
            case.error_message = None

        logger.info("All test cases have been reset")

    def add_case(self, case: TestCase) -> None:
        """添加测试用例

        Args:
            case: 要添加的测试用例
        """
        self.test_cases.append(case)
        self._case_map[case.id] = case
        logger.info(f"Added test case: {case.id}")

    def remove_case(self, case_id: str) -> bool:
        """移除测试用例

        Args:
            case_id: 要移除的用例ID

        Returns:
            是否成功移除
        """
        if case_id in self._case_map:
            case = self._case_map.pop(case_id)
            self.test_cases.remove(case)
            logger.info(f"Removed test case: {case_id}")
            return True
        return False

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """将所有用例转换为字典列表

        Returns:
            用例字典列表
        """
        return [case.to_dict() for case in self.test_cases]

    def export_to_json(self, file_path: str) -> bool:
        """导出测试用例到JSON文件

        Args:
            file_path: 目标文件路径

        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)
            logger.info(f"Exported test cases to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export test cases: {e}")
            return False

    def set_test_cases(self, cases_data: List[Dict[str, Any]]) -> int:
        """设置测试用例（替换现有用例）

        用于从前端接收用户修改后的测试用例。

        Args:
            cases_data: 测试用例字典列表

        Returns:
            设置的用例数量
        """
        # 清空现有用例
        self.test_cases = []
        self._case_map = {}

        for case_data in cases_data:
            case = TestCase.from_dict(case_data)
            self.test_cases.append(case)
            self._case_map[case.id] = case

        logger.info(f"Set {len(self.test_cases)} test cases from external source")
        return len(self.test_cases)

    def get_unexecuted_cases(self) -> List[Tuple[int, TestCase]]:
        """获取所有未执行的用例

        Returns:
            (index, TestCase) 元组列表
        """
        return [
            (i, case) for i, case in enumerate(self.test_cases)
            if case.test_result == TestResultStatus.NOT_RUN
        ]

    def get_unexecuted_indices(self) -> List[int]:
        """获取所有未执行用例的索引列表

        Returns:
            未执行用例的索引列表
        """
        return [
            i for i, case in enumerate(self.test_cases)
            if case.test_result == TestResultStatus.NOT_RUN
        ]