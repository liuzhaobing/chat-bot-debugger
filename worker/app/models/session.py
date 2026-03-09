"""
AgenticTestSession Model
镜像 backend/agentic_test/models.py 中的 AgenticTestSession
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgenticTestSession(Base):
    """Agentic Test 会话模型"""
    
    __tablename__ = "agentic_test_session"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 字段
    name = Column(String(200), nullable=False, default="新测试会话")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=False)
    
    # 关系
    logs = relationship("AgenticTestLog", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgenticTestSession(id={self.id}, name={self.name})>"
