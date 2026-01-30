#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'formatter.CustomJsonFormatter',
            'json_ensure_ascii': False,
            'format': '[%(asctime)s] [%(name)s::%(funcName)s::%(lineno)d] [%(levelname)s] [%(user_id)s] %(message)s',
            'rename_fields': {
                'asctime': 'time',
                'levelname': 'level',
            }
        },
        'standard': {
            'format': '[%(asctime)s] [%(name)s::%(funcName)s::%(lineno)d] [%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'json'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'gunicorn.access': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn.access': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
})


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
