"""
调试脚本 - process_brain 函数

用于独立调试 AgenticTestAgent.process_brain 方法
直接导入原始代码，修改后无需同步

运行方式:
    cd worker
    python scripts/debug_process_brain.py
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# 添加 worker 目录到 Python 路径
worker_dir = Path(__file__).parent.parent
sys.path.insert(0, str(worker_dir))


# ============================================================================
# 从原文件导入
# ============================================================================
from app.services.agent_service import AgenticTestAgent, BrainProcessResult


# ============================================================================
# 创建用于调试的 Agent 子类
# ============================================================================

class DebugAgenticTestAgent(AgenticTestAgent):
    """用于调试的 Agent 子类，重写依赖外部服务的方法"""

    def __init__(self):
        # 调用父类初始化，但使用 mock 的参数
        super().__init__(
            session_id="debug_session_001",
            send_callback=self._mock_send_callback,
            iot_config={'token': '', 'familyId': '', 'env': 'test'}
        )

        # 存储所有回调消息，便于调试
        self.callback_log: list = []

    async def _mock_send_callback(self, event_type: str, message: Any, metadata: Any = None):
        """模拟的回调函数"""
        log_entry = {
            'event_type': event_type,
            'message': message,
            'metadata': metadata
        }
        self.callback_log.append(log_entry)
        print(f"[Callback] {event_type}: {message}")
        if metadata:
            print(f"          metadata: {metadata}")

    async def log_event(self, log_type: str, content: str, metadata: Optional[dict] = None):
        """重写日志记录，跳过数据库操作"""
        print(f"[LogEvent] {log_type}: {content}")
        if metadata:
            print(f"           metadata: {metadata}")


# ============================================================================
# 测试用例
# ============================================================================

async def test_normal_input():
    """测试正常输入"""
    print("\n" + "=" * 60)
    print("测试用例: 正常输入")
    print("=" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 1

    result = await agent.process_brain("打开油烟机")

    print("\n结果:")
    print(f"  success: {result.success}")
    print(f"  next_query: {result.next_query}")
    print(f"  should_continue: {result.should_continue}")
    print(f"  ai_response: {result.ai_response}")
    print(f"  analysis: {result.analysis}")

    return result


async def test_noise_input():
    """测试噪音输入"""
    print("\n" + "=" * 60)
    print("测试用例: 噪音输入 (<noise>)")
    print("=" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 1

    result = await agent.process_brain("<noise>")

    print("\n结果:")
    print(f"  success: {result.success}")
    print(f"  next_query: {result.next_query}")
    print(f"  should_continue: {result.should_continue}")
    print(f"  ai_response: {result.ai_response}")
    print(f"  analysis: {result.analysis}")

    return result


async def test_with_context():
    """测试带上下文的输入"""
    print("\n" + "=" * 60)
    print("测试用例: 带上下文的输入")
    print("=" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 5
    agent.current_query = "上一轮的查询内容"

    context = {
        'current_query': agent.current_query,
        'loop_step': agent.loop_step,
        'device_status': {
            'current': {'device_1': {'power': 'on'}},
            'previous': {'device_1': {'power': 'off'}}
        }
    }

    result = await agent.process_brain("把灯关掉", context)

    print("\n结果:")
    print(f"  success: {result.success}")
    print(f"  next_query: {result.next_query}")
    print(f"  should_continue: {result.should_continue}")
    print(f"  ai_response: {result.ai_response}")
    print(f"  analysis: {result.analysis}")

    return result


async def test_empty_input():
    """测试空输入"""
    print("\n" + "=" * 60)
    print("测试用例: 空输入")
    print("=" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 1

    result = await agent.process_brain("")

    print("\n结果:")
    print(f"  success: {result.success}")
    print(f"  next_query: {result.next_query}")
    print(f"  should_continue: {result.should_continue}")
    print(f"  ai_response: {result.ai_response}")

    return result


async def test_chinese_input():
    """测试中文输入"""
    print("\n" + "=" * 60)
    print("测试用例: 中文输入 (复杂场景)")
    print("=" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 1

    test_cases = [
        "帮我打开厨房的灯",
        "把空调温度调到26度",
        "我想听一首周杰伦的歌",
        "今天天气怎么样",
    ]

    for text in test_cases:
        print(f"\n输入: {text}")
        result = await agent.process_brain(text)
        print(f"输出: next_query={result.next_query}, should_continue={result.should_continue}")

    return result


async def interactive_debug():
    """交互式调试模式"""
    print("\n" + "=" * 60)
    print("交互式调试模式")
    print("=" * 60)
    print("输入 ASR 文本进行调试，输入 'quit' 或 'exit' 退出")
    print("-" * 60)

    agent = DebugAgenticTestAgent()
    agent.loop_step = 1

    while True:
        try:
            user_input = input("\n请输入 ASR 文本: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("退出交互模式")
                break

            if not user_input:
                print("输入为空，请重新输入")
                continue

            print("\n处理中...")
            result = await agent.process_brain(user_input)

            print("\n处理结果:")
            print(f"  success: {result.success}")
            print(f"  next_query: {result.next_query}")
            print(f"  should_continue: {result.should_continue}")
            print(f"  ai_response: {result.ai_response}")
            if result.analysis:
                print(f"  analysis: {result.analysis}")
            if result.error_message:
                print(f"  error: {result.error_message}")

        except KeyboardInterrupt:
            print("\n\n退出交互模式")
            break
        except Exception as e:
            print(f"错误: {e}")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""
    print("=" * 60)
    print("process_brain 函数调试脚本")
    print("=" * 60)

    print("\n选择运行模式:")
    print("  1. 运行所有预设测试用例")
    print("  2. 交互式调试")
    print("  3. 单独测试正常输入")
    print("  4. 单独测试噪音输入")
    print("  5. 单独测试带上下文输入")

    try:
        choice = input("\n请输入选择 (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n退出")
        return

    if choice == '1':
        await test_normal_input()
        await test_noise_input()
        await test_with_context()
        await test_empty_input()
        await test_chinese_input()
    elif choice == '2':
        await interactive_debug()
    elif choice == '3':
        await test_normal_input()
    elif choice == '4':
        await test_noise_input()
    elif choice == '5':
        await test_with_context()
    else:
        print("无效选择，运行默认测试...")
        await test_normal_input()

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())