"""
测试工程师服务 - 缺陷跟踪器

负责缺陷的记录、查询和统计。
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    Defect,
    DefectType,
    Severity,
    DefectStatistics,
    TestCase,
    TestResultStatus,
)

logger = logging.getLogger(__name__)


class DefectTracker:
    """缺陷跟踪器

    管理测试过程中发现的缺陷，包括：
    - 缺陷记录
    - 缺陷查询
    - 缺陷统计
    """

    def __init__(self):
        """初始化缺陷跟踪器"""
        self.defects: List[Defect] = []
        self._defect_map: Dict[str, Defect] = {}

    def record_defect(
        self,
        case_id: str,
        defect_type: DefectType,
        description: str,
        severity: Severity,
        device_guid: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None
    ) -> str:
        """记录缺陷

        Args:
            case_id: 关联的测试用例ID
            defect_type: 缺陷类型
            description: 缺陷描述
            severity: 严重程度
            device_guid: 相关设备GUID
            evidence: 证据数据

        Returns:
            缺陷ID
        """
        defect_id = f"DEF-{uuid.uuid4().hex[:8].upper()}"

        defect = Defect(
            id=defect_id,
            case_id=case_id,
            defect_type=defect_type,
            description=description,
            severity=severity,
            device_guid=device_guid,
            evidence=evidence,
            created_at=datetime.now(),
            status="open",
        )

        self.defects.append(defect)
        self._defect_map[defect_id] = defect

        logger.info(f"Recorded defect {defect_id} for case {case_id}: {description[:50]}...")
        return defect_id

    def get_defect_by_id(self, defect_id: str) -> Optional[Defect]:
        """根据ID获取缺陷

        Args:
            defect_id: 缺陷ID

        Returns:
            缺陷对象，未找到返回None
        """
        return self._defect_map.get(defect_id)

    def get_defects_by_case(self, case_id: str) -> List[Defect]:
        """获取用例关联的缺陷

        Args:
            case_id: 测试用例ID

        Returns:
            缺陷列表
        """
        return [d for d in self.defects if d.case_id == case_id]

    def get_defects_by_severity(self, severity: Severity) -> List[Defect]:
        """按严重程度获取缺陷

        Args:
            severity: 严重程度

        Returns:
            缺陷列表
        """
        return [d for d in self.defects if d.severity == severity]

    def get_defects_by_type(self, defect_type: DefectType) -> List[Defect]:
        """按类型获取缺陷

        Args:
            defect_type: 缺陷类型

        Returns:
            缺陷列表
        """
        return [d for d in self.defects if d.defect_type == defect_type]

    def get_open_defects(self) -> List[Defect]:
        """获取所有未关闭的缺陷

        Returns:
            未关闭的缺陷列表
        """
        return [d for d in self.defects if d.status == "open"]

    def update_defect_status(self, defect_id: str, status: str) -> bool:
        """更新缺陷状态

        Args:
            defect_id: 缺陷ID
            status: 新状态（open, fixed, verified, closed）

        Returns:
            是否更新成功
        """
        defect = self._defect_map.get(defect_id)
        if defect:
            defect.status = status
            logger.info(f"Updated defect {defect_id} status to {status}")
            return True
        return False

    def get_statistics(self) -> DefectStatistics:
        """获取缺陷统计

        Returns:
            缺陷统计对象
        """
        stats = DefectStatistics(total=len(self.defects))

        for defect in self.defects:
            # 按严重程度统计
            if defect.severity == Severity.CRITICAL:
                stats.critical += 1
            elif defect.severity == Severity.MAJOR:
                stats.major += 1
            elif defect.severity == Severity.NORMAL:
                stats.normal += 1
            elif defect.severity == Severity.MINOR:
                stats.minor += 1
            elif defect.severity == Severity.SUGGESTION:
                stats.suggestion += 1

            # 按状态统计
            if defect.status == "open":
                stats.open_count += 1
            elif defect.status == "fixed":
                stats.fixed_count += 1
            elif defect.status == "closed":
                stats.closed_count += 1

        return stats

    def auto_create_from_test_result(
        self,
        test_case: TestCase,
        execution_result: Dict[str, Any]
    ) -> Optional[str]:
        """根据测试结果自动创建缺陷

        Args:
            test_case: 测试用例
            execution_result: 执行结果

        Returns:
            创建的缺陷ID，如果未创建返回None
        """
        if test_case.test_result != TestResultStatus.FAIL:
            return None

        # 根据用例类型确定缺陷类型
        type_mapping = {
            "Functional": DefectType.FUNCTIONAL,
            "State": DefectType.FUNCTIONAL,
            "EdgeCase": DefectType.FUNCTIONAL,
            "Error": DefectType.FUNCTIONAL,
            "Security": DefectType.SECURITY,
            "Performance": DefectType.PERFORMANCE,
        }

        # 根据用例类型确定严重程度
        severity_mapping = {
            "Functional": Severity.NORMAL,
            "State": Severity.NORMAL,
            "EdgeCase": Severity.MINOR,
            "Error": Severity.MAJOR,
            "Security": Severity.CRITICAL,
            "Performance": Severity.NORMAL,
        }

        case_type = test_case.type.value if hasattr(test_case.type, 'value') else str(test_case.type)
        defect_type = type_mapping.get(case_type, DefectType.FUNCTIONAL)
        severity = severity_mapping.get(case_type, Severity.NORMAL)

        # 构建描述
        description = f"测试用例 {test_case.id} 执行失败: {test_case.title}\n"
        if test_case.error_message:
            description += f"错误信息: {test_case.error_message}\n"
        if test_case.actual_results:
            description += f"实际结果: {'; '.join(test_case.actual_results)}"

        # 获取设备GUID
        device_guid = test_case.device_guids[0] if test_case.device_guids else None

        # 创建缺陷
        return self.record_defect(
            case_id=test_case.id,
            defect_type=defect_type,
            description=description,
            severity=severity,
            device_guid=device_guid,
            evidence=execution_result,
        )

    def clear(self) -> None:
        """清空所有缺陷"""
        self.defects = []
        self._defect_map = {}
        logger.info("All defects cleared")

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表

        Returns:
            缺陷字典列表
        """
        return [d.to_dict() for d in self.defects]

    def export_to_json(self, file_path: str) -> bool:
        """导出缺陷到JSON文件

        Args:
            file_path: 目标文件路径

        Returns:
            是否导出成功
        """
        import json
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)
            logger.info(f"Exported defects to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export defects: {e}")
            return False