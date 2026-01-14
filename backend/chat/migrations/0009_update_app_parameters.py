# Migration to update App model: rename variables to parameters, add provider_id

from django.db import migrations, models
import chat.models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_make_app_type_required'),
    ]

    operations = [
        # 重命名 variables 为 parameters
        migrations.RenameField(
            model_name='app',
            old_name='variables',
            new_name='parameters',
        ),
        
        # 删除 function_schema 字段（不再需要）
        migrations.RemoveField(
            model_name='app',
            name='function_schema',
        ),
        
        # 添加 provider_id 字段
        migrations.AddField(
            model_name='app',
            name='provider_id',
            field=models.IntegerField(blank=True, help_text='使用的供应商ID', null=True),
        ),
        
        # 更新 name 字段添加验证器
        migrations.AlterField(
            model_name='app',
            name='name',
            field=models.CharField(
                help_text='应用名称，必须为驼峰命名，如 GetWeather', 
                max_length=100,
                validators=[chat.models.validate_camel_case_name]
            ),
        ),
    ]
