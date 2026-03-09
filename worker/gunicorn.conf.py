"""
Gunicorn 配置文件
生产环境进程管理配置
"""
import multiprocessing
import os

# 从环境变量读取配置
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
bind = f"{os.getenv('WORKER_HOST', '0.0.0.0')}:{os.getenv('WORKER_PORT', '8001')}"
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# 日志配置
accesslog = "-"  # 输出到 stdout
errorlog = "-"   # 输出到 stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "agentic-worker"

# 预加载应用（提高性能）
preload_app = True

# Worker 配置
worker_connections = 1000
max_requests = 10000  # 防止内存泄漏
max_requests_jitter = 1000

# 优雅重启
graceful_timeout = 30

# 回调函数
def on_starting(server):
    """服务器启动时"""
    print(f"Starting Gunicorn with {workers} workers")

def on_reload(server):
    """重载时"""
    print("Reloading Gunicorn")

def worker_int(worker):
    """Worker 被中断时"""
    print(f"Worker {worker.pid} interrupted")

def worker_abort(worker):
    """Worker 异常退出时"""
    print(f"Worker {worker.pid} aborted")

def post_fork(server, worker):
    """Worker fork 后"""
    print(f"Worker {worker.pid} spawned")

def pre_fork(server, worker):
    """Worker fork 前"""
    pass

def pre_exec(server):
    """重新执行前"""
    print("Forked child, re-executing")

def when_ready(server):
    """服务器准备好时"""
    print(f"Server is ready. Listening on: {bind}")

def worker_exit(server, worker):
    """Worker 退出时"""
    print(f"Worker {worker.pid} exited")
