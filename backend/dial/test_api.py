"""
测试 Dial API 的简单脚本
运行: python manage.py shell < dial/test_api.py
"""

from dial.models import CallSession, CallTranscript
from django.utils import timezone

# 清理测试数据
print("清理旧的测试数据...")
CallSession.objects.filter(session_id__startswith='test_').delete()

# 创建测试会话
print("\n创建测试会话...")
session = CallSession.objects.create(
    session_id='test_session_001',
    room_id='test_room_001',
    user_id='test_user',
    participant_id='test_participant',
    agent_type='robam_workflow',
    config_template='ai_telephone',
    status='active'
)
print(f"✓ 会话创建成功: {session.session_id}")

# 添加字幕记录
print("\n添加字幕记录...")
transcript1 = CallTranscript.objects.create(
    session=session,
    speaker='speaker00',
    text='你好，我想咨询一下产品信息',
    is_final=True
)
print(f"✓ 用户消息: {transcript1.text}")

transcript2 = CallTranscript.objects.create(
    session=session,
    speaker='speaker01',
    text='您好，我是AI客服，很高兴为您服务',
    is_final=True
)
print(f"✓ AI回复: {transcript2.text}")

# 查询会话
print("\n查询会话信息...")
sessions = CallSession.objects.all()
print(f"✓ 总会话数: {sessions.count()}")

for s in sessions:
    print(f"\n会话ID: {s.session_id}")
    print(f"状态: {s.status}")
    print(f"开始时间: {s.started_at}")
    print(f"字幕数量: {s.transcripts.count()}")
    
    print("\n字幕内容:")
    for t in s.transcripts.all():
        speaker_name = '用户' if t.speaker == 'speaker00' else 'AI客服'
        print(f"  [{speaker_name}] {t.text}")

print("\n✓ 测试完成!")
