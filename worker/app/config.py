"""
配置管理模块
使用 Pydantic Settings 管理环境变量
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==================== 应用配置 ====================
    app_name: str = Field(default="AgenticWorker", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    
    # ==================== 服务端口 ====================
    worker_host: str = Field(default="0.0.0.0", description="服务监听地址")
    worker_port: int = Field(default=8001, description="服务监听端口")
    
    # ==================== 数据库配置 ====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./agentic.db",
        description="数据库连接URL"
    )
    database_pool_size: int = Field(default=20, description="连接池大小")
    database_max_overflow: int = Field(default=10, description="连接池最大溢出")
    database_pool_timeout: int = Field(default=30, description="连接池超时")
    database_pool_recycle: int = Field(default=3600, description="连接回收时间")
    
    # ==================== Redis 配置 ====================
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    redis_max_connections: int = Field(default=50, description="Redis最大连接数")
    redis_socket_timeout: int = Field(default=5, description="Redis socket超时")
    redis_socket_connect_timeout: int = Field(default=5, description="Redis连接超时")
    session_expire_seconds: int = Field(default=86400, description="Session过期时间")
    
    # ==================== JWT 配置 ====================
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expire_minutes: int = Field(default=1440, description="JWT过期时间（分钟）")
    
    # ==================== WebSocket 配置 ====================
    ws_heartbeat_interval: int = Field(default=30, description="心跳间隔（秒）")
    ws_heartbeat_timeout: int = Field(default=90, description="心跳超时（秒）")
    ws_max_connections: int = Field(default=1000, description="最大连接数")
    ws_message_queue_size: int = Field(default=100, description="消息队列大小")
    
    # ==================== CORS 配置 ====================
    cors_origins: List[str] = Field(
        default=["http://localhost:8080", "http://localhost:3000"],
        description="允许的CORS源"
    )
    cors_allow_credentials: bool = Field(default=True, description="允许携带凭证")
    cors_allow_methods: List[str] = Field(default=["*"], description="允许的HTTP方法")
    cors_allow_headers: List[str] = Field(default=["*"], description="允许的HTTP头")
    
    # ==================== 外部服务配置 ====================
    # TTS
    tts_base_url: Optional[str] = Field(default=None, description="TTS服务URL")
    tts_app_id: Optional[str] = Field(default=None, description="TTS应用ID")
    tts_access_key: Optional[str] = Field(default=None, description="TTS访问密钥")
    tts_resource_id: Optional[str] = Field(default=None, description="TTS资源ID")
    tts_speaker: str = Field(default="default_speaker", description="TTS说话人")
    tts_timeout: int = Field(default=30, description="TTS超时时间")
    
    # ASR
    asr_app_id: str = Field(
        default="4f95e97b0ec641fab9772b68a81bcf4a",
        description="ASR应用ID"
    )
    asr_timeout: int = Field(default=30, description="ASR超时时间")
    
    # IoT
    iot_base_url_test: str = Field(
        default="http://api-test.myroki.com/rest",
        description="IoT测试环境URL"
    )
    iot_base_url_prod: str = Field(
        default="http://api.myroki.com/rest",
        description="IoT生产环境URL"
    )
    iot_timeout: int = Field(default=30, description="IoT超时时间")
    iot_cache_ttl: int = Field(default=60, description="IoT缓存TTL")
    
    # ==================== 任务队列配置 ====================
    task_queue_max_size: int = Field(default=1000, description="任务队列最大大小")
    task_worker_count: int = Field(default=4, description="任务工作线程数")
    task_timeout: int = Field(default=300, description="任务超时时间")
    
    # ==================== 监控配置 ====================
    enable_metrics: bool = Field(default=True, description="启用监控指标")
    metrics_port: int = Field(default=9090, description="监控指标端口")
    
    # ==================== 日志配置 ====================
    log_format: str = Field(default="json", description="日志格式")
    log_file_path: str = Field(default="./logs/worker.log", description="日志文件路径")
    log_file_max_bytes: int = Field(default=10485760, description="日志文件最大字节")
    log_file_backup_count: int = Field(default=5, description="日志文件备份数量")
    
    # ==================== 性能配置 ====================
    gunicorn_workers: int = Field(default=4, description="Gunicorn工作进程数")
    gunicorn_worker_class: str = Field(
        default="uvicorn.workers.UvicornWorker",
        description="Gunicorn工作类"
    )
    gunicorn_timeout: int = Field(default=120, description="Gunicorn超时")
    gunicorn_graceful_timeout: int = Field(default=30, description="Gunicorn优雅超时")
    gunicorn_keepalive: int = Field(default=5, description="Gunicorn保持连接")
    
    # ==================== 安全配置 ====================
    allowed_ws_origins: List[str] = Field(
        default=["http://localhost:8080", "http://localhost:3000"],
        description="允许的WebSocket源"
    )
    rate_limit_enabled: bool = Field(default=True, description="启用速率限制")
    rate_limit_per_minute: int = Field(default=60, description="每分钟速率限制")
    
    # ==================== 开发配置 ====================
    dev_mock_external_services: bool = Field(
        default=False,
        description="开发模式下模拟外部服务"
    )
    dev_skip_auth: bool = Field(default=False, description="开发模式下跳过认证")
    
    @field_validator("cors_origins", "allowed_ws_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS源配置"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"
    
    @property
    def iot_base_url(self) -> str:
        """根据环境返回IoT基础URL"""
        return self.iot_base_url_prod if self.is_production else self.iot_base_url_test


# 全局配置实例
settings = Settings()


# 导出配置
__all__ = ["settings", "Settings"]
