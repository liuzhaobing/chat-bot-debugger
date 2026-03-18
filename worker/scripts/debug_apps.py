"""
App 调试工具

提供统一的 App 调试接口，用于测试各个 App 的调用。

使用方式：
    cd worker
    conda activate chat-bot-debugger
    python scripts/debug_apps.py
"""

import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

# 从项目模块导入 App ID 常量
from app.services.app_ids import (
    JUDGE_APP_ID,
    QUERY_GENERATOR_APP_ID,
    TEST_POINT_EXTRACTOR_APP_ID,
    TEST_CASE_DESIGNER_APP_ID,
    COMPLETION_VERIFIER_APP_ID,
    ASR_APP_ID,
    VERIFICATION_APP_ID,
    APP_INFO,
    list_apps,
)


# ============================================================================
# 后端服务类（简化版，避免依赖问题）
# ============================================================================

class AppInvokeResult:
    """App 调用结果"""
    def __init__(self, success: bool, content: str = "", error: Optional[str] = None,
                 usage: Optional[Dict] = None, latency_ms: Optional[int] = None):
        self.success = success
        self.content = content
        self.error = error
        self.usage = usage
        self.latency_ms = latency_ms

    def __str__(self) -> str:
        if self.success:
            return self.content
        return f"[Error: {self.error}]"


