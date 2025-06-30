#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试策略配置API接口
"""

import requests
import json

def test_strategy_api():
    """测试策略配置API"""
    print("=== CChanTrader-AI 策略配置API测试 ===")
    
    base_url = "http://localhost:8080"
    
    try:
        # 1. 测试获取策略配置
        print("\n1. 测试获取策略配置API:")
        
        response = requests.get(f"{base_url}/api/get_strategy_config")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ 获取策略配置成功")
                config = data['config']
                for key, value in config.items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ 获取失败: {data['message']}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
        
        # 2. 测试保存策略配置
        print("\n2. 测试保存策略配置API:")
        
        test_config = {
            'tech_weight': 0.72,
            'auction_weight': 0.28,
            'score_threshold': 0.68,
            'max_recommendations': 12,
            'min_price': 4.0,
            'max_price': 280.0
        }
        
        print(f"保存配置: {test_config}")
        
        response = requests.post(
            f"{base_url}/api/save_strategy_config",
            json=test_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ 策略配置保存成功")
                print(f"返回消息: {data['message']}")
                if 'config' in data:
                    print("保存的配置:")
                    for key, value in data['config'].items():
                        if key != 'updated_at':
                            print(f"  {key}: {value}")
            else:
                print(f"❌ 保存失败: {data['message']}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
        
        # 3. 验证保存后的配置
        print("\n3. 验证保存后的配置:")
        
        response = requests.get(f"{base_url}/api/get_strategy_config")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                saved_config = data['config']
                
                success = True
                for key, expected_value in test_config.items():
                    actual_value = saved_config.get(key)
                    if key in ['tech_weight', 'auction_weight', 'score_threshold', 'min_price', 'max_price']:
                        if abs(float(actual_value) - float(expected_value)) > 0.001:
                            print(f"❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
                            success = False
                        else:
                            print(f"✅ {key}: {actual_value}")
                    elif key == 'max_recommendations':
                        if int(actual_value) != int(expected_value):
                            print(f"❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
                            success = False
                        else:
                            print(f"✅ {key}: {actual_value}")
                
                if not success:
                    return False
            else:
                print(f"❌ 获取失败: {data['message']}")
                return False
        
        # 4. 测试参数验证
        print("\n4. 测试参数验证:")
        
        # 测试无效权重
        invalid_config = {
            'tech_weight': 0.9,  # 超出范围
            'auction_weight': 0.3,
            'score_threshold': 0.65,
            'max_recommendations': 15,
            'min_price': 2.0,
            'max_price': 300.0
        }
        
        response = requests.post(
            f"{base_url}/api/save_strategy_config",
            json=invalid_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data['success']:
                print(f"✅ 参数验证: 正确拒绝无效配置 - {data['message']}")
            else:
                print("❌ 参数验证: 错误接受了无效配置")
                return False
        
        # 5. 测试权重总和验证
        print("\n5. 测试权重总和验证:")
        
        invalid_sum_config = {
            'tech_weight': 0.6,
            'auction_weight': 0.5,  # 总和1.1
            'score_threshold': 0.65,
            'max_recommendations': 15,
            'min_price': 2.0,
            'max_price': 300.0
        }
        
        response = requests.post(
            f"{base_url}/api/save_strategy_config",
            json=invalid_sum_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data['success']:
                print(f"✅ 权重验证: 正确拒绝权重总和错误 - {data['message']}")
            else:
                print("❌ 权重验证: 错误接受了权重总和错误")
                return False
        
        print("\n6. 总体API测试结果: ✅ 通过")
        
        print("\n🎉 策略配置API测试全部通过！")
        print("功能验证:")
        print("1. ✅ GET /api/get_strategy_config - 获取配置")
        print("2. ✅ POST /api/save_strategy_config - 保存配置")
        print("3. ✅ 参数范围验证")
        print("4. ✅ 权重总和验证")
        print("5. ✅ 数据持久化")
        
        print(f"\n🌐 Web应用运行在: {base_url}")
        print("现在你可以访问配置页面测试策略参数修改功能！")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到Web应用 {base_url}")
        print("请确保Web应用正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy_api()
    if success:
        print("\n✨ 策略参数配置功能已完全修复并可正常使用！")
    else:
        print("\n⚠️ 仍有问题需要解决")