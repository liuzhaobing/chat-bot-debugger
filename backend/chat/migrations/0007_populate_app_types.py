# Data migration to populate initial AppType records

from django.db import migrations


def create_initial_app_types(apps, schema_editor):
    """
    创建初始的应用类型数据
    """
    AppType = apps.get_model('chat', 'AppType')
    
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
    
    for app_type_data in app_types:
        AppType.objects.create(**app_type_data)


def assign_default_app_type(apps, schema_editor):
    """
    为现有的应用分配默认类型（Agent 1.0）
    """
    App = apps.get_model('chat', 'App')
    AppType = apps.get_model('chat', 'AppType')
    
    # 获取 Agent 1.0 类型
    try:
        agent_1_0 = AppType.objects.get(code='agent_1_0')
        # 为所有没有类型的应用分配 Agent 1.0
        App.objects.filter(app_type__isnull=True).update(app_type=agent_1_0)
    except AppType.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_apptype_and_app_extensions'),
    ]

    operations = [
        migrations.RunPython(create_initial_app_types),
        migrations.RunPython(assign_default_app_type),
    ]
