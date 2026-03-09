"""
TraceID 生成工具
用于分布式追踪
"""
import uuid


def generate_trace_id() -> str:
    """
    生成唯一的 TraceID
    
    Returns:
        UUID 格式的 TraceID
    """
    return str(uuid.uuid4())
