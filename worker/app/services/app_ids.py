"""
App ID 常量定义

所有 App 的 ID 集中管理，便于配置和调试。
"""

# ============================================================================
# 测试工程师服务相关 App IDs
# ============================================================================

# 评判 App - 评判测试执行结果是否满足预期
JUDGE_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"

# 查询生成器 App - 根据测试用例和执行上下文生成下一个测试查询语句
QUERY_GENERATOR_APP_ID = "c7a27bd4e3cf49008ae99fc69817f155"

# 测试点提取 App - 从场景描述/需求文档中提取需要验证的测试点
TEST_POINT_EXTRACTOR_APP_ID = "test_point_extractor"

# 测试用例设计 App - 根据 PRD（产品需求文档）自动设计测试用例
TEST_CASE_DESIGNER_APP_ID = "43281a11ed734cbc9ed7d1e1f18a1f99"

# 完成验证 App - 大模型验证是否所有测试用例都已完成执行
COMPLETION_VERIFIER_APP_ID = "751fcb8cbfa64d19862f223e38406dc2"

# ============================================================================
# 其他服务 App IDs
# ============================================================================

# ASR 语音识别 App
ASR_APP_ID = "4f95e97b0ec641fab9772b68a81bcf4a"

# TTS 语音合成 App（需要配置）
TTS_APP_ID = ""  # 从环境变量配置

# 验证 App
VERIFICATION_APP_ID = "e4d13f457f7f486c99ca11b39a7b8347"


# ============================================================================
# App 信息汇总
# ============================================================================

APP_INFO = {
    "judge": {
        "id": JUDGE_APP_ID,
        "name": "评判 App",
        "description": "评判测试执行结果是否满足预期，判断当前用例是否通过",
        "module": "tester_service.py",
    },
    "query_generator": {
        "id": QUERY_GENERATOR_APP_ID,
        "name": "查询生成器 App",
        "description": "根据测试用例和执行上下文生成下一个测试查询语句",
        "module": "tester_service.py",
    },
    "test_point_extractor": {
        "id": TEST_POINT_EXTRACTOR_APP_ID,
        "name": "测试点提取 App",
        "description": "从场景描述/需求文档中提取需要验证的测试点",
        "module": "tester_service.py",
    },
    "test_case_designer": {
        "id": TEST_CASE_DESIGNER_APP_ID,
        "name": "测试用例设计 App",
        "description": "根据 PRD（产品需求文档）自动设计测试用例",
        "module": "case_manager.py",
    },
    "completion_verifier": {
        "id": COMPLETION_VERIFIER_APP_ID,
        "name": "完成验证 App",
        "description": "大模型验证是否所有测试用例都已完成执行",
        "module": "progressor.py",
    },
    "asr": {
        "id": ASR_APP_ID,
        "name": "ASR 语音识别 App",
        "description": "语音识别服务",
        "module": "asr_service.py",
    },
    "verification": {
        "id": VERIFICATION_APP_ID,
        "name": "验证 App",
        "description": "验证服务",
        "module": "verifiers.py",
    },
}


def get_app_id(app_name: str) -> str:
    """根据 App 名称获取 App ID

    Args:
        app_name: App 名称（如 "judge", "query_generator" 等）

    Returns:
        App ID 字符串
    """
    if app_name in APP_INFO:
        return APP_INFO[app_name]["id"]
    raise ValueError(f"Unknown app name: {app_name}")


def list_apps() -> None:
    """打印所有 App 信息"""
    print("\n" + "=" * 80)
    print("App ID 列表")
    print("=" * 80)
    for name, info in APP_INFO.items():
        print(f"\n{info['name']}:")
        print(f"  名称: {name}")
        print(f"  ID: {info['id']}")
        print(f"  描述: {info['description']}")
        print(f"  模块: {info['module']}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    list_apps()