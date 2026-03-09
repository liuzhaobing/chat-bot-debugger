"""
AgenticTestLog Model
镜像 backend/agentic_test/models.py 中的 AgenticTestLog
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgenticTestLog(Base):
    """Agentic Test 日志模型"""
    
    __tablename__ = "agentic_test_log"
    
    # 日志类型常量
    LOG_TYPE_USER_QUERY = "user_query"
    LOG_TYPE_TTS_GENERATED = "tts_generated"
    LOG_TYPE_SPEAKER_PLAY = "speaker_play"
    LOG_TYPE_MIC_CAPTURE = "mic_capture"
    LOG_TYPE_VAD_RESULT = "vad_result"
    LOG_TYPE_ASR_RESULT = "asr_result"
    LOG_TYPE_IOT_QUERY = "iot_query"
    LOG_TYPE_APP_CALL = "app_call"
    LOG_TYPE_SYSTEM_ERROR = "system_error"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    session_id = Column(UUID(as_uuid=True), ForeignKey("agentic_test_session.id"), nullable=False)
    
    # 字段
    log_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    # 注意：使用 meta_data 作为 Python 属性名，映射到数据库列 metadata
    # 因为 metadata 是 SQLAlchemy 的保留属性名
    meta_data = Column("metadata", JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    session = relationship("AgenticTestSession", back_populates="logs")
    
    def __repr__(self):
        return f"<AgenticTestLog(id={self.id}, type={self.log_type})>"
