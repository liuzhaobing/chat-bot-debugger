"""
测试报告生成器模块

功能:
- 收集测试结果
- 分析测试数据
- 生成测试报告
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationDetail:
    """对话详情"""
    round_number: int
    query: str
    tts_audio_length: int
    asr_result: str
    vad_confidence: float
    device_status_before: Dict[str, Any]
    device_status_after: Dict[str, Any]
    judge_result: Dict[str, Any]
    timestamp: str


@dataclass
class ScenarioTestDetail:
    """场景测试详情"""
    scenario_id: str
    scenario_name: str
    category: str
    priority: int
    status: str  # success/failed/skipped
    start_time: str
    end_time: str
    duration_seconds: float
    conversations: List[ConversationDetail]
    verification_result: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class TaskTestSummary:
    """任务测试概况"""
    task_description: str
    device_guid: str
    device_name: str
    device_type: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    pass_rate: float
    total_conversations: int
    start_time: str
    end_time: str
    duration_seconds: float


@dataclass
class TestReport:
    """完整测试报告"""
    report_id: str
    task_summary: TaskTestSummary
    scenario_details: List[ScenarioTestDetail]
    conversation_details: List[ConversationDetail]
    generated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'task_summary': asdict(self.task_summary),
            'scenario_details': [asdict(s) for s in self.scenario_details],
            'conversation_details': [asdict(c) for c in self.conversation_details],
            'generated_at': self.generated_at
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        pass
    
    def generate_report(
        self,
        task_description: str,
        device_info: Dict[str, Any],
        scenario_results: List[Dict[str, Any]],
        start_time: str,
        end_time: str
    ) -> TestReport:
        """
        生成测试报告
        
        Args:
            task_description: 任务描述
            device_info: 设备信息
            scenario_results: 场景测试结果列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            TestReport对象
        """
        try:
            # 生成报告ID
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 收集所有对话详情
            all_conversations = []
            for scenario in scenario_results:
                conversations = scenario.get('conversations', [])
                for conv in conversations:
                    all_conversations.append(ConversationDetail(
                        round_number=conv.get('round_number', 0),
                        query=conv.get('query', ''),
                        tts_audio_length=conv.get('tts_audio_length', 0),
                        asr_result=conv.get('asr_result', ''),
                        vad_confidence=conv.get('vad_confidence', 0.0),
                        device_status_before=conv.get('device_status_before', {}),
                        device_status_after=conv.get('device_status_after', {}),
                        judge_result=conv.get('judge_result', {}),
                        timestamp=conv.get('timestamp', '')
                    ))
            
            # 生成场景详情
            scenario_details = []
            for scenario in scenario_results:
                conversations = []
                for conv in scenario.get('conversations', []):
                    conversations.append(ConversationDetail(
                        round_number=conv.get('round_number', 0),
                        query=conv.get('query', ''),
                        tts_audio_length=conv.get('tts_audio_length', 0),
                        asr_result=conv.get('asr_result', ''),
                        vad_confidence=conv.get('vad_confidence', 0.0),
                        device_status_before=conv.get('device_status_before', {}),
                        device_status_after=conv.get('device_status_after', {}),
                        judge_result=conv.get('judge_result', {}),
                        timestamp=conv.get('timestamp', '')
                    ))
                
                scenario_details.append(ScenarioTestDetail(
                    scenario_id=scenario.get('scenario_id', ''),
                    scenario_name=scenario.get('scenario_name', ''),
                    category=scenario.get('category', 'unknown'),
                    priority=scenario.get('priority', 5),
                    status=scenario.get('status', 'unknown'),
                    start_time=scenario.get('start_time', ''),
                    end_time=scenario.get('end_time', ''),
                    duration_seconds=scenario.get('duration_seconds', 0.0),
                    conversations=conversations,
                    verification_result=scenario.get('verification', {}),
                    error_message=scenario.get('error')
                ))
            
            # 计算统计信息
            total_scenarios = len(scenario_results)
            passed_scenarios = sum(1 for s in scenario_results if s.get('status') == 'completed' and s.get('verification', {}).get('passed'))
            failed_scenarios = sum(1 for s in scenario_results if s.get('status') == 'failed' or not s.get('verification', {}).get('passed'))
            skipped_scenarios = sum(1 for s in scenario_results if s.get('status') == 'skipped')
            pass_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0.0
            
            # 计算持续时间
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                duration_seconds = (end_dt - start_dt).total_seconds()
            except:
                duration_seconds = 0.0
            
            # 生成任务概况
            task_summary = TaskTestSummary(
                task_description=task_description,
                device_guid=device_info.get('device_guid', ''),
                device_name=device_info.get('device_name', ''),
                device_type=device_info.get('device_type', ''),
                total_scenarios=total_scenarios,
                passed_scenarios=passed_scenarios,
                failed_scenarios=failed_scenarios,
                skipped_scenarios=skipped_scenarios,
                pass_rate=round(pass_rate, 2),
                total_conversations=len(all_conversations),
                start_time=start_time,
                end_time=end_time,
                duration_seconds=round(duration_seconds, 2)
            )
            
            # 生成完整报告
            report = TestReport(
                report_id=report_id,
                task_summary=task_summary,
                scenario_details=scenario_details,
                conversation_details=all_conversations,
                generated_at=datetime.now().isoformat()
            )
            
            logger.info(f"Test report generated: {report_id}, pass_rate={pass_rate:.1f}%")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def generate_summary_text(self, report: TestReport) -> str:
        """
        生成报告摘要文本
        
        Args:
            report: TestReport对象
            
        Returns:
            摘要文本
        """
        summary = report.task_summary
        
        text = f"""
