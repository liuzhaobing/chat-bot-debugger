"""
测试工程师服务 - 测试结果评判器

负责测试结果的评判，判断测试是否通过。
"""

import json
import logging
from typing import Optional, Dict, Any, List

from .models import (
    TestCase,
    TestResultStatus,
    ExecutionResult,
    JudgeResult,
    TesterConfig,
)

logger = logging.getLogger(__name__)


class TestJudge:
    """测试结果评判器

    负责评判测试执行结果是否满足预期，包括：
    - 设备状态变化验证
    - 语义匹配验证
    - 调用判断App进行智能评判
    """

    def __init__(
        self,
        config: Optional[TesterConfig] = None,
        backend_service=None
    ):
        """初始化评判器

        Args:
            config: 测试服务配置
            backend_service: 后端服务实例
        """
        self.config = config or TesterConfig()
        self.backend_service = backend_service

    async def judge(
        self,
        test_case: TestCase,
        execution_result: ExecutionResult,
        device_status_before: Dict[str, Any],
        device_status_after: Dict[str, Any]
    ) -> JudgeResult:
        """评判测试结果

        Args:
            test_case: 测试用例
            execution_result: 执行结果
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态

        Returns:
            评判结果
        """
        try:
            # 检测设备状态变化
            device_changes = self.compare_device_status(
                device_status_before,
                device_status_after,
                test_case.device_guids
            )

            # 调用判断App进行评判
            judge_app_result = await self.call_judge_app(
                execution_result.asr_text,
                device_status_before,
                device_status_after,
                device_changes
            )

            # 分析预期结果
            is_pass = self._analyze_expectations(
                test_case,
                execution_result,
                device_changes,
                judge_app_result
            )

            # 构建评判结果
            result = JudgeResult(
                case_id=test_case.id,
                is_pass=is_pass,
                confidence=judge_app_result.get('confidence', 0.8),
                analysis=judge_app_result.get('analysis', ''),
                detected_intent=judge_app_result.get('detected_intent'),
                should_continue=judge_app_result.get('should_continue', True),
                suggested_action=judge_app_result.get('suggested_action', 'continue_conversation'),
                device_mentioned=judge_app_result.get('device_mentioned', False),
            )

            logger.info(f"Judge result for {test_case.id}: {'PASS' if is_pass else 'FAIL'}")
            return result

        except Exception as e:
            logger.error(f"Error in judge: {e}")
            return JudgeResult(
                case_id=test_case.id,
                is_pass=False,
                confidence=0.0,
                analysis=f"评判异常: {str(e)}",
                should_continue=True,
            )

    async def call_judge_app(
        self,
        asr_text: str,
        device_status_before: Dict[str, Any],
        device_status_after: Dict[str, Any],
        device_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用判断App进行评判

        Args:
            asr_text: ASR识别文本
            device_status_before: 执行前设备状态
            device_status_after: 执行后设备状态
            device_changes: 设备状态变化

        Returns:
            评判结果字典
        """
        try:
            if self.backend_service:
                result = await self.backend_service.invoke_app(
                    app_id=self.config.judge_app_id,
                    message=f"分析用户语音: {asr_text}",
                    parameters={
                        "asr_text": asr_text,
                        "current_device_status": device_status_after,
                        "previous_device_status": device_status_before,
                        "device_changes": device_changes,
                    }
                )

                if result.success and result.content:
                    try:
                        parsed = json.loads(result.content)
                        logger.debug(f"Judge app result: {parsed}")
                        return parsed
                    except json.JSONDecodeError:
                        logger.warning(f"Judge app returned non-JSON: {result.content[:100]}")

            # 返回默认结果
            return self._get_default_judge_result(asr_text, device_changes)

        except Exception as e:
            logger.error(f"Judge app call failed: {e}")
            return self._get_default_judge_result(asr_text, device_changes)

    def _get_default_judge_result(
        self,
        asr_text: str,
        device_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取默认评判结果

        Args:
            asr_text: ASR识别文本
            device_changes: 设备状态变化

        Returns:
            默认评判结果
        """
        has_changes = bool(device_changes.get('changes'))
        return {
            'analysis': f'分析用户语音: {asr_text}',
            'confidence': 0.75,
            'should_continue': True,
            'suggested_action': 'continue_conversation',
            'detected_intent': 'device_control',
            'device_mentioned': has_changes,
        }

    def compare_device_status(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        target_guids: List[str] = None
    ) -> Dict[str, Any]:
        """比较设备状态变化

        Args:
            before: 执行前状态
            after: 执行后状态
            target_guids: 目标设备GUID列表

        Returns:
            设备状态变化字典
        """
        changes = {}
        target_guids = target_guids or []

        # 检查目标设备的状态变化
        for device_guid in target_guids:
            before_status = before.get(device_guid, [])
            after_status = after.get(device_guid, [])

            if before_status != after_status:
                changes[device_guid] = {
                    'has_change': True,
                    'before': before_status,
                    'after': after_status,
                    'diff': self._compute_diff(before_status, after_status),
                }
            else:
                changes[device_guid] = {
                    'has_change': False,
                }

        return {
            'changes': changes,
            'total_changes': sum(1 for c in changes.values() if c.get('has_change')),
        }

    def _compute_diff(
        self,
        before: List[Dict],
        after: List[Dict]
    ) -> Dict[str, Any]:
        """计算状态差异

        Args:
            before: 之前的状态列表
            after: 之后的状态列表

        Returns:
            差异字典
        """
        diff = {
            'added': [],
            'removed': [],
            'modified': [],
        }

        # 将状态列表转换为字典便于比较
        before_map = {item.get('name'): item for item in before if isinstance(item, dict)}
        after_map = {item.get('name'): item for item in after if isinstance(item, dict)}

        all_keys = set(before_map.keys()) | set(after_map.keys())

        for key in all_keys:
            if key not in before_map:
                diff['added'].append({'name': key, 'value': after_map.get(key)})
            elif key not in after_map:
                diff['removed'].append({'name': key, 'value': before_map.get(key)})
            elif before_map[key] != after_map[key]:
                diff['modified'].append({
                    'name': key,
                    'before': before_map[key],
                    'after': after_map[key],
                })

        return diff

    def _analyze_expectations(
        self,
        test_case: TestCase,
        execution_result: ExecutionResult,
        device_changes: Dict[str, Any],
        judge_app_result: Dict[str, Any]
    ) -> bool:
        """分析预期结果是否满足

        Args:
            test_case: 测试用例
            execution_result: 执行结果
            device_changes: 设备状态变化
            judge_app_result: 判断App结果

        Returns:
            是否通过
        """
        expect_results = test_case.expect_results

        if not expect_results:
            # 没有预期结果，默认通过
            return True

        # 检查设备状态变化
        if not device_changes.get('total_changes', 0) > 0:
            # 某些用例可能不需要设备状态变化（如错误处理用例）
            if test_case.type.value in ['Error', 'Security']:
                return True

        # 简单的预期结果匹配
        # TODO: 更复杂的语义匹配逻辑
        matched_count = 0
        for expect in expect_results:
            expect_lower = expect.lower()

            # 检查ASR文本是否匹配预期
            if execution_result.asr_text:
                # 提取关键词
                keywords = self._extract_keywords(expect_lower)
                if any(kw in execution_result.asr_text.lower() for kw in keywords):
                    matched_count += 1
                    continue

            # 检查设备变化是否匹配预期
            if '变为' in expect or '从' in expect:
                if device_changes.get('total_changes', 0) > 0:
                    matched_count += 1
                    continue

            # 检查成功关键词
            if any(kw in expect_lower for kw in ['成功', '通过', '正确']):
                if judge_app_result.get('confidence', 0) > 0.7:
                    matched_count += 1
                    continue

        # 至少匹配一半的预期结果视为通过
        match_ratio = matched_count / len(expect_results) if expect_results else 1.0
        return match_ratio >= 0.5

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 简单的关键词提取
        keywords = []
        # 提取设备名称
        device_keywords = ['灯', '油烟机', '空调', '一体机', '烤箱']
        for kw in device_keywords:
            if kw in text:
                keywords.append(kw)

        # 提取动作
        action_keywords = ['打开', '关闭', '开启', '关', '开']
        for kw in action_keywords:
            if kw in text:
                keywords.append(kw)

        return keywords

    def determine_test_status(self, judge_result: JudgeResult) -> TestResultStatus:
        """根据评判结果确定测试状态

        Args:
            judge_result: 评判结果

        Returns:
            测试状态
        """
        if judge_result.is_pass:
            return TestResultStatus.PASS
        else:
            return TestResultStatus.FAIL