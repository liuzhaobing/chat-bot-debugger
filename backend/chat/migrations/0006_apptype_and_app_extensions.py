# Generated migration file for AppType and App extensions

from django.db import migrations, models
import django.db.models.deletion
import chat.models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20260113_0812'),
    ]

    operations = [
        # 创建 AppType 表
        migrations.CreateModel(
            name='AppType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="显示名称，如 'Agent 1.0'", max_length=50)),
                ('code', models.CharField(help_text="代码标识，如 'agent_1_0'", max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='类型描述')),
                ('is_active', models.BooleanField(default=True, help_text='是否启用')),
                ('sort_order', models.IntegerField(default=0, help_text='排序权重，数字越小越靠前')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '应用类型',
                'verbose_name_plural': '应用类型',
                'ordering': ['sort_order', 'id'],
            },
        ),
        
        # 添加 App 的新字段
        migrations.AddField(
            model_name='app',
            name='model_name',
            field=models.CharField(blank=True, help_text="使用的模型名称，如 'gpt-4'", max_length=100),
        ),
        migrations.AddField(
            model_name='app',
            name='function_schema',
            field=models.JSONField(
                blank=True, 
                default=dict, 
                help_text='Function Calling Schema，用于将应用作为工具调用',
                validators=[chat.models.validate_function_schema]
            ),
        ),
        migrations.AddField(
            model_name='app',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # 添加 app_type 外键（允许为空，稍后填充默认值）
        migrations.AddField(
            model_name='app',
            name='app_type',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='apps',
                to='chat.apptype',
                help_text='应用类型：Agent 1.0, Agent 2.0, Workflow 等'
            ),
        ),
    ]
