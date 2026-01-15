# Generated migration file for dial app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CallSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=255, unique=True)),
                ('room_id', models.CharField(max_length=255)),
                ('user_id', models.CharField(max_length=255)),
                ('participant_id', models.CharField(max_length=255)),
                ('agent_type', models.CharField(max_length=100)),
                ('config_template', models.CharField(max_length=100)),
                ('status', models.CharField(default='pending', max_length=50)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'dial_call_session',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='CallTranscript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speaker', models.CharField(max_length=50)),
                ('text', models.TextField()),
                ('is_final', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transcripts', to='dial.callsession')),
            ],
            options={
                'db_table': 'dial_call_transcript',
                'ordering': ['timestamp'],
            },
        ),
    ]
