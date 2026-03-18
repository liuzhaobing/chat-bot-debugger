"""
Agentic Test 服务模块（简化版）
仅包含 HTTP API 所需的 IOTService

注意：完整的业务逻辑已迁移到 worker 服务
"""
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
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
            raise RuntimeError(
                f"[MOCK 已删除] 无法获取家庭设备：缺少 family_id 或 iot_token。"
                f"family_id={'已设置' if _family_id else '未设置'}, iot_token={'已设置' if _iot_token else '未设置'}"
            )

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
            raise RuntimeError(
                f"[MOCK 已删除] 获取家庭设备失败: {e}。"
                f"family_id={_family_id}"
            )

    async def get_device_status(self, device_guids: List[str], iot_token: Optional[str] = None) -> Dict[str, Any]:
        """查询指定设备GUID列表的状态详情

        Args:
            device_guids: 设备GUID列表
            iot_token: IOT token

        Returns:
            设备状态结果，data中包含多个设备的状态列表
        """
        _iot_token = iot_token or self.token
        device_ids_str = ",".join(device_guids)

        if not _iot_token:
            raise RuntimeError(
                f"[MOCK 已删除] 无法获取设备状态：iot_token 为空。"
                f"device_guids={device_guids}"
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={"Authorization": f"Bearer {_iot_token}"},
                    params={"deviceIds": device_ids_str}
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Device status retrieved: {device_ids_str}")
                return result

        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            raise RuntimeError(
                f"[MOCK 已删除] 获取设备状态失败: {e}。"
                f"device_guids={device_guids}"
            )


__all__ = ['IOTService']