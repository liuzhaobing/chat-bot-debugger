#!/usr/bin/env python
"""
测试UUID主键功能
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import Provider, LLMModel

def test_uuid_generation():
    """测试UUID自动生成"""
    print("=" * 60)
    print("测试 UUID 主键功能")
    print("=" * 60)
    
    # 测试Provider
    print("\n1. 测试 Provider UUID 生成:")
    providers = Provider.objects.all()[:3]
    for p in providers:
        print(f"   Provider: {p.name}")
        print(f"   ID: {p.id} (长度: {len(p.id)})")
        print(f"   类型: {type(p.id)}")
        print()
    
    # 测试LLMModel
    print("2. 测试 LLMModel UUID 生成:")
    models = LLMModel.objects.all()[:3]
    for m in models:
        print(f"   Model: {m.name}")
        print(f"   ID: {m.id} (长度: {len(m.id)})")
        print(f"   Provider ID: {m.provider_id}")
        print()
    
    # 测试查询
    print("3. 测试组合查询:")
    if providers and models:
        provider = providers[0]
        model = models[0]
        print(f"   查询条件: provider_id={model.provider_id}, name={model.name}")
        try:
            result = LLMModel.objects.get(provider_id=model.provider_id, name=model.name)
            print(f"   ✅ 查询成功: {result.name} (ID: {result.id})")
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    test_uuid_generation()
