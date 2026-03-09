# -*- coding:utf-8 -*-
# Filename: formatter
# Description:
# Author: zhaobing.liu@outlook.com
# Created: 2025/7/28
# Last Modified: 2025/7/28
import json
import traceback
from datetime import datetime

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def jsonify_log_record(self, log_record):
        """
        将日志记录转换为 JSON 字符串

        重写此方法以禁用 ensure_ascii，支持中文等非ASCII字符正常显示
        """
        return json.dumps(log_record, ensure_ascii=False, default=str)

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add trace info
        log_record['traceId'] = getattr(record, 'traceId', '')
        log_record['sessionId'] = getattr(record, 'sessionId', '')
        log_record['job_instance_id'] = getattr(record, 'job_instance_id', '')

        # Add environment info
        log_record['env'] = 'prod'  # Configure based on environment
        log_record['index'] = 'roki_ai_test_platform_worker_prod'

        # Add time in desired format
        log_record['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Add execution context
        log_record['thread'] = record.threadName
        log_record['class'] = f"{record.name}.{record.funcName}:{record.lineno}"
        log_record['level'] = record.levelname

        # Add optional fields
        log_record['code'] = getattr(record, 'code', '')
        log_record['carrier'] = getattr(record, 'carrier', '')
        log_record['deviceId'] = getattr(record, 'deviceId', '')
        log_record['platform'] = getattr(record, 'platform', '')
        log_record['uid'] = record.user_id if hasattr(record, 'user_id') else ''
        log_record['stack_trace'] = ''
        if record.exc_info:
            log_record['stack_trace'] = ''.join(traceback.format_exception(*record.exc_info))
