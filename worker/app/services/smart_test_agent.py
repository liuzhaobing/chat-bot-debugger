"""
智能测试Agent - 具备完整的Planning能力
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from app.services.agent_service import AgenticTestAgent
from app.services.scenario_generator import ScenarioGenerator
from app.services.verifiers import IOTStateVerifier, VerificationStatus
from app.services.device_protocols import DeviceProtocolLoader
from app.models.session import AgenticTestSession
from app.models.log import AgenticTestLog
from app.core.database import get_db_context
from sqlalchemy import select

logger = logging.getLogger(__name__)


class TaskStatus:
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SmartTestAgent(AgenticTestAgent):
    """
    智能测试Agent - 扩展基础Agent，增加Planning能力

    能力:
    1. 理解宏观任务意图
    2. 设备定位和GUID识别
    3. 协议加载和分析
    4. 测试场景生成
    5. 任务分解和执行
    6. 测试报告生成
    """

    def __init__(self, session_id: str, send_callback: Callable, iot_config: Dict[str, str] = None):
        """初始化智能测试Agent"""
        super().__init__(session_id, send_callback, iot_config)

        # Planning相关
        self.task_description = ""
        self.target_device_guid = None
        self.target_device_name = None
        self.target_device_type = None
        self.device_protocol = None

        # 场景生成器
        self.scenario_generator = ScenarioGenerator()
        self.protocol_loader = DeviceProtocolLoader()

        # 测试场景和任务
        self.test_scenarios = []
        self.current_scenario_index = 0
        self.scenario_results = []

        # 测试报告
        self.test_report = {
            'task_description': '',
            'start_time': None,
            'end_time': None,
            'device_info': {},
            'scenarios': [],
            'summary': {}
        }

        logger.info(f"SmartTestAgent initialized for session {session_id}")

    async def accept_task(self, task_description: str):
        """
        接受测试任务

        Args:
            task_description: 测试组长派发的宏观任务描述
        """
        self.task_description = task_description
        self.test_report['task_description'] = task_description
        self.test_report['start_time'] = datetime.now().isoformat()

        await self.send_callback('task_received', f'收到测试任务: {task_description}')
        await self.log_event('task_received', task_description)

        await self._analyze_task()

    async def _analyze_task(self):
        """分析任务意图"""
        await self.send_callback('status', '正在分析任务意图...')

        try:
            task_lower = self.task_description.lower()

            # 设备关键词匹配
            device_keywords = {
                'cq928': ('一体机', 'CQ928'),
                '蒸烤': ('一体机', None),
                '油烟机': ('油烟机', None),
                'w760': ('洗碗机', 'W760'),
                '洗碗机': ('洗碗机', None)
            }

            detected_device_type = None
            detected_device_model = None

            for keyword, (device_type, model) in device_keywords.items():
                if keyword in task_lower:
                    detected_device_type = device_type
                    detected_device_model = model
                    break

            if not detected_device_type:
                await self.send_callback('error', '无法识别设备类型，请明确指定设备')
                return

            await self.send_callback('task_analyzed', f'识别到设备类型: {detected_device_type}', {
                'device_type': detected_device_type,
                'device_model': detected_device_model
            })

            await self._locate_device(detected_device_type, detected_device_model)

        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            await self.send_callback('error', f'任务分析失败: {str(e)}')

    async def _locate_device(self, device_type: str, device_model: Optional[str] = None):
        """定位目标设备"""
        await self.send_callback('status', f'正在定位{device_type}设备...')

        try:
            if not self.iot_config.get('token') or not self.iot_config.get('familyId'):
                raise RuntimeError(
                    f"[MOCK 已删除] 无法定位设备：IOT配置不完整。"
                    f"token={'已设置' if self.iot_config.get('token') else '未设置'}, "
                    f"familyId={'已设置' if self.iot_config.get('familyId') else '未设置'}"
                )

            devices_result = await self.iot_service.get_family_devices(
                self.iot_config['familyId'],
                self.iot_config['token']
            )

            if devices_result.get('success', False) or devices_result.get('rc') == 0:
                devices = devices_result.get('data', [])

                matched_device = None
                for device in devices:
                    device_name = device.get('name', '')
                    device_dt = device.get('dt', '')
                    category = device.get('categoryName', '')

                    if device_model and device_model.upper() in device_dt.upper():
                        matched_device = device
                        break
                    elif device_type in category or device_type in device_name:
                        matched_device = device
                        break

                if matched_device:
                    self.target_device_guid = matched_device.get('deviceGuid')
                    self.target_device_name = matched_device.get('name')
                    self.target_device_type = device_type

                    await self.send_callback('device_located', f'已定位设备: {self.target_device_name}', {
                        'device_guid': self.target_device_guid,
                        'device_name': self.target_device_name,
                        'device_type': self.target_device_type
                    })
                else:
                    raise RuntimeError(
                        f"[MOCK 已删除] 未找到匹配的{device_type}设备。"
                        f"可用设备: {[d.get('name') for d in devices]}"
                    )

            self.test_report['device_info'] = {
                'device_guid': self.target_device_guid,
                'device_name': self.target_device_name,
                'device_type': self.target_device_type
            }

            await self._load_device_protocol()

        except Exception as e:
            logger.error(f"Device location failed: {e}")
            await self.send_callback('error', f'设备定位失败: {str(e)}')

    async def _load_device_protocol(self):
        """加载设备协议"""
        await self.send_callback('status', f'正在加载{self.target_device_type}协议...')

        try:
            self.device_protocol = self.protocol_loader.get_protocol(self.target_device_type)

            if self.device_protocol:
                properties_count = len(self.device_protocol.get('properties', []))
                functions_count = len(self.device_protocol.get('functions', []))

                await self.send_callback('protocol_loaded', '协议加载成功', {
                    'device_type': self.target_device_type,
                    'properties_count': properties_count,
                    'functions_count': functions_count
                })

                await self._generate_test_scenarios()
            else:
                await self.send_callback('warning', f'未找到{self.target_device_type}的协议文件')

        except Exception as e:
            logger.error(f"Protocol loading failed: {e}")
            await self.send_callback('error', f'协议加载失败: {str(e)}')

    async def _generate_test_scenarios(self):
        """生成测试场景"""
        await self.send_callback('status', '正在生成测试场景...')

        try:
            test_focus = None
            if '语音控制' in self.task_description:
                test_focus = '语音控制'

            self.test_scenarios = self.scenario_generator.generate_scenarios_from_protocol(
                self.target_device_type,
                test_focus
            )

            if self.test_scenarios:
                await self.send_callback('scenarios_generated', f'已生成{len(self.test_scenarios)}个测试场景', {
                    'scenario_count': len(self.test_scenarios),
                    'scenarios': [
                        {
                            'id': s['scenario_id'],
                            'name': s['scenario_name'],
                            'priority': s['priority'],
                            'category': s['category']
                        }
                        for s in self.test_scenarios[:10]
                    ]
                })

                await self._start_test_execution()
            else:
                await self.send_callback('warning', '未能生成测试场景')

        except Exception as e:
            logger.error(f"Scenario generation failed: {e}")
            await self.send_callback('error', f'场景生成失败: {str(e)}')

    async def _start_test_execution(self):
        """开始执行测试"""
        await self.send_callback('status', '开始执行测试场景...')
        self.is_running = True
        self.current_scenario_index = 0

        while self.is_running and self.current_scenario_index < len(self.test_scenarios):
            scenario = self.test_scenarios[self.current_scenario_index]

            await self.send_callback('test_step', f'执行场景: {scenario["scenario_name"]}', {
                'scenario_index': self.current_scenario_index + 1,
                'total_scenarios': len(self.test_scenarios),
                'scenario': scenario
            })

            result = await self._execute_scenario(scenario)
            self.scenario_results.append(result)

            await self.send_callback('scenario_result', '场景执行完成', result)

            self.current_scenario_index += 1
            await asyncio.sleep(2.0)

        await self._generate_test_report()

    async def _execute_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试场景"""
        scenario_result = {
            'scenario_id': scenario['scenario_id'],
            'scenario_name': scenario['scenario_name'],
            'query': scenario['query'],
            'start_time': datetime.now().isoformat(),
            'status': TaskStatus.IN_PROGRESS,
            'conversations': [],
            'verification': None
        }

        try:
            self.current_query = scenario['query']

            # 获取控制前的设备状态
            before_status = await self._get_current_device_status()

            # 执行Agent循环
            await self.execute_full_loop()

            # 等待处理
            await asyncio.sleep(5.0)

            # 获取控制后的设备状态
            after_status = await self._get_current_device_status()

            # 验证结果
            verification_result = await self._verify_scenario_result(
                scenario,
                before_status,
                after_status
            )

            scenario_result['verification'] = verification_result
            scenario_result['status'] = TaskStatus.COMPLETED if verification_result.get('passed') else TaskStatus.FAILED
            scenario_result['end_time'] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Scenario execution failed: {e}")
            scenario_result['status'] = TaskStatus.FAILED
            scenario_result['error'] = str(e)
            scenario_result['end_time'] = datetime.now().isoformat()

        return scenario_result

    async def _get_current_device_status(self) -> Dict[str, Any]:
        """获取当前设备状态"""
        try:
            if self.target_device_guid and self.iot_config.get('token'):
                status_result = await self.iot_service.get_device_status(
                    [self.target_device_guid],
                    self.iot_config['token']
                )

                if status_result.get('success', False) or status_result.get('rc') == 0:
                    data = status_result.get('data', [])
                    if data:
                        return data[0].get('properties', {})

            return {}

        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            return {}

    async def _verify_scenario_result(
        self,
        scenario: Dict[str, Any],
        before_status: Dict[str, Any],
        after_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证场景执行结果"""
        try:
            verifier = IOTStateVerifier(self.iot_service, self.protocol_loader)

            result = await verifier.verify_state_change(
                device_guid=self.target_device_guid,
                before_properties=before_status,
                after_properties=after_status,
                device_type=self.target_device_type,
                query=scenario['query'],
                expectation=f"设备应该{scenario['scenario_name']}",
                expected_changes=scenario.get('expected_state_changes', {})
            )

            return {
                'passed': result.status == VerificationStatus.SUCCESS,
                'status': result.status.value,
                'message': result.message,
                'confidence': result.confidence,
                'property_changes': [
                    {
                        'property_id': change.property_id,
                        'property_name': change.property_name,
                        'previous_value': change.previous_value,
                        'current_value': change.current_value,
                        'is_expected': change.is_expected
                    }
                    for change in result.property_changes
                ]
            }

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                'passed': False,
                'status': 'error',
                'message': f'验证失败: {str(e)}',
                'confidence': 0.0
            }

    async def _generate_test_report(self):
        """生成测试报告"""
        await self.send_callback('status', '正在生成测试报告...')

        try:
            self.test_report['end_time'] = datetime.now().isoformat()
            self.test_report['scenarios'] = self.scenario_results

            total_scenarios = len(self.scenario_results)
            passed_scenarios = sum(
                1 for r in self.scenario_results
                if r.get('status') == TaskStatus.COMPLETED and r.get('verification', {}).get('passed')
            )
            failed_scenarios = sum(
                1 for r in self.scenario_results
                if r.get('status') == TaskStatus.FAILED or not r.get('verification', {}).get('passed')
            )

            pass_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0

            self.test_report['summary'] = {
                'total_scenarios': total_scenarios,
                'passed': passed_scenarios,
                'failed': failed_scenarios,
                'pass_rate': round(pass_rate, 2),
                'duration_seconds': self._calculate_duration()
            }

            await self.send_callback('test_report', '测试报告已生成', self.test_report)
            await self.log_event('test_report', json.dumps(self.test_report, ensure_ascii=False))

            logger.info(f"Test report: {passed_scenarios}/{total_scenarios} passed ({pass_rate:.1f}%)")

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            await self.send_callback('error', f'报告生成失败: {str(e)}')

    def _calculate_duration(self) -> float:
        """计算测试持续时间（秒）"""
        try:
            if self.test_report['start_time'] and self.test_report['end_time']:
                start = datetime.fromisoformat(self.test_report['start_time'])
                end = datetime.fromisoformat(self.test_report['end_time'])
                return (end - start).total_seconds()
        except:
            pass
        return 0.0

    @staticmethod
    def identify_target_device_guid(query: str, devices: List[Dict[str, Any]]) -> Optional[str]:
        """从query中识别要操作的设备GUID"""
        query_lower = query.lower()

        device_keywords = {
            '油烟机': ['油烟机', '抽油烟机', '烟机'],
            '一体机': ['一体机', '蒸烤', '烤箱', 'cq928'],
            '洗碗机': ['洗碗机', 'w760'],
            '燃气灶': ['燃气灶', '灶具', '灶台'],
            '翻炒锅': ['翻炒锅', '炒锅']
        }

        for device_type, keywords in device_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                for device in devices:
                    category = device.get('categoryName', '')
                    name = device.get('name', '')

                    if device_type in category or device_type in name:
                        return device.get('deviceGuid')

        if devices:
            return devices[0].get('deviceGuid')

        return None