"""
AgenticTestLog Model
镜像 backend/agentic_test/models.py 中的 AgenticTestLog
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, TypeDecorator, CHAR
from sqlalchemy.orm import relationship

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

    # 主键 - 使用 GUID 类型兼容 SQLite
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # 外键 - 使用 GUID 类型兼容 SQLite
    session_id = Column(GUID(), ForeignKey("agentic_test_session.id"), nullable=False)
    
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
