"""
验证器模块 - 用于验证设备状态变化和语音响应

包含:
- IOTStateVerifier: IOT设备状态验证器，对比控制前后的properties JSON
- ResponseVerifier: 语音响应验证器
- CombinedValidator: 综合验证器
"""
import re
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import jsondiff

from chat.models import App
from chat.views import AppViewSet
from channels.db import database_sync_to_async
from device_protocols import DeviceProtocolLoader
from device_protocols.parser import ProtocolParser

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
    """
    IOT设备状态验证器

    使用jsondiff对比控制前后的properties JSON，验证设备状态是否按预期变化。

    使用示例:
        verifier = IOTStateVerifier(iot_service)

        # 获取控制前状态
        before_status = await iot_service.get_device_status(device_guid, token)

        # 执行控制操作...

        # 获取控制后状态
        after_status = await iot_service.get_device_status(device_guid, token)

        # 验证状态变化
        result = await verifier.verify_state_change(
            device_guid=device_guid,
            device_type="油烟机",
            before_properties=before_status.get('data', [{}])[0].get('properties', {}),
            after_properties=after_status.get('data', [{}])[0].get('properties', {}),
            query="打开油烟机",
            expectation="油烟机应该开机"
        )
    """

    def __init__(self, iot_service=None, protocol_loader=None):
        """
        初始化IOT状态验证器

        Args:
            iot_service: IOTService实例，用于获取设备状态
            protocol_loader: DeviceProtocolLoader实例，用于加载物模型协议
        """
        self.iot_service = iot_service
        
        # 延迟导入，避免循环依赖
        if protocol_loader is None:
            try:
                self.protocol_loader = DeviceProtocolLoader()
            except ImportError:
                logger.warning("DeviceProtocolLoader not available")
                self.protocol_loader = None
        else:
            self.protocol_loader = protocol_loader
        
        # 验证App名称（用于动态查找）
        self.verification_app_name = "IotStateVerification"
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
        """
        验证设备状态变化

        Args:
            device_guid: 设备GUID
            before_properties: 控制前的properties字典
            after_properties: 控制后的properties字典
            device_type: 设备类型（如"油烟机"），用于加载物模型协议
            query: 用户查询/指令
            expectation: 期望结果描述
            expected_changes: 预期的属性变化，如 {'powerState': 1, 'workState': 1}
            property_definitions: 属性定义映射，如 {'powerState': '电源状态'}

        Returns:
            VerificationResult验证结果
        """
        try:
            # 使用jsondiff对比差异
            diff = jsondiff.diff(before_properties, after_properties)

            if not diff:
                # 无变化
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
            
            # 如果提供了设备类型，从物模型协议中提取差异属性的定义
            protocol_definitions = {}
            if device_type and self.protocol_loader:
                protocol_definitions = self.protocol_loader.extract_property_definitions(
                    device_type, 
                    changed_property_ids
                )
                logger.info(f"Extracted {len(protocol_definitions)} property definitions from protocol")

            # 解析差异详情
            property_changes = self._parse_diff(
                diff,
                before_properties,
                after_properties,
                expected_changes,
                property_definitions or {}
            )

            # 如果提供了query和expectation，调用验证App进行智能判断
            if query and expectation and device_type:
                app_result = await self._call_verification_app(
                    device_guid=device_guid,
                    device_type=device_type,
                    diff=diff,
                    protocol_definitions=protocol_definitions,
                    query=query,
                    expectation=expectation,
                    property_changes=property_changes
                )
                
                if app_result:
                    # 使用App的判断结果
                    return VerificationResult(
                        status=app_result.get('status', VerificationStatus.FAILED),
                        device_guid=device_guid,
                        message=app_result.get('message', ''),
                        property_changes=property_changes,
                        diff_details=dict(diff),
                        confidence=app_result.get('confidence', 0.0),
                        timestamp=time.time()
                    )

            # 计算验证状态和置信度（传统方式）
            status, confidence, message = self._calculate_result(
                property_changes,
                expected_changes
            )

            return VerificationResult(
                status=status,
                device_guid=device_guid,
                message=message,
                property_changes=property_changes,
                diff_details=dict(diff),
                confidence=confidence,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error verifying state change for {device_guid}: {e}")
            return VerificationResult(
                status=VerificationStatus.ERROR,
                device_guid=device_guid,
                message=f"验证过程发生错误: {str(e)}",
                timestamp=time.time()
            )

    def _parse_diff(
        self,
        diff: Dict[str, Any],
        before_properties: Dict[str, Any],
        after_properties: Dict[str, Any],
        expected_changes: Optional[Dict[str, Any]],
        property_definitions: Optional[Dict[str, str]]
    ) -> List[PropertyChange]:
        """
        解析jsondiff结果，生成属性变化列表

        Args:
            diff: jsondiff的差异结果
            before_properties: 控制前的properties
            after_properties: 控制后的properties
            expected_changes: 预期的属性变化
            property_definitions: 属性定义映射

        Returns:
            属性变化列表
        """
        property_changes = []
        expected_changes = expected_changes or {}
        property_definitions = property_definitions or {}

        for key, change in diff.items():
            # jsondiff可能返回不同类型的值:
            # - 直接值: 表示属性被修改为新值
            # - 列表 [old, new]: 表示属性从old变为new
            # - 字典: 表示嵌套结构的变化

            property_name = property_definitions.get(key, key)

            if isinstance(change, list) and len(change) == 2:
                # [old_value, new_value] 格式
                previous_value = change[0]
                current_value = change[1]
            elif isinstance(change, dict):
                # 嵌套变化，转换为字符串表示
                previous_value = self._get_nested_value(before_properties, key)
                current_value = self._get_nested_value(after_properties, key)
            else:
                # 直接值，表示新值
                previous_value = before_properties.get(key)
                current_value = change

            # 检查是否是预期变化
            expected_value = expected_changes.get(key)
            is_expected = (
                expected_value is None or  # 没有预期值要求
                current_value == expected_value
            )

            property_changes.append(PropertyChange(
                property_id=key,
                property_name=property_name,
                previous_value=previous_value,
                current_value=current_value,
                expected_value=expected_value,
                is_expected=is_expected
            ))

        return property_changes

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """获取嵌套值"""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value

    def _calculate_result(
        self,
        property_changes: List[PropertyChange],
        expected_changes: Optional[Dict[str, Any]]
    ) -> Tuple[VerificationStatus, float, str]:
        """
        计算验证结果状态和置信度

        Args:
            property_changes: 属性变化列表
            expected_changes: 预期的属性变化

        Returns:
            (状态, 置信度, 消息)
        """
        if not property_changes:
            return VerificationStatus.FAILED, 0.0, "未检测到属性变化"

        # 统计变化情况
        total_changes = len(property_changes)
        expected_changes = expected_changes or {}

        # 如果有预期变化，检查是否全部满足
        if expected_changes:
            matched_changes = sum(1 for c in property_changes if c.is_expected)
            total_expected = len(expected_changes)

            # 计算匹配的预期属性数量
            expected_keys = set(expected_changes.keys())
            changed_keys = {c.property_id for c in property_changes}
            matched_keys = expected_keys & changed_keys

            if matched_keys == expected_keys:
                # 所有预期变化都发生了
                confidence = matched_changes / total_changes if total_changes > 0 else 1.0
                return (
                    VerificationStatus.SUCCESS,
                    confidence,
                    f"所有预期变化已验证，共{total_changes}个属性发生变化"
                )
            elif matched_keys:
                # 部分预期变化发生了
                confidence = len(matched_keys) / len(expected_keys)
                missing = expected_keys - changed_keys
                return (
                    VerificationStatus.PARTIAL,
                    confidence,
                    f"部分预期变化已验证，缺少: {', '.join(missing)}"
                )
            else:
                # 预期变化都没有发生
                return (
                    VerificationStatus.FAILED,
                    0.0,
                    f"预期变化未发生，实际变化: {', '.join(c.property_id for c in property_changes)}"
                )
        else:
            # 没有预期变化要求，只要有变化就算成功
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
        """
        通过IOT查询验证状态变化（带重试机制）

        在控制操作后调用，自动获取设备状态并验证。

        Args:
            device_guid: 设备GUID
            expected_changes: 预期的属性变化
            before_properties: 控制前的properties，如果为None则使用缓存或空字典
            token: IOT认证token
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            timeout: 超时时间（秒）

        Returns:
            VerificationResult验证结果
        """
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
                # 检查超时
                if time.time() - start_time > timeout:
                    return VerificationResult(
                        status=VerificationStatus.FAILED,
                        device_guid=device_guid,
                        message=f"验证超时（{timeout}秒）",
                        timestamp=time.time()
                    )

                # 获取当前设备状态
                status_result = await self.iot_service.get_device_status(device_guid, token)

                if status_result.get('success', False) or status_result.get('rc') == 0:
                    data = status_result.get('data', [])
                    if data:
                        after_properties = data[0].get('properties', {})

                        # 验证状态变化
                        result = await self.verify_state_change(
                            device_guid=device_guid,
                            before_properties=before_props,
                            after_properties=after_properties,
                            expected_changes=expected_changes
                        )

                        # 如果成功或部分成功，直接返回
                        if result.status in [VerificationStatus.SUCCESS, VerificationStatus.PARTIAL]:
                            return result

                        # 否则等待后重试
                        await asyncio.sleep(retry_interval)
                    else:
                        logger.warning(f"No data in status result for {device_guid}")
                        await asyncio.sleep(retry_interval)
                else:
                    logger.warning(f"Failed to get device status: {status_result.get('msg')}")
                    await asyncio.sleep(retry_interval)

            except Exception as e:
                logger.error(f"Error in verify_with_iot_query attempt {attempt + 1}: {e}")
                await asyncio.sleep(retry_interval)

        return VerificationResult(
            status=VerificationStatus.FAILED,
            device_guid=device_guid,
            message=f"验证失败，已重试{max_retries}次",
            timestamp=time.time()
        )

    def compare_properties(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        简单对比两个properties字典，返回差异

        这是一个工具方法，不涉及IOT查询。

        Args:
            before: 控制前的properties
            after: 控制后的properties

        Returns:
            差异字典
        """
        diff = jsondiff.diff(before, after)
        return dict(diff) if diff else {}

    def check_specific_properties(
        self,
        properties: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        检查特定属性是否满足预期值

        Args:
            properties: 当前设备属性
            expected: 预期属性值

        Returns:
            (是否全部满足, 不满足的属性详情)
        """
        mismatches = {}

        for key, expected_value in expected.items():
            actual_value = properties.get(key)
            if actual_value != expected_value:
                mismatches[key] = {
                    'expected': expected_value,
                    'actual': actual_value
                }

        return len(mismatches) == 0, mismatches
    
    def _extract_changed_property_ids(self, diff: Dict[str, Any]) -> List[str]:
        """
        从jsondiff结果中提取变化的属性ID列表
        
        Args:
            diff: jsondiff的差异结果
            
        Returns:
            变化的属性ID列表
        """
        property_ids = []
        
        for key in diff.keys():
            # 处理嵌套的key（如 "a.b.c"）
            if '.' in str(key):
                # 取第一层key
                property_ids.append(str(key).split('.')[0])
            else:
                property_ids.append(str(key))
        
        return list(set(property_ids))  # 去重
    
    async def _call_verification_app(
        self,
        device_guid: str,
        device_type: str,
        diff: Dict[str, Any],
        protocol_definitions: Dict[str, Dict[str, Any]],
        query: str,
        expectation: str,
        property_changes: List[PropertyChange]
    ) -> Optional[Dict[str, Any]]:
        """
        调用验证App进行智能判断
        
        Args:
            device_guid: 设备GUID
            device_type: 设备类型
            diff: jsondiff差异结果
            protocol_definitions: 差异属性的物模型定义
            query: 用户查询
            expectation: 期望结果
            property_changes: 属性变化列表
            
        Returns:
            App判断结果，如果调用失败则返回None
        """
        try:

            # 获取验证App
            @database_sync_to_async
            def get_app():
                try:
                    return App.objects.get(id=self.verification_app_id)
                except App.DoesNotExist:
                    logger.warning(f"Verification app '{self.verification_app_id}' not found")
                    return None
            
            app = await get_app()
            if not app:
                return None
            
            # 格式化物模型定义
            formatted_definitions = ProtocolParser.format_property_definitions(protocol_definitions)
            
            # 格式化属性变化
            changes_text = []
            for change in property_changes:
                prop_def = protocol_definitions.get(change.property_id, {})
                if prop_def:
                    change_text = ProtocolParser.format_property_change(
                        change.property_id,
                        prop_def,
                        change.previous_value,
                        change.current_value
                    )
                else:
                    change_text = f"{change.property_name}: {change.previous_value} → {change.current_value}"
                changes_text.append(change_text)
            
            formatted_changes = "\n".join(changes_text)
            
            # 准备参数
            parameters = {
                "device_guid": device_guid,
                "device_type": device_type,
                "query": query,
                "expectation": expectation,
                "property_changes": formatted_changes,
                "property_definitions": formatted_definitions,
                "diff_json": json.dumps(diff, ensure_ascii=False, indent=2)
            }
            
            # 调用App
            app_viewset = AppViewSet()
            
            @database_sync_to_async
            def execute_app():
                return app_viewset._execute_app(app=app, parameters=parameters)
            
            result = await execute_app()
            
            if result["status"] == "success":
                # 解析App返回的结果
                content = result["content"]
                
                # 尝试解析JSON格式的结果
                try:
                    parsed_result = json.loads(content)
                    
                    # 转换status字符串为VerificationStatus枚举
                    status_str = parsed_result.get('status', 'failed').lower()
                    if status_str == 'success':
                        status = VerificationStatus.SUCCESS
                    elif status_str == 'partial':
                        status = VerificationStatus.PARTIAL
                    elif status_str == 'error':
                        status = VerificationStatus.ERROR
                    else:
                        status = VerificationStatus.FAILED
                    
                    return {
                        'status': status,
                        'message': parsed_result.get('message', ''),
                        'confidence': parsed_result.get('confidence', 0.5),
                        'analysis': parsed_result.get('analysis', '')
                    }
                except json.JSONDecodeError:
                    # 如果不是JSON，直接使用文本内容
                    return {
                        'status': VerificationStatus.SUCCESS if '成功' in content or '符合' in content else VerificationStatus.FAILED,
                        'message': content,
                        'confidence': 0.7,
                        'analysis': content
                    }
            else:
                logger.error(f"Verification app call failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to call verification app: {e}")
            return None


class ResponseVerifier:
    """语音响应验证器"""

    def verify_response(
        self,
        asr_text: str,
        expected_keywords: List[str] = None,
        expected_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        验证语音响应内容

        Args:
            asr_text: ASR识别的文本
            expected_keywords: 预期的关键词列表
            expected_patterns: 预期的正则模式列表

        Returns:
            验证结果字典
        """
        result = {
            'text': asr_text,
            'keyword_matches': [],
            'pattern_matches': [],
            'passed': True,
            'confidence': 0.0
        }

        # 检查关键词
        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() in asr_text.lower():
                    result['keyword_matches'].append(keyword)

            keyword_ratio = len(result['keyword_matches']) / len(expected_keywords)
            result['confidence'] = keyword_ratio

        # 检查正则模式
        if expected_patterns:
            for pattern in expected_patterns:
                if re.search(pattern, asr_text):
                    result['pattern_matches'].append(pattern)

        # 计算是否通过
        if expected_keywords:
            result['passed'] = len(result['keyword_matches']) > 0

        return result


class CombinedValidator:
    """
    综合验证器

    结合IOT状态验证和语音响应验证，提供综合判定结果。
    """

    def __init__(self, iot_service=None):
        """
        初始化综合验证器

        Args:
            iot_service: IOTService实例
        """
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
        """
        执行综合验证

        Args:
            device_guid: 设备GUID
            before_properties: 控制前属性
            after_properties: 控制后属性
            asr_text: ASR识别文本
            expected_state_changes: 预期状态变化
            expected_keywords: 预期关键词

        Returns:
            综合验证结果
        """
        # IOT状态验证
        iot_result = await self.iot_verifier.verify_state_change(
            device_guid=device_guid,
            before_properties=before_properties,
            after_properties=after_properties,
            expected_changes=expected_state_changes
        )

        # 语音响应验证
        response_result = self.response_verifier.verify_response(
            asr_text=asr_text,
            expected_keywords=expected_keywords
        )

        # 综合判定
        combined_status = self._determine_combined_status(
            iot_result.status,
            response_result['passed']
        )

        combined_confidence = (
            iot_result.confidence * 0.7 +  # IOT状态权重70%
            (1.0 if response_result['passed'] else 0.0) * 0.3  # 语音响应权重30%
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