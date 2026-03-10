"""
Agentic Test 服务模块（简化版）
仅包含 HTTP API 所需的 IOTService

注意：完整的业务逻辑已迁移到 worker 服务
"""
import asyncio
import logging
import random
import os
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class IOTService:
    """物联网设备服务 - 用于 HTTP API"""

    # IoT 环境配置
    IOT_BASE_URL_TEST = os.environ.get("IOT_BASE_URL_TEST", "http://api-test.myroki.com/rest")
    IOT_BASE_URL_PROD = os.environ.get("IOT_BASE_URL_PROD", "http://api.myroki.com/rest")

    def __init__(self, token: str = "", family_id: str = "", env: str = "test"):
        """初始化IOT服务"""
        self.token = token
        self.family_id = family_id
        self.env = env

        # 根据环境选择基础 URL
        self.base_url = self.IOT_BASE_URL_PROD if env == "prod" else self.IOT_BASE_URL_TEST

        logger.info(f"IOTService initialized: env={env}, base_url={self.base_url}")

    def update_config(self, token: Optional[str] = None, family_id: Optional[str] = None, env: Optional[str] = None):
        """更新IOT配置"""
        if token is not None:
            self.token = token
        if family_id is not None:
            self.family_id = family_id
        if env is not None:
            self.env = env
            self.base_url = self.IOT_BASE_URL_PROD if env == "prod" else self.IOT_BASE_URL_TEST

    async def get_family_devices(self, family_id: Optional[str] = None, iot_token: Optional[str] = None) -> Dict[str, Any]:
        """查询指定家庭圈的设备清单"""
        _family_id = family_id or self.family_id
        _iot_token = iot_token or self.token

        if not _family_id or not _iot_token:
            logger.warning("Missing credentials, using mock data")
            return await self._get_mock_family_devices()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
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

        if not _iot_token:
            return await self._get_mock_device_status(device_guid)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={"Authorization": f"Bearer {_iot_token}"},
                    params={"deviceIds": device_guid}
                )

                response.raise_for_status()
                result = response.json()

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


__all__ = ['IOTService']