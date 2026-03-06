"""
协议解析器
提供物模型协议的解析和格式化功能
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ProtocolParser:
    """协议解析器"""
    
    @staticmethod
    def format_property_definition(property_def: Dict[str, Any]) -> str:
        """
        格式化属性定义为可读文本
        
        Args:
            property_def: 属性定义字典
            
        Returns:
            格式化后的文本
        """
        lines = []
        
        # 基本信息
        prop_id = property_def.get('id', 'unknown')
        prop_name = property_def.get('name', 'unknown')
        lines.append(f"属性ID: {prop_id}")
        lines.append(f"属性名称: {prop_name}")
        
        # 值类型
        value_type = property_def.get('valueType', {})
        type_name = value_type.get('type', 'unknown')
        lines.append(f"数据类型: {type_name}")
        
        # 枚举值
        if type_name == 'enum':
            elements = value_type.get('elements', [])
            if elements:
                lines.append("可选值:")
                for elem in elements:
                    value = elem.get('value', '')
                    text = elem.get('text', '')
                    lines.append(f"  - {value}: {text}")
        
        # 数值范围
        if type_name in ['int', 'float']:
            unit = value_type.get('unit')
            if unit:
                lines.append(f"单位: {unit}")
            
            min_val = value_type.get('min')
            max_val = value_type.get('max')
            if min_val is not None or max_val is not None:
                range_str = f"范围: "
                if min_val is not None:
                    range_str += f"{min_val}"
                range_str += " ~ "
                if max_val is not None:
                    range_str += f"{max_val}"
                lines.append(range_str)
        
        # 描述
        description = property_def.get('description')
        if description:
            lines.append(f"描述: {description}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_property_definitions(
        property_defs: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        批量格式化属性定义
        
        Args:
            property_defs: 属性ID到定义的映射字典
            
        Returns:
            格式化后的文本
        """
        if not property_defs:
            return "无属性定义"
        
        sections = []
        for prop_id, prop_def in property_defs.items():
            formatted = ProtocolParser.format_property_definition(prop_def)
            sections.append(formatted)
        
        return "\n\n".join(sections)
    
    @staticmethod
    def extract_enum_text(property_def: Dict[str, Any], value: Any) -> str:
        """
        从枚举属性定义中提取值对应的文本
        
        Args:
            property_def: 属性定义
            value: 属性值
            
        Returns:
            对应的文本，如果找不到则返回原值的字符串形式
        """
        value_type = property_def.get('valueType', {})
        
        if value_type.get('type') != 'enum':
            return str(value)
        
        elements = value_type.get('elements', [])
        value_str = str(value)
        
        for elem in elements:
            if str(elem.get('value')) == value_str:
                return elem.get('text', value_str)
        
        return value_str
    
    @staticmethod
    def format_property_change(
        property_id: str,
        property_def: Dict[str, Any],
        old_value: Any,
        new_value: Any
    ) -> str:
        """
        格式化属性变化为可读文本
        
        Args:
            property_id: 属性ID
            property_def: 属性定义
            old_value: 旧值
            new_value: 新值
            
        Returns:
            格式化后的变化描述
        """
        prop_name = property_def.get('name', property_id)
        
        # 如果是枚举类型，转换为文本
        value_type = property_def.get('valueType', {})
        if value_type.get('type') == 'enum':
            old_text = ProtocolParser.extract_enum_text(property_def, old_value)
            new_text = ProtocolParser.extract_enum_text(property_def, new_value)
            return f"{prop_name}: {old_text} → {new_text}"
        else:
            # 添加单位（如果有）
            unit = value_type.get('unit', '')
            unit_str = f" {unit}" if unit else ""
            return f"{prop_name}: {old_value}{unit_str} → {new_value}{unit_str}"
