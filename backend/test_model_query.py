#!/usr/bin/env python
"""
测试模型查询修复
验证多供应商同名模型的查询
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import Provider, LLMModel

def test_duplicate_model_names():
    """测试同名模型的查询"""
    print("=" * 60)
    print("测试多供应商同名模型查询")
    print("=" * 60)
    
    # 查找所有模型名称
    all_models = LLMModel.objects.all()
    model_names = {}
    
    for model in all_models:
        name = model.name
        if name not in model_names:
            model_names[name] = []
        model_names[name].append({
            'id': model.id,
            'provider_id': model.provider_id,
            'provider_name': model.provider.name
        })
    
    # 找出重复的模型名称
    duplicates = {name: models for name, models in model_names.items() if len(models) > 1}
    
    if duplicates:
        print(f"\n发现 {len(duplicates)} 个重复的模型名称:\n")
        for name, models in duplicates.items():
            print(f"模型名称: {name}")
            print(f"出现次数: {len(models)}")
            for m in models:
                print(f"  - Provider: {m['provider_name']} (ID: {m['provider_id']})")
                print(f"    Model ID: {m['id']}")
            print()
        
        # 测试查询
        print("测试组合查询（provider_id + model_name）:")
        test_name = list(duplicates.keys())[0]
        test_models = duplicates[test_name]
        
        for m in test_models:
            try:
                result = LLMModel.objects.get(
                    provider_id=m['provider_id'],
                    name=test_name
                )
                print(f"✅ 查询成功: {result.name} from {result.provider.name}")
            except Exception as e:
                print(f"❌ 查询失败: {e}")
        
        # 测试错误的查询方式（仅使用name）
        print(f"\n测试错误的查询方式（仅使用 name='{test_name}'）:")
        try:
            result = LLMModel.objects.get(name=test_name)
            print(f"⚠️  查询返回了结果（这不应该发生）: {result.name}")
        except LLMModel.MultipleObjectsReturned as e:
            print(f"✅ 正确抛出 MultipleObjectsReturned 异常")
            print(f"   错误信息: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    else:
        print("\n✅ 没有发现重复的模型名称")
        print("   所有模型名称在各自的供应商内都是唯一的")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    test_duplicate_model_names()
