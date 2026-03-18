"""
IoT 服务
从 backend/agentic_test/services.py 迁移
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
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
            raise RuntimeError(
                f"[MOCK 已删除] 无法获取家庭设备：缺少 family_id 或 iot_token。"
                f"family_id={'已设置' if _family_id else '未设置'}, iot_token={'已设置' if _iot_token else '未设置'}"
            )
        
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
            async with httpx.AsyncClient(timeout=settings.iot_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/iot/api/device/property/shadow",
                    headers={"Authorization": f"Bearer {_iot_token}"},
                    params={"deviceIds": device_ids_str}
                )

                response.raise_for_status()
                result = response.json()

                # 更新缓存
                for device_guid in device_guids:
                    self.device_cache[device_guid] = result
                    self.last_update_time[device_guid] = asyncio.get_event_loop().time()

                logger.info(f"Device status retrieved: {device_ids_str}")
                return result

        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            raise RuntimeError(
                f"[MOCK 已删除] 获取设备状态失败: {e}。"
                f"device_guids={device_guids}"
            )
    
    