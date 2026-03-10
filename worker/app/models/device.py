"""
DeviceStatus Model
镜像 backend/agentic_test/models.py 中的 DeviceStatus
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, TypeDecorator, CHAR

from app.core.database import Base


class GUID(TypeDecorator):
    """
    数据库无关的 UUID 类型，兼容 SQLite 和 PostgreSQL。
    在 SQLite 中存储为 CHAR(32)（无连字符的十六进制字符串），
    在 Python 中转换为 uuid.UUID 对象或字符串。
    """
    impl = CHAR(32)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return value.hex
        elif isinstance(value, str):
            # 移除连字符，返回 32 字符的十六进制字符串
            return value.replace('-', '')
        else:
            return str(value).replace('-', '')

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, str):
            return value
        else:
            return str(value)


class DeviceStatus(Base):
    """设备状态模型"""

    __tablename__ = "device_status"

    # 主键 - 使用 GUID 类型兼容 SQLite
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # 字段
    device_id = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(200), nullable=False)
    device_type = Column(String(50), nullable=False)  # 油烟机、空调等
    status = Column(JSON, nullable=False, default=dict)  # 设备状态数据
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DeviceStatus(device_id={self.device_id}, name={self.device_name})>"
