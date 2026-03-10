"""
IoT 服务
从 backend/agentic_test/services.py 迁移
"""
import asyncio
import logging
import random
from typing import Dict, Any, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class IOTService:
    """物联网设备服务"""
    
    def __init__(self, token: str = "", family_id: str = "", env: str = "test"):
        """初始化IOT服务"""
        self.token = token
        self.family_id = family_id
        self.env = env
        
        self.base_url = settings.iot_base_url_prod if env == "prod" else settings.iot_base_url_test
        
        # 设备状态缓存
        self.device_cache: Dict[str, Any] = {}
        self.last_update_time: Dict[str, float] = {}
        
        logger.info(
            f"IOTService initialized: env={env}, base_url={self.base_url}, "
            f"has_token={bool(token)}, has_family_id={bool(family_id)}"
        )
    
    def update_config(self, token: Optional[str] = None, family_id: Optional[str] = None, env: Optional[str] = None):
        """更新IOT配置"""
        if token is not None:
            self.token = token
        if family_id is not None:
            self.family_id = family_id
        if env is not None:
            self.env = env
            self.base_url = settings.iot_base_url
        
        logger.info(
            f"IOTService config updated: env={self.env}, base_url={self.base_url}, "
            f"has_token={bool(self.token)}, has_family_id={bool(self.family_id)}"
        )
    
    async def get_family_devices(self, family_id: Optional[str] = None, iot_token: Optional[str] = None) -> Dict[str, Any]:
        """查询指定家庭圈的设备清单"""
        _family_id = family_id or self.family_id
        _iot_token = iot_token or self.token
        
        if not _family_id or not _iot_token:
            logger.warning("Missing credentials or mock mode, using mock data")
            return await self._get_mock_family_devices()
        
        try:
            async with httpx.AsyncClient(timeout=settings.iot_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/dms/api/family/device/queryByFamily",
                    headers={"Authorization": f"Bearer {_iot_token}"},
                    params={"familyId": _family_id}
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Family devices retrieved: {_family_id}, count: {len(result.get('data', []))}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get family devices: {e}")
            return await self._get_mock_family_devices()
    
    async def get_device_status(self, device_guid: str, iot_token: Optional[str] = None) -> Dict[str, Any]:
        """查询指定设备GUID的状态详情"""
        _iot_token = iot_token or self.token
        
        if not _iot_token or settings.dev_mock_external_services:
            return await self._get_mock_device_status(device_guid)
        
        try:
            async with httpx.AsyncClient(timeout=settings.iot_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={"Authorization": f"Bearer {_iot_token}"},
                    params={"deviceIds": device_guid}
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 更新缓存
                self.device_cache[device_guid] = result
                self.last_update_time[device_guid] = asyncio.get_event_loop().time()
                
                logger.info(f"Device status retrieved: {device_guid}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            return await self._get_mock_device_status(device_guid)
    
    async def _get_mock_family_devices(self) -> Dict[str, Any]:
        """返回模拟的家庭设备清单"""
        await asyncio.sleep(0.3)
        
        return {
            "rc": 0,
            "msg": "操作成功",
            "success": True,
            "data": [
                {
                    "familyId": "test_family_001",
                    "familyName": "测试家庭",
                    "deviceId": 10182044,
                    "deviceGuid": "CQ928c0f535efd97f",
                    "name": "CQ928蒸烤一体机",
                    "dc": "RZKY",
                    "categoryName": "一体机",
                    "dt": "CQ928",
                    "netState": 1,
                    "status": 1,
                    "platformCode": "ZKY02",
                },
                {
                    "familyId": "test_family_001",
                    "familyName": "测试家庭",
                    "deviceId": 10182046,
                    "deviceGuid": "YYJ001c0f535efd99f",
                    "name": "智能油烟机",
                    "dc": "RZKY",
                    "categoryName": "油烟机",
                    "dt": "YYJ001",
                    "netState": 1,
                    "status": 1,
                    "platformCode": "YYJ01",
                }
            ]
        }
    
    async def _get_mock_device_status(self, device_guid: str) -> Dict[str, Any]:
        """返回模拟的设备状态"""
        await asyncio.sleep(0.3)
        
        return {
            "rc": 0,
            "msg": "操作成功",
            "success": True,
            "data": [
                {
                    "deviceId": device_guid,
                    "status": 1,
                    "properties": {
                        "powerState": random.choice([0, 1]),
                        "workState": random.choice([0, 1, 2]),
                        "faultCode": 0,
                        "timestamp": int(asyncio.get_event_loop().time())
                    }
                }
            ]
        }
