"""
验证器模块 - 用于验证设备状态变化、语音响应和测试结果评判

包含：
1. IOT设备状态验证器 (IOTStateVerifier)
2. 语音响应验证器 (ResponseVerifier)
3. 综合验证器 (CombinedValidator)
4. 测试结果评判器（TestJudge）- 包含设备状态变化计算和格式化静态方法
"""
import re
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import jsondiff
    HAS_JSONDIFF = True
except ImportError:
    HAS_JSONDIFF = False
    logging.warning("jsondiff not available, using basic diff")

from app.services.device_protocols import DeviceProtocolLoader
from app.services.device_protocols.parser import ProtocolParser

logger = logging.getLogger(__name__)


# ============================================================================
# 验证状态和结果类
# ============================================================================


class VerificationStatus(Enum):
    """验证状态枚举"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class PropertyChange:
    """单个属性变化"""
    property_id: str
    property_name: str
    previous_value: Any
    current_value: Any
    expected_value: Optional[Any] = None
    is_expected: bool = True


@dataclass
class VerificationResult:
    """验证结果"""
    status: VerificationStatus
    device_guid: str
    message: str
    property_changes: List[PropertyChange] = field(default_factory=list)
    diff_details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "device_guid": self.device_guid,
            "message": self.message,
            "property_changes": [
                {
                    "property_id": change.property_id,
                    "property_name": change.property_name,
                    "previous_value": change.previous_value,
                    "current_value": change.current_value,
                    "expected_value": change.expected_value,
                    "is_expected": change.is_expected
                }
                for change in self.property_changes
            ],
            "diff_details": self.diff_details,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


class IOTStateVerifier:
    """IOT设备状态验证器"""

    def __init__(self, iot_service=None, protocol_loader=None):
        """初始化IOT状态验证器"""
        self.iot_service = iot_service
        self.protocol_loader = protocol_loader or DeviceProtocolLoader()
        self.verification_app_id = "e4d13f457f7f486c99ca11b39a7b8347"

    async def verify_state_change(
        self,
        device_guid: str,
        before_properties: Dict[str, Any],
        after_properties: Dict[str, Any],
        device_type: Optional[str] = None,
        query: Optional[str] = None,
        expectation: Optional[str] = None,
        expected_changes: Optional[Dict[str, Any]] = None,
        property_definitions: Optional[Dict[str, str]] = None
    ) -> VerificationResult:
        """验证设备状态变化"""
        try:
            # 使用jsondiff对比差异
            if HAS_JSONDIFF:
                diff = jsondiff.diff(before_properties, after_properties)
            else:
                diff = self._simple_diff(before_properties, after_properties)

            if not diff:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    device_guid=device_guid,
                    message="设备状态未发生变化",
                    diff_details={},
                    confidence=0.0,
                    timestamp=time.time()
                )

            # 提取差异的属性ID列表
            changed_property_ids = self._extract_changed_property_ids(diff)

            # 从物模型协议中提取差异属性的定义
            protocol_definitions = {}
            if device_type and self.protocol_loader:
                protocol_definitions = self.protocol_loader.extract_property_definitions(
                    device_type,
                    changed_property_ids
                )

            # 解析差异详情
            property_changes = self._parse_diff(
                diff,
                before_properties,
                after_properties,
                expected_changes,
                property_definitions or {}
            )

            # 计算验证状态和置信度
            status, confidence, message = self._calculate_result(
                property_changes,
                expected_changes
            )

            return VerificationResult(
                status=status,
                device_guid=device_guid,
                message=message,
                property_changes=property_changes,
                diff_details=dict(diff) if diff else {},
                confidence=confidence,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error verifying state change: {e}")
            return VerificationResult(
                status=VerificationStatus.ERROR,
                device_guid=device_guid,
                message=f"验证过程发生错误: {str(e)}",
                timestamp=time.time()
            )

    def _simple_diff(self, before: Dict, after: Dict) -> Dict:
        """简单对比差异"""
        diff = {}
        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)
            if before_val != after_val:
                diff[key] = [before_val, after_val]
        return diff

    def _extract_changed_property_ids(self, diff: Dict) -> List[str]:
        """提取变化的属性ID列表"""
        property_ids = []
        for key in diff.keys():
            if '.' in str(key):
                property_ids.append(str(key).split('.')[0])
            else:
                property_ids.append(str(key))
        return list(set(property_ids))

    def _parse_diff(
        self,
        diff: Dict,
        before_properties: Dict,
        after_properties: Dict,
        expected_changes: Optional[Dict],
        property_definitions: Optional[Dict]
    ) -> List[PropertyChange]:
        """解析差异"""
        property_changes = []
        expected_changes = expected_changes or {}
        property_definitions = property_definitions or {}

        for key, change in diff.items():
            property_name = property_definitions.get(key, key)

            if isinstance(change, list) and len(change) == 2:
                previous_value = change[0]
                current_value = change[1]
            elif isinstance(change, dict):
                previous_value = before_properties.get(key)
                current_value = after_properties.get(key)
            else:
                previous_value = before_properties.get(key)
                current_value = change

            expected_value = expected_changes.get(key)
            is_expected = expected_value is None or current_value == expected_value

            property_changes.append(PropertyChange(
                property_id=key,
                property_name=property_name,
                previous_value=previous_value,
                current_value=current_value,
                expected_value=expected_value,
                is_expected=is_expected
            ))

        return property_changes

    def _calculate_result(
        self,
        property_changes: List[PropertyChange],
        expected_changes: Optional[Dict]
    ) -> Tuple[VerificationStatus, float, str]:
        """计算验证结果"""
        if not property_changes:
            return VerificationStatus.FAILED, 0.0, "未检测到属性变化"

        total_changes = len(property_changes)
        expected_changes = expected_changes or {}

        if expected_changes:
            matched_changes = sum(1 for c in property_changes if c.is_expected)
            total_expected = len(expected_changes)

            expected_keys = set(expected_changes.keys())
            changed_keys = {c.property_id for c in property_changes}
            matched_keys = expected_keys & changed_keys

            if matched_keys == expected_keys:
                confidence = matched_changes / total_changes if total_changes > 0 else 1.0
                return (
                    VerificationStatus.SUCCESS,
                    confidence,
                    f"所有预期变化已验证，共{total_changes}个属性发生变化"
                )
            elif matched_keys:
                confidence = len(matched_keys) / len(expected_keys)
                missing = expected_keys - changed_keys
                return (
                    VerificationStatus.PARTIAL,
                    confidence,
                    f"部分预期变化已验证，缺少: {', '.join(missing)}"
                )
            else:
                return (
                    VerificationStatus.FAILED,
                    0.0,
                    f"预期变化未发生"
                )
        else:
            return (
                VerificationStatus.SUCCESS,
                1.0,
                f"检测到{total_changes}个属性变化"
            )

    async def verify_with_iot_query(
        self,
        device_guid: str,
        expected_changes: Dict[str, Any],
        before_properties: Optional[Dict[str, Any]] = None,
        token: str = None,
        max_retries: int = 3,
        retry_interval: float = 1.0,
        timeout: float = 10.0
    ) -> VerificationResult:
        """通过IOT查询验证状态变化"""
        if not self.iot_service:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                device_guid=device_guid,
                message="IOTService未配置",
                timestamp=time.time()
            )

        start_time = time.time()
        before_props = before_properties or {}

        for attempt in range(max_retries):
            try:
                if time.time() - start_time > timeout:
                    return VerificationResult(
                        status=VerificationStatus.FAILED,
                        device_guid=device_guid,
                        message=f"验证超时（{timeout}秒）",
                        timestamp=time.time()
                    )

                status_result = await self.iot_service.get_device_status([device_guid], token)

                if status_result.get('success', False) or status_result.get('rc') == 0:
                    data = status_result.get('data', [])
                    if data:
                        after_properties = data[0].get('properties', {})

                        result = await self.verify_state_change(
                            device_guid=device_guid,
                            before_properties=before_props,
                            after_properties=after_properties,
                            expected_changes=expected_changes
                        )

                        if result.status in [VerificationStatus.SUCCESS, VerificationStatus.PARTIAL]:
                            return result

                        await asyncio.sleep(retry_interval)
                    else:
                        await asyncio.sleep(retry_interval)
                else:
                    await asyncio.sleep(retry_interval)

            except Exception as e:
                logger.error(f"Error in verify_with_iot_query: {e}")
                await asyncio.sleep(retry_interval)

        return VerificationResult(
            status=VerificationStatus.FAILED,
            device_guid=device_guid,
            message=f"验证失败，已重试{max_retries}次",
            timestamp=time.time()
        )


class ResponseVerifier:
    """语音响应验证器"""

    def verify_response(
        self,
        asr_text: str,
        expected_keywords: List[str] = None,
        expected_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """验证语音响应内容"""
        result = {
            'text': asr_text,
            'keyword_matches': [],
            'pattern_matches': [],
            'passed': True,
            'confidence': 0.0
        }

        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() in asr_text.lower():
                    result['keyword_matches'].append(keyword)

            keyword_ratio = len(result['keyword_matches']) / len(expected_keywords)
            result['confidence'] = keyword_ratio

        if expected_patterns:
            for pattern in expected_patterns:
                if re.search(pattern, asr_text):
                    result['pattern_matches'].append(pattern)

        if expected_keywords:
            result['passed'] = len(result['keyword_matches']) > 0

        return result


class CombinedValidator:
    """综合验证器"""

    def __init__(self, iot_service=None):
        self.iot_verifier = IOTStateVerifier(iot_service)
        self.response_verifier = ResponseVerifier()

    async def verify(
        self,
        device_guid: str,
        before_properties: Dict[str, Any],
        after_properties: Dict[str, Any],
        asr_text: str,
        expected_state_changes: Dict[str, Any] = None,
        expected_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """执行综合验证"""
        iot_result = await self.iot_verifier.verify_state_change(
            device_guid=device_guid,
            before_properties=before_properties,
            after_properties=after_properties,
            expected_changes=expected_state_changes
        )

        response_result = self.response_verifier.verify_response(
            asr_text=asr_text,
            expected_keywords=expected_keywords
        )

        combined_status = self._determine_combined_status(
            iot_result.status,
            response_result['passed']
        )

        combined_confidence = (
            iot_result.confidence * 0.7 +
            (1.0 if response_result['passed'] else 0.0) * 0.3
        )

        return {
            'status': combined_status.value,
            'confidence': combined_confidence,
            'iot_verification': iot_result.to_dict(),
            'response_verification': response_result,
            'timestamp': time.time()
        }

    def _determine_combined_status(
        self,
        iot_status: VerificationStatus,
        response_passed: bool
    ) -> VerificationStatus:
        """确定综合验证状态"""
        if iot_status == VerificationStatus.SUCCESS and response_passed:
            return VerificationStatus.SUCCESS
        elif iot_status == VerificationStatus.ERROR:
            return VerificationStatus.ERROR
        elif iot_status == VerificationStatus.SUCCESS or response_passed:
            return VerificationStatus.PARTIAL
        else:
            return VerificationStatus.FAILED


# ============================================================================
# 测试结果评判器
# ============================================================================

# 延迟导入，避免循环依赖
def _get_tester_models():
    """延迟导入 tester.models，避免循环依赖"""
    from app.services.tester.models import (
        TestCase,
        TestResultStatus,
        ExecutionResult,
        JudgeResult,
        TesterConfig,
    )
    return TestCase, TestResultStatus, ExecutionResult, JudgeResult, TesterConfig


class TestJudge:
    """测试结果评判器

    负责评判测试执行结果是否满足预期，包括：
    - 设备状态变化验证
    - 语义匹配验证
    - 调用判断App进行智能评判

    核心目的：判断当前测试步骤是否达到了预期效果
    1. 设备响应是否正确？ - ASR 识别的语音回复是否符合预期
    2. 设备状态是否变化？ - IoT 设备状态是否按预期改变

    三个关键作用：
    1. 判断步骤通过 - 当前这一轮交互是否满足预期
    2. 决定是否继续 - 当前用例是否还需要更多轮次
    3. 指导缺陷记录 - 失败时用于触发自动创建缺陷记录
    """

    # 设备品类名称到协议ID的映射
    CATEGORY_TO_PROTOCOL_ID = {
        "一体机": "一体机",
        "油烟机": "油烟机",
        "燃气灶": "燃气灶",
        "自动翻炒锅": "自动翻炒锅",
    }

    def __init__(
        self,
        config=None,
        backend_service=None
    ):
        """初始化评判器

        Args:
            config: 测试服务配置
            backend_service: 后端服务实例
        """
        _, _, _, _, TesterConfig = _get_tester_models()
        self.config = config or TesterConfig()
        self.backend_service = backend_service

        # 家庭设备列表（用于查询设备品类）
        self.family_devices: Dict[str, Any] = {}

        # 设备协议缓存：{protocol_id: {property_id: property_definition}}
        self.common_protocol: Dict[str, Dict[str, Any]] = {}

    def set_family_devices(self, family_devices: Dict[str, Any]) -> None:
        """设置家庭设备列表

        Args:
            family_devices: 家庭设备字典，格式为 {device_guid: {category_name, nick_name, ...}}
        """
        self.family_devices = family_devices or {}

    async def initialize_protocols(self, categories: List[str] = None) -> None:
        """初始化设备协议

        查询指定品类的设备协议，并构建属性ID到属性定义的映射。

        Args:
            categories: 设备品类列表，默认为 ["一体机", "油烟机", "燃气灶", "自动翻炒锅"]
        """
        if categories is None:
            categories = list(self.CATEGORY_TO_PROTOCOL_ID.keys())

        if not self.backend_service:
            logger.warning("BackendService not configured, skip protocol initialization")
            return

        self.common_protocol = {}

        for category in categories:
            protocol_id = self.CATEGORY_TO_PROTOCOL_ID.get(category)
            if not protocol_id:
                logger.warning(f"Unknown category: {category}, skip")
                continue

            try:
                protocol_data = await self.backend_service.get_device_protocol(protocol_id)
                if not protocol_data:
                    logger.warning(f"Protocol not found: {protocol_id} (category: {category})")
                    continue

                # 获取 protocol 字段（可能是 dict 或直接是 properties 列表）
                protocol = protocol_data.get('protocol', protocol_data)
                properties = protocol.get('properties', [])

                if not properties:
                    logger.warning(f"No properties in protocol: {protocol_id}")
                    continue

                # 构建属性ID到属性定义的映射
                property_map = {}
                for prop in properties:
                    prop_id = prop.get('id')
                    if prop_id:
                        property_map[prop_id] = prop

                self.common_protocol[protocol_id] = property_map
                logger.info(f"Loaded protocol {protocol_id}: {len(property_map)} properties")

            except Exception as e:
                logger.error(f"Failed to load protocol {protocol_id}: {e}")

    def get_property_description(self, device_guid: str, property_id: str) -> str:
        """获取属性的含义说明

        通过设备GUID查询品类，再从协议中获取属性定义，格式化为纯文本说明。

        Args:
            device_guid: 设备GUID
            property_id: 属性ID

        Returns:
            属性含义的纯文本说明，如果找不到则返回 "-"
        """
        # 通过 GUID 查询设备品类
        device_info = self.family_devices.get(device_guid)
        if not device_info:
            return "-"

        category_name = device_info.get('category_name')
        if not category_name:
            return "-"

        # 获取协议ID
        protocol_id = self.CATEGORY_TO_PROTOCOL_ID.get(category_name)
        if not protocol_id:
            return "-"

        # 从协议中获取属性定义
        property_map = self.common_protocol.get(protocol_id, {})
        prop_def = property_map.get(property_id)

        if not prop_def:
            return "-"

        # 格式化属性定义为纯文本
        return self._format_property_to_text(prop_def)

    @staticmethod
    def _format_property_to_text(prop_def: Dict[str, Any]) -> str:
        """将属性定义格式化为纯文本说明

        格式示例：
        - 枚举类型: "功率: 1=弱档, 2=中档, 3=强档, 6=爆炒, 0=无风量"
        - 数值类型: "红外温度第一路: float, 单位: 摄氏度"
        - 简单类型: "灯开关"

        Args:
            prop_def: 属性定义字典

        Returns:
            格式化的纯文本说明
        """
        if not prop_def:
            return "-"

        parts = []

        # 属性名称
        name = prop_def.get('name', '')
        if name:
            parts.append(name)

        # 值类型
        value_type = prop_def.get('valueType', {})
        type_name = value_type.get('type', '')

        if type_name == 'enum':
            # 枚举类型：列出所有可选值
            elements = value_type.get('elements', [])
            if elements:
                enum_parts = []
                for elem in elements:
                    value = elem.get('value', '')
                    text = elem.get('text', '')
                    if value and text:
                        enum_parts.append(f"{value}={text}")
                if enum_parts:
                    parts.append(f"[{', '.join(enum_parts)}]")
        elif type_name in ('int', 'float'):
            # 数值类型：显示单位和范围
            type_str = '整数' if type_name == 'int' else '浮点数'
            unit = value_type.get('unit', '')
            scale = value_type.get('scale')

            type_info = type_str
            if unit:
                type_info += f", 单位: {unit}"
            if scale:
                type_info += f", 精度: {scale}"
            parts.append(f"({type_info})")
        elif type_name == 'string':
            parts.append("(字符串)")
        elif type_name == 'bool':
            parts.append("(布尔值: 是/否)")

        # 描述
        description = prop_def.get('description', '')
        if description:
            parts.append(f"- {description}")

        return ' '.join(parts) if parts else "-"

    # ========================================================================
    # 静态方法：设备状态变化工具函数
    # ========================================================================

    @staticmethod
    def compute_device_changes(
        device_status_before: Dict[str, Any],
        device_status_after: Dict[str, Any],
        target_device_guids: List[str] = None
    ) -> Dict[str, Any]:
        """计算设备状态变化

        使用 jsondiff 对比前后状态，返回结构化的变化数据。

        Args:
            device_status_before: 执行前的设备状态，格式为 {device_guid: {property_name: value, ...}}
            device_status_after: 执行后的设备状态
            target_device_guids: 目标设备GUID列表

        Returns:
            变化字典，格式为 {changes: {device_guid: {...}}, total_changes: int}
        """
        changes = {}
        device_guids = target_device_guids or list(device_status_after.keys())

        for device_guid in device_guids:
            before_props = device_status_before.get(device_guid, {})
            after_props = device_status_after.get(device_guid, {})

            if before_props != after_props:
                # 使用 jsondiff 计算详细差异
                diff_result = TestJudge._compute_detailed_diff(before_props, after_props)

                changes[device_guid] = {
                    'has_change': True,
                    'before': before_props,
                    'after': after_props,
                    'diff': diff_result,
                }
            else:
                changes[device_guid] = {
                    'has_change': False,
                }

        return {
            'changes': changes,
            'total_changes': sum(1 for c in changes.values() if c.get('has_change')),
        }

    @staticmethod
    def format_device_changes_table(
        device_status_before: Dict[str, Any],
        device_status_after: Dict[str, Any],
        target_device_guids: List[str] = None
    ) -> str:
        """将设备状态变化格式化为 Markdown 表格

        使用 jsondiff 对比变化，只显示有变化的参数。

        Args:
            device_status_before: 执行前的设备状态，格式为 {device_guid: {property_name: value, ...}}
            device_status_after: 执行后的设备状态
            target_device_guids: 目标设备GUID列表

        Returns:
            Markdown 格式的表格字符串
        """
        parts = []

        # 表头
        parts.append("| 设备GUID | 状态有变更的参数键 | 变化前的值 | 变化后的值 | 参数键的含义说明 |")
        parts.append("|:---|:---|:---|:---|:---|")

        device_guids = target_device_guids or list(device_status_after.keys())

        for device_guid in device_guids:
            before_props = device_status_before.get(device_guid, {})
            after_props = device_status_after.get(device_guid, {})

            # 使用 jsondiff 对比（属性已经是 dict 格式）
            if HAS_JSONDIFF:
                diff = jsondiff.diff(before_props, after_props)
            else:
                diff = TestJudge._simple_dict_diff(before_props, after_props)

            if diff:
                for param_name, change in diff.items():
                    if isinstance(change, dict):
                        if 'old_value' in change and 'new_value' in change:
                            before_val = change['old_value']
                            after_val = change['new_value']
                        else:
                            before_val = before_props.get(param_name, '-')
                            after_val = after_props.get(param_name, '-')
                    else:
                        before_val = before_props.get(param_name, '-')
                        after_val = after_props.get(param_name, '-')

                    before_str = TestJudge._format_value(before_val)
                    after_str = TestJudge._format_value(after_val)
                    parts.append(f"| {device_guid} | {param_name} | {before_str} | {after_str} | - |")

        return "\n".join(parts)

    def format_device_changes_from_diff(self, device_changes: Dict[str, Any]) -> str:
        """从已有的设备变化数据格式化为 Markdown 表格

        Args:
            device_changes: 设备状态变化字典

        Returns:
            Markdown 格式的表格字符串
        """
        parts = []

        # 表头
        parts.append("| 设备GUID | 状态有变更的参数键 | 变化前的值 | 变化后的值 | 参数键的含义说明 |")
        parts.append("|:---|:---|:---|:---|:---|")

        changes = device_changes.get('changes', {})
        for device_guid, change_info in changes.items():
            if change_info.get('has_change'):
                diff = change_info.get('diff', {})
                # 处理修改的字段
                for modified in diff.get('modified', []):
                    param_name = modified.get('name', '')
                    before_val = self._format_value(modified.get('before', {}).get('value', ''))
                    after_val = self._format_value(modified.get('after', {}).get('value', ''))
                    # 获取属性含义说明
                    prop_desc = self.get_property_description(device_guid, param_name)
                    parts.append(f"| {device_guid} | {param_name} | {before_val} | {after_val} | {prop_desc} |")
                # 处理新增的字段
                for added in diff.get('added', []):
                    param_name = added.get('name', '')
                    after_val = self._format_value(added.get('value', ''))
                    # 获取属性含义说明
                    prop_desc = self.get_property_description(device_guid, param_name)
                    parts.append(f"| {device_guid} | {param_name} | - | {after_val} | {prop_desc} |")
                # 处理删除的字段
                for removed in diff.get('removed', []):
                    param_name = removed.get('name', '')
                    before_val = self._format_value(removed.get('value', ''))
                    # 获取属性含义说明
                    prop_desc = self.get_property_description(device_guid, param_name)
                    parts.append(f"| {device_guid} | {param_name} | {before_val} | - | {prop_desc} |")

        return "\n".join(parts)

    @staticmethod
    def format_conversation_history_table(
        conversation_history: List[Dict[str, str]],
        max_rounds: int = 10,
        include_current_round_hint: bool = True
    ) -> str:
        """将对话历史格式化为 Markdown 表格

        Args:
            conversation_history: 对话历史列表，每条消息包含 role 和 content
            max_rounds: 最多显示的对话轮次，默认10轮
            include_current_round_hint: 是否包含当前轮次提示

        Returns:
            Markdown 格式的表格字符串
        """
        parts = []

        # 计算当前轮次（基于对话历史长度，每2条消息为1轮）
        total_rounds = (len(conversation_history) + 1) // 2 if conversation_history else 0
        current_round = total_rounds + 1  # 当前正在评判的是新一轮

        # 取最近 max_rounds 轮的对话（最多 max_rounds * 2 条消息）
        max_messages = max_rounds * 2
        recent_history = conversation_history[-max_messages:] if conversation_history else []

        # 计算显示的起始轮次
        display_start_round = max(1, total_rounds - max_rounds + 1) if recent_history else 1

        # 添加提示信息
        if include_current_round_hint:
            if recent_history:
                parts.append(f"> 注：当前正在评判的是第 {current_round} 轮对话（表格中最新的一轮）")
                if len(conversation_history) > max_messages:
                    omitted_count = len(conversation_history) - max_messages
                    parts.append(f"> 注：仅显示最近 {max_rounds} 轮对话，更早的 {omitted_count} 条消息已省略")
            else:
                parts.append(f"> 注：当前是第 {current_round} 轮对话（首轮测试）")

        parts.append("")

        # 构建表格
        parts.append("| 轮次 | 角色 | 内容 |")
        parts.append("|:---|:---|:---|")

        if recent_history:
            round_num = display_start_round
            for i, msg in enumerate(recent_history):
                role_name = "测试员" if msg.get('role') == 'user' else "被测系统"
                # 每两条消息为同一轮（用户+系统），用户消息开始新的一轮
                if i > 0 and msg.get('role') == 'user':
                    round_num += 1
                # 第一条消息的轮次
                if i == 0:
                    round_num = display_start_round
                parts.append(f"| {round_num} | {role_name} | {msg.get('content', '')} |")

        return "\n".join(parts)

    # ========================================================================
    # 内部辅助静态方法
    # ========================================================================

    @staticmethod
    def _simple_dict_diff(before: Dict, after: Dict) -> Dict:
        """简单的字典差异对比"""
        diff = {}
        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            if key not in before:
                diff[key] = {'old_value': None, 'new_value': after[key]}
            elif key not in after:
                diff[key] = {'old_value': before[key], 'new_value': None}
            elif before[key] != after[key]:
                diff[key] = {'old_value': before[key], 'new_value': after[key]}
        return diff

    @staticmethod
    def _compute_detailed_diff(before: Dict, after: Dict) -> Dict[str, Any]:
        """计算详细的状态差异"""
        diff = {
            'added': [],
            'removed': [],
            'modified': [],
        }

        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            if key not in before:
                diff['added'].append({'name': key, 'value': after[key]})
            elif key not in after:
                diff['removed'].append({'name': key, 'value': before[key]})
            elif before[key] != after[key]:
                diff['modified'].append({
                    'name': key,
                    'before': {'value': before[key]},
                    'after': {'value': after[key]},
                })

        return diff

    @staticmethod
    def _format_value(value: Any) -> str:
        """格式化值为字符串"""
        if value is None:
            return '-'
        if isinstance(value, bool):
            return '是' if value else '否'
        if isinstance(value, (dict, list)):
            return str(value)
        return str(value)

    # ========================================================================
    # 实例方法
    # ========================================================================

    async def judge(
        self,
        test_case,
        execution_result,
        device_status_before: Dict[str, Any],
        device_status_after: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """评判测试结果

        Args:
            test_case: 测试用例
            execution_result: 执行结果
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态
            conversation_history: 对话历史记录

        Returns:
            评判结果
        """
        TestCase, _, _, JudgeResult, _ = _get_tester_models()

        try:
            # 检测设备状态变化
            device_changes = TestJudge.compute_device_changes(
                device_status_before,
                device_status_after,
                test_case.device_guids
            )

            # 调用判断App进行评判
            judge_app_result = await self.call_judge_app(
                test_case=test_case,
                conversation_history=conversation_history or [],
                device_changes=device_changes
            )

            # 构建评判结果
            result = JudgeResult(
                case_id=test_case.id,
                is_pass=judge_app_result.get('is_pass', False),
                actual_result=judge_app_result.get('actual_result', ''),
                next_action=judge_app_result.get('next_action', 'next_step'),
            )

            logger.info(f"Judge result for {test_case.id}: {'PASS' if result.is_pass else 'FAIL'}, next_action={result.next_action}")
            return result

        except Exception as e:
            logger.error(f"Error in judge: {e}")
            return JudgeResult(
                case_id=test_case.id,
                is_pass=False,
                actual_result=f"评判异常: {str(e)}",
                next_action="next_case",
            )

    async def call_judge_app(
        self,
        test_case,
        conversation_history: List[Dict[str, str]],
        device_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用判断App进行评判

        输入数据（message）包含：
        1. 当前测试用例（测试用例的表头字段）
        2. 对话历史记录（多轮对话的表头）
        3. 设备状态变更记录

        Args:
            test_case: 测试用例
            conversation_history: 对话历史记录
            device_changes: 设备状态变化

        Returns:
            评判结果字典，包含：
            - actual_result: 用例实际执行情况记录
            - is_pass: 当前测试步骤是否通过
            - next_action: 枚举值 "next_step" 或 "next_case"
        """
        try:
            # 构建消息内容（Markdown格式）
            message = self._build_judge_message(
                test_case=test_case,
                conversation_history=conversation_history,
                device_changes=device_changes
            )

            logger.info(f"[DEBUG] call_judge_app: backend_service={self.backend_service is not None}, judge_app_id={self.config.judge_app_id}")

            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.config.judge_app_id,
                    message=message,
                )

                logger.info(f"[DEBUG] Judge app invoke result: success={result.success}, has_content={result.content is not None}")

                if result.success and result.content:
                    try:
                        parsed = json.loads(result.content)
                        logger.info(f"[DEBUG] Judge app parsed result: is_pass={parsed.get('is_pass')}, next_action={parsed.get('next_action')}")
                        return parsed
                    except json.JSONDecodeError:
                        logger.warning(f"Judge app returned non-JSON: {result.content[:100]}")

            # 返回默认结果
            logger.info("[DEBUG] Using default judge result (next_case)")
            return self._get_default_judge_result(test_case, device_changes)

        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return self._get_default_judge_result(test_case, device_changes)

    def _build_judge_message(
        self,
        test_case,
        conversation_history: List[Dict[str, str]],
        device_changes: Dict[str, Any]
    ) -> str:
        """构建评判App的消息内容

        使用独立的格式化工具函数构建 Markdown 格式的消息。

        Args:
            test_case: 测试用例
            conversation_history: 对话历史记录
            device_changes: 设备状态变化

        Returns:
            格式化的消息内容（Markdown格式）
        """
        # 延迟导入，避免循环依赖
        from app.services.tester.case_manager import TestCaseManager

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
        parts.append(self.format_device_changes_from_diff(device_changes))

        return "\n".join(parts)

    def _get_default_judge_result(
        self,
        test_case,
        device_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取默认评判结果

        Args:
            test_case: 测试用例
            device_changes: 设备状态变化

        Returns:
            默认评判结果
        """
        has_changes = device_changes.get('total_changes', 0) > 0
        actual_result = f"测试用例 {test_case.title} 执行完成"

        if has_changes:
            actual_result += "，设备状态已变更"
        else:
            actual_result += "，设备状态无变化"

        logger.info(f"[DEBUG] _get_default_judge_result: has_changes={has_changes}, returning next_action='next_case'")

        return {
            'actual_result': actual_result,
            'is_pass': has_changes,  # 有变化则认为通过
            'next_action': 'next_case',
        }

    def determine_test_status(self, judge_result):
        """根据评判结果确定测试状态

        Args:
            judge_result: 评判结果

        Returns:
            测试状态
        """
        _, TestResultStatus, _, _, _ = _get_tester_models()

        if judge_result.is_pass:
            return TestResultStatus.PASS
        else:
            return TestResultStatus.FAIL