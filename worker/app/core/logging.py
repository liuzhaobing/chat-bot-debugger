"""
结构化日志配置
支持 JSON 格式日志，包含 TraceID
"""
import json
import logging
import sys
from typing import Any, Dict, Optional
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

from app.config import settings


# 上下文变量，用于在整个请求生命周期中存储 job_instance_id
_job_instance_id_ctx: ContextVar[Optional[str]] = ContextVar('job_instance_id', default=None)


def set_job_instance_id(job_instance_id: Optional[str]) -> None:
    """设置当前上下文的 job_instance_id

    在请求开始时调用，后续所有日志都会自动包含此字段。

    Args:
        job_instance_id: 任务实例ID
    """
    _job_instance_id_ctx.set(job_instance_id)


def get_job_instance_id() -> Optional[str]:
    """获取当前上下文的 job_instance_id"""
    return _job_instance_id_ctx.get()


class JobInstanceIdFilter(logging.Filter):
    """日志过滤器，自动添加 job_instance_id 到日志记录"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.job_instance_id = get_job_instance_id() or ''
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义 JSON 日志格式化器"""

    def jsonify_log_record(self, log_record: Dict[str, Any]) -> str:
        """
        将日志记录转换为 JSON 字符串

        重写此方法以禁用 ensure_ascii，支持中文等非ASCII字符正常显示
        """
        return json.dumps(log_record, ensure_ascii=False, default=str)

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """添加自定义字段"""
        super().add_fields(log_record, record, message_dict)

        # 添加应用信息
        log_record['app'] = settings.app_name
        log_record['environment'] = settings.environment

        # 添加日志级别
        log_record['level'] = record.levelname

        # 添加模块信息
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # 添加 TraceID（如果存在）
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id

        # 添加 job_instance_id（用于日志追踪和报告关联）
        if hasattr(record, 'job_instance_id'):
            log_record['job_instance_id'] = record.job_instance_id


def setup_logging() -> None:
    """
    配置应用日志

    根据配置选择 JSON 或文本格式
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 添加 job_instance_id 过滤器（自动添加到所有日志记录）
    job_instance_filter = JobInstanceIdFilter()
    root_logger.addFilter(job_instance_filter)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 选择格式化器
    if settings.log_format == "json":
        # JSON 格式（生产环境推荐）
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
    else:
        # 文本格式（开发环境）
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if settings.log_file_path:
        try:
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                settings.log_file_path,
                maxBytes=settings.log_file_max_bytes,
                backupCount=settings.log_file_backup_count
            )
            file_handler.setLevel(getattr(logging, settings.log_level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")
    
    # 设置第三方库日志级别
    # 注意：uvicorn 的 WebSocket 协议使用 "uvicorn.error" logger 输出帧调试日志
    # 如果应用日志级别是 DEBUG，需要单独控制 uvicorn.error 以避免 websockets 协议日志刷屏
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)  # WebSocket 协议帧日志
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)  # websockets 所有模块日志
    
    root_logger.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}"
    )


__all__ = ["setup_logging", "CustomJsonFormatter", "JobInstanceIdFilter", "set_job_instance_id", "get_job_instance_id"]
