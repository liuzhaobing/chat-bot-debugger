"""
设备协议加载器
负责加载和管理设备物模型协议文件
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class DeviceProtocolLoader:
    """设备协议加载器"""

    def __init__(self, protocols_dir: str = None):
        """
        初始化协议加载器

        Args:
            protocols_dir: 协议文件目录路径
        """
        if protocols_dir is None:
            # 默认使用 backend/device_protocols/protocols 目录
            current_dir = Path(__file__).parent
            protocols_dir = current_dir.parent.parent.parent.parent / "backend" / "device_protocols" / "protocols"

        self.protocols_dir = Path(protocols_dir)
        self._protocol_cache = {}

        logger.info(f"DeviceProtocolLoader initialized with dir: {self.protocols_dir}")

    def get_protocol(self, device_type: str) -> Optional[Dict[str, Any]]:
        """
        获取指定设备类型的协议

        Args:
            device_type: 设备类型

        Returns:
            协议字典
        """
        if device_type in self._protocol_cache:
            return self._protocol_cache[device_type]

        protocol_file = self.protocols_dir / f"{device_type}物模型协议.json"

        if not protocol_file.exists():
            logger.warning(f"Protocol file not found: {protocol_file}")
            return None

        try:
            with open(protocol_file, 'r', encoding='utf-8') as f:
                protocol = json.load(f)

            self._protocol_cache[device_type] = protocol
            logger.info(f"Protocol loaded: {device_type}")

            return protocol

        except Exception as e:
            logger.error(f"Failed to load protocol {device_type}: {e}")
            return None

    def list_protocols(self) -> List[str]:
        """列出所有可用的协议"""
        protocols = []

        if not self.protocols_dir.exists():
            logger.warning(f"Protocols directory not found: {self.protocols_dir}")
            return protocols

        for file_path in self.protocols_dir.glob("*物模型协议.json"):
            device_type = file_path.stem.replace("物模型协议", "")
            protocols.append(device_type)

        return protocols

    def get_properties(self, device_type: str) -> List[Dict[str, Any]]:
        """获取设备的属性定义列表"""
        protocol = self.get_protocol(device_type)
        if not protocol:
            return []
        return protocol.get('properties', [])

    def get_property_by_id(self, device_type: str, property_id: str) -> Optional[Dict[str, Any]]:
        """根据属性ID获取属性定义"""
        properties = self.get_properties(device_type)
        for prop in properties:
            if prop.get('id') == property_id:
                return prop
        return None

    def get_functions(self, device_type: str) -> List[Dict[str, Any]]:
        """获取设备的功能定义列表"""
        protocol = self.get_protocol(device_type)
        if not protocol:
            return []
        return protocol.get('functions', [])

    def get_function_by_id(self, device_type: str, function_id: str) -> Optional[Dict[str, Any]]:
        """根据功能ID获取功能定义"""
        functions = self.get_functions(device_type)
        for func in functions:
            if func.get('id') == function_id:
                return func
        return None

    def extract_property_definitions(
        self,
        device_type: str,
        property_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """批量提取指定属性ID的定义"""
        result = {}
        properties = self.get_properties(device_type)
        property_map = {prop.get('id'): prop for prop in properties}

        for prop_id in property_ids:
            if prop_id in property_map:
                result[prop_id] = property_map[prop_id]

        return result