"""
测试工程师服务 - 测试报告生成器

负责生成测试报告，支持多种格式输出。
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    TestReport,
    TestCase,
    Defect,
    TestCaseStatistics,
    DefectStatistics,
    SessionInfo,
    TestResultStatus,
)

logger = logging.getLogger(__name__)


class TestReporter:
    """测试报告生成器

    生成测试执行报告，支持：
    - Markdown格式
    - HTML格式
    - JSON格式
    """

    def __init__(self):
        """初始化报告生成器"""
        pass

    async def generate_report(
        self,
        test_cases: List[TestCase],
        defects: List[Defect],
        session_info: SessionInfo
    ) -> TestReport:
        """生成测试报告

        Args:
            test_cases: 测试用例列表
            defects: 缺陷列表
            session_info: 会话信息

        Returns:
            测试报告对象
        """
        # 统计用例
        case_stats = self._calculate_case_statistics(test_cases)

        # 统计缺陷
        defect_stats = self._calculate_defect_statistics(defects)

        # 生成摘要
        summary = self._generate_summary(case_stats, defect_stats, session_info)

        report = TestReport(
            session_info=session_info,
            case_statistics=case_stats,
            defect_statistics=defect_stats,
            test_cases=test_cases,
            defects=defects,
            generated_at=datetime.now(),
            summary=summary,
        )

        logger.info(f"Generated test report: {case_stats.passed}/{case_stats.total} passed")
        return report

    def _calculate_case_statistics(self, test_cases: List[TestCase]) -> TestCaseStatistics:
        """计算用例统计

        Args:
            test_cases: 测试用例列表

        Returns:
            用例统计对象
        """
        stats = TestCaseStatistics(total=len(test_cases))

        for case in test_cases:
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

    def _calculate_defect_statistics(self, defects: List[Defect]) -> DefectStatistics:
        """计算缺陷统计

        Args:
            defects: 缺陷列表

        Returns:
            缺陷统计对象
        """
        from .models import Severity

        stats = DefectStatistics(total=len(defects))

        for defect in defects:
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

            if defect.status == "open":
                stats.open_count += 1
            elif defect.status == "fixed":
                stats.fixed_count += 1
            elif defect.status == "closed":
                stats.closed_count += 1

        return stats

    def _generate_summary(
        self,
        case_stats: TestCaseStatistics,
        defect_stats: DefectStatistics,
        session_info: SessionInfo
    ) -> str:
        """生成测试摘要

        Args:
            case_stats: 用例统计
            defect_stats: 缺陷统计
            session_info: 会话信息

        Returns:
            摘要文本
        """
        lines = [
            f"## 测试执行摘要",
            f"",
            f"- **测试会话**: {session_info.session_id}",
            f"- **执行时间**: {session_info.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **执行时长**: {session_info.duration_seconds:.1f} 秒",
            f"- **测试环境**: {session_info.iot_env}",
            f"",
            f"### 测试用例统计",
            f"",
            f"| 状态 | 数量 | 占比 |",
            f"|:-----|:----:|:----:|",
            f"| 总计 | {case_stats.total} | 100% |",
            f"| 通过 | {case_stats.passed} | {case_stats.pass_rate:.1f}% |",
            f"| 失败 | {case_stats.failed} | {case_stats.failed/case_stats.total*100 if case_stats.total else 0:.1f}% |",
            f"| 阻塞 | {case_stats.blocked} | {case_stats.blocked/case_stats.total*100 if case_stats.total else 0:.1f}% |",
            f"| 跳过 | {case_stats.skipped} | {case_stats.skipped/case_stats.total*100 if case_stats.total else 0:.1f}% |",
            f"| 未执行 | {case_stats.not_run} | {case_stats.not_run/case_stats.total*100 if case_stats.total else 0:.1f}% |",
        ]

        if defect_stats.total > 0:
            lines.extend([
                f"",
                f"### 缺陷统计",
                f"",
                f"| 严重程度 | 数量 |",
                f"|:---------|:----:|",
                f"| 致命 | {defect_stats.critical} |",
                f"| 严重 | {defect_stats.major} |",
                f"| 一般 | {defect_stats.normal} |",
                f"| 轻微 | {defect_stats.minor} |",
                f"| 建议 | {defect_stats.suggestion} |",
            ])

        return "\n".join(lines)

    async def export_to_markdown(self, report: TestReport) -> str:
        """导出为Markdown格式

        Args:
            report: 测试报告

        Returns:
            Markdown文本
        """
        lines = [
            f"# 测试报告",
            f"",
            f"> 生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            report.summary,
            f"",
            f"---",
            f"",
            f"## 测试用例详情",
            f"",
        ]

        # 用例详情表格
        lines.extend([
            f"| 用例ID | 模块 | 标题 | 类型 | 状态 |",
            f"|:-------|:-----|:-----|:----:|:----:|",
        ])

        for case in report.test_cases:
            status_emoji = {
                TestResultStatus.PASS: "✅",
                TestResultStatus.FAIL: "❌",
                TestResultStatus.BLOCKED: "🚫",
                TestResultStatus.SKIPPED: "⏭️",
                TestResultStatus.NOT_RUN: "⬜",
            }.get(case.test_result, "❓")

            lines.append(
                f"| {case.id} | {case.module} | {case.title} | {case.type.value} | {status_emoji} {case.test_result.value} |"
            )

        # 失败用例详情
        failed_cases = [c for c in report.test_cases if c.test_result == TestResultStatus.FAIL]
        if failed_cases:
            lines.extend([
                f"",
                f"## 失败用例详情",
                f"",
            ])

            for case in failed_cases:
                lines.extend([
                    f"### {case.id}: {case.title}",
                    f"",
                    f"**预期结果**:",
                    f"",
                ])
                for result in case.expect_results:
                    lines.append(f"- {result}")

                lines.extend([
                    f"",
                    f"**实际结果**:",
                    f"",
                ])
                if case.actual_results:
                    for result in case.actual_results:
                        lines.append(f"- {result}")
                else:
                    lines.append(f"- 无")

                if case.error_message:
                    lines.extend([
                        f"",
                        f"**错误信息**: {case.error_message}",
                    ])

                lines.append("")

        # 缺陷详情
        if report.defects:
            lines.extend([
                f"## 缺陷列表",
                f"",
                f"| 缺陷ID | 用例ID | 类型 | 严重程度 | 描述 | 状态 |",
                f"|:-------|:-------|:-----|:---------|:-----|:----:|",
            ])

            for defect in report.defects:
                lines.append(
                    f"| {defect.id} | {defect.case_id} | {defect.defect_type.value} | "
                    f"{defect.severity.value} | {defect.description[:50]}... | {defect.status} |"
                )

        return "\n".join(lines)

    async def export_to_html(self, report: TestReport) -> str:
        """导出为HTML格式

        Args:
            report: 测试报告

        Returns:
            HTML文本
        """
        md_content = await self.export_to_markdown(report)

        # 简单的Markdown到HTML转换
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>测试报告</title>",
            "    <style>",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }",
            "        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
            "        h2 { color: #555; margin-top: 30px; }",
            "        table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "        th { background-color: #4CAF50; color: white; }",
            "        tr:nth-child(even) { background-color: #f2f2f2; }",
            "        .pass { color: #4CAF50; }",
            "        .fail { color: #f44336; }",
            "        .blocked { color: #ff9800; }",
            "        blockquote { background-color: #f9f9f9; border-left: 4px solid #ccc; padding: 10px 20px; }",
            "    </style>",
            "</head>",
            "<body>",
        ]

        # 转换Markdown内容
        for line in md_content.split('\n'):
            if line.startswith('# '):
                html_lines.append(f"    <h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"    <h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"    <h3>{line[4:]}</h3>")
            elif line.startswith('| '):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if all(c.replace(':', '').replace('-', '') == '' for c in cells):
                    continue  # 跳过分隔行
                html_lines.append("    <tr>")
                for cell in cells:
                    html_lines.append(f"        <td>{cell}</td>")
                html_lines.append("    </tr>")
            elif line.startswith('> '):
                html_lines.append(f"    <blockquote>{line[2:]}</blockquote>")
            elif line.startswith('- '):
                html_lines.append(f"    <li>{line[2:]}</li>")
            elif line.strip():
                html_lines.append(f"    <p>{line}</p>")

        html_lines.extend([
            "</body>",
            "</html>",
        ])

        return "\n".join(html_lines)

    async def export_to_json(self, report: TestReport) -> str:
        """导出为JSON格式

        Args:
            report: 测试报告

        Returns:
            JSON字符串
        """
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    async def export_report(
        self,
        report: TestReport,
        format: str = "markdown"
    ) -> str:
        """导出报告

        Args:
            report: 测试报告
            format: 输出格式（markdown, html, json）

        Returns:
            报告内容
        """
        if format == "markdown":
            return await self.export_to_markdown(report)
        elif format == "html":
            return await self.export_to_html(report)
        elif format == "json":
            return await self.export_to_json(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def save_report(
        self,
        report: TestReport,
        file_path: str,
        format: str = "markdown"
    ) -> bool:
        """保存报告到文件

        Args:
            report: 测试报告
            file_path: 文件路径
            format: 输出格式

        Returns:
            是否保存成功
        """
        try:
            content = await self.export_report(report, format)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Report saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False