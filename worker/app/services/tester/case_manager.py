"""
测试工程师服务 - 测试用例管理器

负责测试用例的加载、存储、查询和状态更新。
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    TestCase,
    TestCaseType,
    TestResultStatus,
    TestCaseStatistics,
    TesterConfig,
)

logger = logging.getLogger(__name__)


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

    def _load_default_cases(self):
        """加载默认测试用例"""
        for case_data in DEFAULT_TEST_CASES:
            case = TestCase.from_dict(case_data)
            self.test_cases.append(case)
            self._case_map[case.id] = case

        logger.info(f"Loaded {len(self.test_cases)} default test cases")

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

    async def design_cases_from_scenario(
        self,
        scenario: str,
        llm_service
    ) -> List[TestCase]:
        """根据场景自动设计测试用例

        Args:
            scenario: 场景描述
            llm_service: LLM服务实例

        Returns:
            生成的测试用例列表
        """
        # TODO: 实现基于LLM的测试用例自动生成
        logger.info(f"Designing test cases for scenario: {scenario}")
        return []

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