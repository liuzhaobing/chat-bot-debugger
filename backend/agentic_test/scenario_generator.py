"""
场景生成器模块 - 根据IOT协议自动生成测试场景

功能:
- 从设备协议中提取功能点
- 生成测试场景
- 优先级排序
"""
import json
import logging
from typing import Dict, List, Any, Optional
from device_protocols import DeviceProtocolLoader
from device_protocols.parser import ProtocolParser

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """测试场景生成器"""
    
    def __init__(self):
        """初始化场景生成器"""
        self.protocol_loader = DeviceProtocolLoader()
        
    def generate_scenarios_from_protocol(
        self,
        device_type: str,
        test_focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        从设备协议生成测试场景
        
        Args:
            device_type: 设备类型（如"油烟机"）
            test_focus: 测试重点（可选）
            
        Returns:
            测试场景列表
        """
        try:
            # 加载设备协议
            protocol = self.protocol_loader.get_protocol(device_type)
            if not protocol:
                logger.error(f"Protocol not found for device type: {device_type}")
                return []
            
            # 提取functions作为测试场景基础
            functions = protocol.get('functions', [])
            properties = protocol.get('properties', [])
            
            scenarios = []
            
            # 从functions生成场景
            for func in functions:
                scenario = self._generate_scenario_from_function(func, properties, device_type)
                if scenario:
                    scenarios.append(scenario)
            
            # 从properties生成场景（针对可写属性）
            for prop in properties:
                if 'write' in prop.get('expands', {}).get('type', []):
                    scenario = self._generate_scenario_from_property(prop, device_type)
                    if scenario:
                        scenarios.append(scenario)
            
            # 按优先级排序
            scenarios = self._prioritize_scenarios(scenarios, test_focus)
            
            logger.info(f"Generated {len(scenarios)} test scenarios for {device_type}")
            return scenarios
            
        except Exception as e:
            logger.error(f"Failed to generate scenarios: {e}")
            return []
    
    def _generate_scenario_from_function(
        self,
        function: Dict[str, Any],
        properties: List[Dict[str, Any]],
        device_type: str
    ) -> Optional[Dict[str, Any]]:
        """从function生成测试场景"""
        try:
            func_id = function.get('id')
            func_name = function.get('name')
            inputs = function.get('inputs', [])
            
            # 生成测试查询
            query = self._generate_query_from_function(func_name, inputs)
            
            # 生成预期状态变化
            expected_changes = self._extract_expected_changes(inputs, properties)
            
            # 生成预期响应关键词
            expected_keywords = self._generate_expected_keywords(func_name)
            
            return {
                'scenario_id': f"{device_type}_{func_id}",
                'scenario_name': func_name,
                'device_type': device_type,
                'function_id': func_id,
                'query': query,
                'expected_state_changes': expected_changes,
                'expected_keywords': expected_keywords,
                'priority': self._calculate_priority(func_name),
                'category': self._categorize_function(func_name)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate scenario from function: {e}")
            return None
    
    def _generate_scenario_from_property(
        self,
        property_def: Dict[str, Any],
        device_type: str
    ) -> Optional[Dict[str, Any]]:
        """从property生成测试场景"""
        try:
            prop_id = property_def.get('id')
            prop_name = property_def.get('name')
            value_type = property_def.get('valueType', {})
            
            # 只为enum类型生成场景
            if value_type.get('type') != 'enum':
                return None
            
            elements = value_type.get('elements', [])
            if not elements:
                return None
            
            # 为每个枚举值生成一个场景
            scenarios = []
            for element in elements[:3]:  # 限制前3个值
                value = element.get('value')
                text = element.get('text')
                
                query = f"设置{prop_name}为{text}"
                
                scenario = {
                    'scenario_id': f"{device_type}_{prop_id}_{value}",
                    'scenario_name': f"设置{prop_name}-{text}",
                    'device_type': device_type,
                    'property_id': prop_id,
                    'query': query,
                    'expected_state_changes': {prop_id: value},
                    'expected_keywords': [text, prop_name, '设置', '成功'],
                    'priority': 2,
                    'category': 'property_control'
                }
                scenarios.append(scenario)
            
            return scenarios[0] if scenarios else None
            
        except Exception as e:
            logger.error(f"Failed to generate scenario from property: {e}")
            return None
    
    def _generate_query_from_function(
        self,
        func_name: str,
        inputs: List[Dict[str, Any]]
    ) -> str:
        """从function名称和输入生成自然语言查询"""
        # 简化的查询生成逻辑
        if '开机' in func_name or '启动' in func_name:
            return "打开设备"
        elif '关机' in func_name or '停止' in func_name:
            return "关闭设备"
        elif '档位' in func_name or '功率' in func_name:
            return "调节档位"
        elif '灯' in func_name or '照明' in func_name:
            return "打开灯光"
        else:
            return func_name
    
    def _extract_expected_changes(
        self,
        inputs: List[Dict[str, Any]],
        properties: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """从inputs提取预期的状态变化"""
        expected_changes = {}
        
        for input_def in inputs:
            input_id = input_def.get('id')
            value_type = input_def.get('valueType', {})
            
            # 如果是enum类型，取第一个有效值
            if value_type.get('type') == 'enum':
                elements = value_type.get('elements', [])
                if elements:
                    expected_changes[input_id] = elements[0].get('value')
        
        return expected_changes
    
    def _generate_expected_keywords(self, func_name: str) -> List[str]:
        """生成预期的响应关键词"""
        keywords = ['好的', '已', '成功']
        
        if '开' in func_name:
            keywords.extend(['打开', '开启'])
        elif '关' in func_name:
            keywords.extend(['关闭', '关掉'])
        elif '设置' in func_name:
            keywords.extend(['设置', '调整'])
        
        return keywords
    
    def _calculate_priority(self, func_name: str) -> int:
        """计算场景优先级 (1-5, 1最高)"""
        # 基础功能优先级最高
        if any(keyword in func_name for keyword in ['开机', '关机', '启动', '停止']):
            return 1
        # 常用功能次之
        elif any(keyword in func_name for keyword in ['档位', '温度', '灯']):
            return 2
        # 高级功能
        elif any(keyword in func_name for keyword in ['定时', '预约', '清洗']):
            return 3
        # 其他功能
        else:
            return 4
    
    def _categorize_function(self, func_name: str) -> str:
        """对功能进行分类"""
        if any(keyword in func_name for keyword in ['开机', '关机', '启动', '停止']):
            return 'power_control'
        elif any(keyword in func_name for keyword in ['档位', '功率', '风速']):
            return 'level_control'
        elif any(keyword in func_name for keyword in ['灯', '照明']):
            return 'light_control'
        elif any(keyword in func_name for keyword in ['定时', '预约']):
            return 'timer_control'
        elif any(keyword in func_name for keyword in ['清洗', '除垢']):
            return 'maintenance'
        else:
            return 'other'
    
    def _prioritize_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
        test_focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """对场景进行优先级排序"""
        # 如果有测试重点，提升相关场景的优先级
        if test_focus:
            for scenario in scenarios:
                if test_focus.lower() in scenario['scenario_name'].lower():
                    scenario['priority'] = max(1, scenario['priority'] - 1)
        
        # 按优先级排序
        return sorted(scenarios, key=lambda x: x['priority'])