class BackendService:
    """简化的后端服务类"""

    def __init__(self, backend_url: str = "http://localhost:8000", timeout: float = 60.0):
        self.backend_url = backend_url
        self.default_timeout = timeout

    async def invoke_app(
        self,
        app_id: str,
        message: Optional[str] = None,
        context: Optional[list] = None,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> AppInvokeResult:
        """调用 Backend App 执行接口"""
        url = f"{self.backend_url}/api/apps/{app_id}/invoke/"
        request_timeout = timeout or self.default_timeout

        payload = {
            "message": message or "",
            "context": context or [],
            "parameters": parameters or {}
        }

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                print(f"\n📡 请求 URL: {url}")
                print(f"📝 App ID: {app_id}")
                if message:
                    print(f"💬 Message: {message[:200]}{'...' if len(message) > 200 else ''}")
                if parameters:
                    print(f"⚙️  Parameters: {json.dumps(parameters, ensure_ascii=False)[:200]}")

                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                status = data.get("status", "")
                content = data.get("content", "")
                error = data.get("error")
                usage = data.get("usage")
                latency_ms = data.get("latency_ms")

                if status == "success":
                    print(f"✅ 调用成功 (耗时: {latency_ms}ms)")
                    return AppInvokeResult(True, content, None, usage, latency_ms)
                else:
                    print(f"❌ 调用失败: {error}")
                    return AppInvokeResult(False, content, error, usage, latency_ms)

        except httpx.TimeoutException:
            error_msg = f"请求超时 ({request_timeout}s)"
            print(f"⏰ {error_msg}")
            return AppInvokeResult(False, error=error_msg)

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 错误: {e.response.status_code}"
            print(f"❌ {error_msg}")
            return AppInvokeResult(False, error=error_msg)

        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            print(f"❌ {error_msg}")
            return AppInvokeResult(False, error=error_msg)


# ============================================================================
# 调试函数
# ============================================================================

async def debug_app(
    app_id: str,
    message: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试单个 App

    Args:
        app_id: App ID
        message: 消息内容
        parameters: 参数
        backend_url: 后端服务 URL

    Returns:
        调用结果
    """
    service = BackendService(backend_url=backend_url, timeout=120.0)
    return await service.invoke_app(app_id, message=message, parameters=parameters)


def print_result(result: AppInvokeResult, title: str = "结果") -> None:
    """打印调用结果"""
    print(f"\n{'=' * 60}")
    print(f"📋 {title}")
    print("=" * 60)

    if result.success:
        print("状态: ✅ 成功")
        print(f"\n📄 内容:\n{result.content}")
        if result.usage:
            print(f"\n📊 Token 使用: {result.usage}")
    else:
        print(f"状态: ❌ 失败")
        print(f"错误: {result.error}")

    print("=" * 60)


# ============================================================================
# 各 App 调试函数
# ============================================================================

async def debug_judge_app(
    asr_text: str,
    device_status_before: Optional[Dict] = None,
    device_status_after: Optional[Dict] = None,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试评判 App

    Args:
        asr_text: ASR 识别文本
        device_status_before: 执行前设备状态
        device_status_after: 执行后设备状态
        backend_url: 后端服务 URL
    """
    print("\n" + "=" * 60)
    print("🔍 调试评判 App (JUDGE_APP_ID)")
    print("=" * 60)

    device_status_before = device_status_before or {}
    device_status_after = device_status_after or {}

    # 计算设备状态变化（属性已经是 dict 格式）
    device_changes = {"changes": {}, "total_changes": 0}
    for device_guid in set(list(device_status_before.keys()) + list(device_status_after.keys())):
        before = device_status_before.get(device_guid, {})
        after = device_status_after.get(device_guid, {})
        if before != after:
            device_changes["changes"][device_guid] = {
                "has_change": True,
                "before": before,
                "after": after
            }
            device_changes["total_changes"] += 1

    result = await debug_app(
        app_id=JUDGE_APP_ID,
        message=f"分析用户语音: {asr_text}",
        parameters={
            "asr_text": asr_text,
            "current_device_status": device_status_after,
            "previous_device_status": device_status_before,
            "device_changes": device_changes,
        },
        backend_url=backend_url
    )

    print_result(result, "评判结果")
    return result


async def debug_query_generator_app(
    test_case: Optional[Dict] = None,
    family_devices: Optional[Dict] = None,
    conversation_history: Optional[list] = None,
    current_device_status: Optional[Dict] = None,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试查询生成器 App

    Args:
        test_case: 当前测试用例
        family_devices: 家庭设备列表
        conversation_history: 对话历史
        current_device_status: 当前设备状态
        backend_url: 后端服务 URL
    """
    print("\n" + "=" * 60)
    print("🔍 调试查询生成器 App (QUERY_GENERATOR_APP_ID)")
    print("=" * 60)

    # 默认测试用例
    test_case = test_case or {
        "id": "APPL-LIGHT-001",
        "module": "一体机 - 灯光控制",
        "title": "语音打开一体机内部灯光",
        "type": "Functional",
        "preconditions": ["设备在线"],
        "device_guids": ["38-i750411c84f366"],
        "steps": ["语音指令：打开一体机灯"],
        "expect_results": ["灯光状态从0变为1"],
        "actual_results": [],
        "test_result": "NotRun"
    }

    family_devices = family_devices or {}
    conversation_history = conversation_history or []
    current_device_status = current_device_status or {}

    # 构建消息
    message_parts = []

    # 测试用例表格
    message_parts.append("**当前测试用例**：")
    message_parts.append("| 用例ID | 模块 | 标题 | 类型 | 测试结果 |")
    message_parts.append("|:---|:---|:---|:---|:---|")
    message_parts.append(f"| {test_case['id']} | {test_case['module']} | {test_case['title']} | {test_case['type']} | {test_case['test_result']} |")

    # 家庭设备列表
    if family_devices:
        message_parts.append("\n**家庭设备列表**：")
        message_parts.append("| 设备GUID | 设备类型 | 设备昵称 |")
        message_parts.append("|:---|:---|:---|")
        for guid, device in family_devices.items():
            message_parts.append(f"| {guid} | {device.get('category_name', 'N/A')} | {device.get('nick_name', 'N/A')} |")

    # 对话历史
    if conversation_history:
        message_parts.append("\n**对话历史**：")
        for msg in conversation_history[-5:]:  # 最近5条
            role = "测试员" if msg['role'] == 'user' else "被测系统"
            message_parts.append(f"- {role}: {msg['content']}")

    # 设备状态
    if current_device_status:
        message_parts.append("\n**当前设备状态**：")
        message_parts.append(f"```json\n{json.dumps(current_device_status, ensure_ascii=False, indent=2)}\n```")

    message = "\n".join(message_parts)

    result = await debug_app(
        app_id=QUERY_GENERATOR_APP_ID,
        message=message,
        backend_url=backend_url
    )

    print_result(result, "生成的查询")
    return result


async def debug_test_point_extractor_app(
    scenario: str,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试测试点提取 App

    Args:
        scenario: 场景描述
        backend_url: 后端服务 URL
    """
    print("\n" + "=" * 60)
    print("🔍 调试测试点提取 App (TEST_POINT_EXTRACTOR_APP_ID)")
    print("=" * 60)

    result = await debug_app(
        app_id=TEST_POINT_EXTRACTOR_APP_ID,
        message=f"从以下场景中提取测试点：\n\n{scenario}",
        parameters={
            "scenario": scenario,
        },
        backend_url=backend_url
    )

    print_result(result, "提取的测试点")
    return result


async def debug_test_case_designer_app(
    prd: str,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试测试用例设计 App

    Args:
        prd: 产品需求文档
        backend_url: 后端服务 URL
    """
    print("\n" + "=" * 60)
    print("🔍 调试测试用例设计 App (TEST_CASE_DESIGNER_APP_ID)")
    print("=" * 60)

    result = await debug_app(
        app_id=TEST_CASE_DESIGNER_APP_ID,
        message=prd,
        backend_url=backend_url
    )

    print_result(result, "设计的测试用例")
    return result


async def debug_completion_verifier_app(
    test_cases: list,
    backend_url: str = "http://localhost:8000"
) -> AppInvokeResult:
    """调试完成验证 App

    Args:
        test_cases: 测试用例列表
        backend_url: 后端服务 URL
    """
    print("\n" + "=" * 60)
    print("🔍 调试完成验证 App (COMPLETION_VERIFIER_APP_ID)")
    print("=" * 60)

    # 构建 Markdown 表格
    lines = ["| index | title | test_result |", "|-------|-------|-------------|"]
    for i, case in enumerate(test_cases):
        title = case.get('title', case.get('id', 'N/A'))
        test_result = case.get('test_result', 'NotRun')
        lines.append(f"| {i} | {title} | {test_result} |")
    table = "\n".join(lines)

    result = await debug_app(
        app_id=COMPLETION_VERIFIER_APP_ID,
        message=f"请分析以下测试用例执行情况，判断是否全部完成：\n\n{table}",
        parameters={
            "case_table": table,
        },
        backend_url=backend_url
    )

    print_result(result, "完成验证结果")
    return result


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数 - 演示所有 App 的调试"""
    print("\n" + "=" * 80)
    print("🛠️  App 调试工具")
    print("=" * 80)

    # 从命令行参数获取后端 URL
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    print(f"\n📡 后端服务: {backend_url}")

    while True:
        print("\n请选择要调试的 App:")
        print("  1. 评判 App (JUDGE_APP_ID)")
        print("  2. 查询生成器 App (QUERY_GENERATOR_APP_ID)")
        print("  3. 测试点提取 App (TEST_POINT_EXTRACTOR_APP_ID)")
        print("  4. 测试用例设计 App (TEST_CASE_DESIGNER_APP_ID)")
        print("  5. 完成验证 App (COMPLETION_VERIFIER_APP_ID)")
        print("  6. 列出所有 App ID")
        print("  0. 退出")

        choice = input("\n请输入选项 (0-6): ").strip()

        if choice == "0":
            print("\n👋 再见!")
            break

        elif choice == "1":
            asr_text = input("请输入 ASR 文本 (默认: '好的，已为您打开一体机灯'): ").strip()
            asr_text = asr_text or "好的，已为您打开一体机灯"
            await debug_judge_app(asr_text=asr_text, backend_url=backend_url)

        elif choice == "2":
            await debug_query_generator_app(backend_url=backend_url)

        elif choice == "3":
            scenario = input("请输入场景描述 (默认: 灯光控制测试): ").strip()
            scenario = scenario or """
            测试一体机灯光控制功能：
            1. 语音打开一体机内部灯光
            2. 语音关闭一体机内部灯光
            3. 重复打开测试（幂等性）
            4. 重复关闭测试（幂等性）
            """
            await debug_test_point_extractor_app(scenario=scenario, backend_url=backend_url)

        elif choice == "4":
            prd = input("请输入 PRD 内容 (默认: 灯光控制 PRD): ").strip()
            prd = prd or """
            ## 灯光控制功能需求

            ### 功能描述
            用户可以通过语音控制一体机内部灯光的开关。

            ### 功能点
            1. 打开灯光：用户说"打开一体机灯"，系统应打开灯光
            2. 关闭灯光：用户说"关闭一体机灯"，系统应关闭灯光
            3. 状态查询：用户问"灯光是什么状态"，系统应回答当前状态
            """
            await debug_test_case_designer_app(prd=prd, backend_url=backend_url)

        elif choice == "5":
            # 模拟测试用例列表
            test_cases = [
                {"id": "001", "title": "语音打开一体机内部灯光", "test_result": "Pass"},
                {"id": "002", "title": "语音关闭一体机内部灯光", "test_result": "Pass"},
                {"id": "003", "title": "语音重复打开测试", "test_result": "NotRun"},
                {"id": "004", "title": "语音重复关闭测试", "test_result": "NotRun"},
            ]
            await debug_completion_verifier_app(test_cases=test_cases, backend_url=backend_url)

        elif choice == "6":
            print("\n" + "=" * 60)
            print("📋 App ID 列表")
            print("=" * 60)
            print(f"JUDGE_APP_ID              = {JUDGE_APP_ID}")
            print(f"QUERY_GENERATOR_APP_ID    = {QUERY_GENERATOR_APP_ID}")
            print(f"TEST_POINT_EXTRACTOR_APP_ID = {TEST_POINT_EXTRACTOR_APP_ID}")
            print(f"TEST_CASE_DESIGNER_APP_ID = {TEST_CASE_DESIGNER_APP_ID}")
            print(f"COMPLETION_VERIFIER_APP_ID = {COMPLETION_VERIFIER_APP_ID}")
            print(f"ASR_APP_ID                = {ASR_APP_ID}")
            print("=" * 60)

        else:
            print("❌ 无效选项，请重新输入")


if __name__ == "__main__":
    asyncio.run(main())