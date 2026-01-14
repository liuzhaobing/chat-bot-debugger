#!/usr/bin/env python
"""
初始化应用类型数据
运行此脚本以创建默认的应用类型
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import AppType

def init_app_types():
    """初始化应用类型数据"""
    app_types = [
        {
            'name': 'Agent 1.0',
            'code': 'agent_1_0',
            'description': '结合 Prompt 与模型参数控制的 Agent 模式，适合快速构建和调试对话应用。',
            'is_active': True,
            'sort_order': 1
        },
        {
            'name': 'Agent 2.0',
            'code': 'agent_2_0',
            'description': '基于复杂框架构建，强化 React 与 Function Call 能力，适用于重逻辑场景。',
            'is_active': False,  # 暂未实现
            'sort_order': 2
        },
        {
            'name': 'Workflow',
            'code': 'workflow',
            'description': '自定义编排工作流，支持复杂的多步骤任务处理。',
            'is_active': False,  # 暂未实现
            'sort_order': 3
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for app_type_data in app_types:
        app_type, created = AppType.objects.update_or_create(
            code=app_type_data['code'],
            defaults={
                'name': app_type_data['name'],
                'description': app_type_data['description'],
                'is_active': app_type_data['is_active'],
                'sort_order': app_type_data['sort_order']
            }
        )
        if created:
            created_count += 1
            print(f"✓ 创建应用类型: {app_type.name}")
        else:
            updated_count += 1
            print(f"✓ 更新应用类型: {app_type.name}")
    
    print(f"\n完成! 创建 {created_count} 个，更新 {updated_count} 个应用类型")

if __name__ == '__main__':
    print("正在初始化应用类型...")
    init_app_types()
