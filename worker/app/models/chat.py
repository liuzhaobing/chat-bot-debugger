"""
Chat Models
镜像 backend/chat/models.py 中的 App 相关模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AppType(Base):
    """应用类型模型"""
    
    __tablename__ = "chat_apptype"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 字段
    name = Column(String(50), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    apps = relationship("App", back_populates="app_type")
    
    def __repr__(self):
        return f"<AppType(code={self.code}, name={self.name})>"


class App(Base):
    """应用模型"""
    
    __tablename__ = "chat_app"
    
    # 主键
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon_url = Column(String(200), nullable=True)
    
    # 分类和类型
    category_id = Column(Integer, ForeignKey("chat_appcategory.id"), nullable=True)
    app_type_id = Column(Integer, ForeignKey("chat_apptype.id"), nullable=False)
    
    # Agent 1.0 配置
    execution_mode = Column(String(10), nullable=False, default="chat")
    system_prompt = Column(Text, nullable=False, default="")
    parameters = Column(JSON, nullable=False, default=dict)
    
    # 模型配置
    provider_id = Column(String(32), nullable=True)
    model_name = Column(String(100), nullable=False, default="")
    configuration = Column(JSON, nullable=False, default=dict)
    
    # 元数据
    is_featured = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    app_type = relationship("AppType", back_populates="apps")
    
    def __repr__(self):
        return f"<App(id={self.id}, name={self.name})>"


class Conversation(Base):
    """对话会话模型"""
    
    __tablename__ = "chat_conversation"
    
    # 主键
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    
    # 字段
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """消息模型"""
    
    __tablename__ = "chat_message"
    
    # 主键
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    
    # 外键
    conversation_id = Column(String(32), ForeignKey("chat_conversation.id"), nullable=False)
    
    # 字段
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    reasoning_content = Column(Text, nullable=True)
    token_usage = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"
