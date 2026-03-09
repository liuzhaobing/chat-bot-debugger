"""
结构化日志配置
支持 JSON 格式日志，包含 TraceID
"""
import json
import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.config import settings


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
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    root_logger.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}"
    )


__all__ = ["setup_logging", "CustomJsonFormatter"]
