"""
DeviceStatus Model
镜像 backend/agentic_test/models.py 中的 DeviceStatus
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class DeviceStatus(Base):
    """设备状态模型"""
    
    __tablename__ = "device_status"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 字段
    device_id = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(200), nullable=False)
    device_type = Column(String(50), nullable=False)  # 油烟机、空调等
    status = Column(JSON, nullable=False, default=dict)  # 设备状态数据
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DeviceStatus(device_id={self.device_id}, name={self.device_name})>"
