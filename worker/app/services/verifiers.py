"""
验证器模块 - 用于验证设备状态变化和语音响应
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
        self.verification_app_id = "3b5c603a388541f7942396adec9a57ce"

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

                status_result = await self.iot_service.get_device_status(device_guid, token)

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