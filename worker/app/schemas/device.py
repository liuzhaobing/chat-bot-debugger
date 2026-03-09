"""
设备相关 Schemas
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IoTConfig(BaseModel):
    """IoT 配置"""
    token: str = Field(..., description="IoT 认证 Token")
    familyId: str = Field(..., alias="familyId", description="家庭 ID")
    env: str = Field(default="test", description="环境（test/prod）")
    
    class Config:
        populate_by_name = True


class DeviceInfo(BaseModel):
    """设备信息"""
    familyId: str = Field(..., description="家庭 ID")
    familyName: str = Field(..., description="家庭名称")
    deviceId: int = Field(..., description="设备 ID")
    deviceGuid: str = Field(..., description="设备 GUID")
    name: str = Field(..., description="设备名称")
    dc: str = Field(..., description="设备类别")
    categoryName: str = Field(..., description="类别名称")
    dt: str = Field(..., description="设备类型")
    displayType: str = Field(..., description="显示类型")
    deviceTypeName: str = Field(..., description="设备类型名称")
    netState: int = Field(..., description="网络状态")
    status: int = Field(..., description="设备状态")
    platformCode: str = Field(..., description="平台代码")


class DeviceProperty(BaseModel):
    """设备属性"""
    name: str = Field(..., description="属性名称")
    value: Any = Field(..., description="属性值")
    dataType: str = Field(..., description="数据类型")


class DeviceStatus(BaseModel):
    """设备状态"""
    device_guid: str = Field(..., description="设备 GUID")
    properties: List[DeviceProperty] = Field(default_factory=list, description="设备属性列表")
    timestamp: Optional[float] = Field(None, description="时间戳")
