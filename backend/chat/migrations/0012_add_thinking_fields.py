# Generated migration for deep thinking feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_auto_20260114_0246'),  # 替换为实际的上一个迁移文件名
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reasoning_content',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='深度思考内容 (reasoning_content)，从 delta.reasoning_content 获取'
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='token_usage',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='Token 使用统计 {prompt_tokens, completion_tokens, total_tokens}'
            ),
        ),
    ]
