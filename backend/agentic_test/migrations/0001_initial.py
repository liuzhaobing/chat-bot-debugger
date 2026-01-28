from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AgenticTestSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(default='新测试会话', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'agentic_test_session',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='DeviceStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('device_id', models.CharField(max_length=100, unique=True)),
                ('device_name', models.CharField(max_length=200)),
                ('device_type', models.CharField(max_length=50)),
                ('status', models.JSONField(default=dict)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'device_status',
            },
        ),
        migrations.CreateModel(
            name='AgenticTestLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('log_type', models.CharField(choices=[('user_query', '用户查询'), ('tts_generated', 'TTS生成'), ('speaker_play', '扬声器播放'), ('mic_capture', '麦克风采集'), ('vad_result', 'VAD结果'), ('asr_result', 'ASR识别'), ('iot_query', 'IOT查询'), ('app_call', 'App调用'), ('system_error', '系统错误')], max_length=20)),
                ('content', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='agentic_test.agentictestsession')),
            ],
            options={
                'db_table': 'agentic_test_log',
                'ordering': ['-timestamp'],
            },
        ),
    ]