测试报告摘要
============

任务描述: {summary.task_description}
设备信息: {summary.device_name} ({summary.device_type})
设备GUID: {summary.device_guid}

测试结果:
- 总场景数: {summary.total_scenarios}
- 通过场景: {summary.passed_scenarios}
- 失败场景: {summary.failed_scenarios}
- 跳过场景: {summary.skipped_scenarios}
- 通过率: {summary.pass_rate}%

对话统计:
- 总对话轮次: {summary.total_conversations}

时间信息:
- 开始时间: {summary.start_time}
- 结束时间: {summary.end_time}
- 持续时间: {summary.duration_seconds}秒

报告ID: {report.report_id}
生成时间: {report.generated_at}
"""
        return text.strip()
    
    def export_to_markdown(self, report: TestReport, file_path: str):
        """
        导出报告为Markdown格式
        
        Args:
            report: TestReport对象
            file_path: 输出文件路径
        """
        try:
            summary = report.task_summary
            
            md_content = f"""# 测试报告

## 基本信息

- **报告ID**: {report.report_id}
- **生成时间**: {report.generated_at}
- **任务描述**: {summary.task_description}

## 设备信息

- **设备名称**: {summary.device_name}
- **设备类型**: {summary.device_type}
- **设备GUID**: {summary.device_guid}

## 测试概况

| 指标 | 数值 |
|------|------|
| 总场景数 | {summary.total_scenarios} |
| 通过场景 | {summary.passed_scenarios} |
| 失败场景 | {summary.failed_scenarios} |
| 跳过场景 | {summary.skipped_scenarios} |
| 通过率 | {summary.pass_rate}% |
| 总对话轮次 | {summary.total_conversations} |
| 测试时长 | {summary.duration_seconds}秒 |

## 场景详情

"""
            
            for i, scenario in enumerate(report.scenario_details, 1):
                status_emoji = "✅" if scenario.status == "completed" and scenario.verification_result.get('passed') else "❌"
                
                md_content += f"""
### {i}. {scenario.scenario_name} {status_emoji}

- **场景ID**: {scenario.scenario_id}
- **分类**: {scenario.category}
- **优先级**: {scenario.priority}
- **状态**: {scenario.status}
- **开始时间**: {scenario.start_time}
- **结束时间**: {scenario.end_time}
- **持续时间**: {scenario.duration_seconds}秒

"""
                
                if scenario.verification_result:
                    md_content += f"""
**验证结果**:
- 通过: {'是' if scenario.verification_result.get('passed') else '否'}
- 置信度: {scenario.verification_result.get('confidence', 0.0)}
- 消息: {scenario.verification_result.get('message', '')}

"""
                
                if scenario.error_message:
                    md_content += f"""
**错误信息**: {scenario.error_message}

"""
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"Report exported to markdown: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export report to markdown: {e}")
            raise
