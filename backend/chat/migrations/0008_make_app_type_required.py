# Make app_type field required after data migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_populate_app_types'),
    ]

    operations = [
        # 现在所有应用都有类型了，可以将字段设为必填
        migrations.AlterField(
            model_name='app',
            name='app_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='apps',
                to='chat.apptype',
                help_text='应用类型：Agent 1.0, Agent 2.0, Workflow 等'
            ),
        ),
    ]
