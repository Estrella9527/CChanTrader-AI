#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置保存和加载功能
用于验证邮件配置缓存问题是否已解决
"""

import os
import sys
from dotenv import load_dotenv

def test_config_save_load():
    """测试配置的保存和加载"""
    print("=== CChanTrader-AI 配置缓存问题测试 ===")
    
    # 1. 显示当前配置
    print("\n1. 当前环境变量配置:")
    load_dotenv(override=True)
    
    current_email = os.getenv('SENDER_EMAIL', 'NOT_SET')
    current_password = os.getenv('SENDER_PASSWORD', 'NOT_SET') 
    current_recipient = os.getenv('RECIPIENT_EMAILS', 'NOT_SET')
    current_provider = os.getenv('EMAIL_PROVIDER', 'NOT_SET')
    
    print(f"发送邮箱: {current_email}")
    print(f"邮箱密码: {'*' * len(current_password) if current_password != 'NOT_SET' else 'NOT_SET'}")
    print(f"接收邮箱: {current_recipient}")
    print(f"邮件服务商: {current_provider}")
    
    # 2. 测试保存功能
    print("\n2. 测试配置保存...")
    
    test_config = {
        'sender_email': 'azhizhengzhuan@gmail.com',
        'sender_password': 'ovun jujl wwwl ybpn',  # 你提供的新授权码
        'recipient_emails': 'azhizhengzhuan@gmail.com',
        'email_provider': 'gmail'
    }
    
    # 导入WebAppManager进行保存测试
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from web_app import WebAppManager
        
        manager = WebAppManager()
        manager.save_email_config(test_config)
        print("✅ 配置保存成功")
        
    except Exception as e:
        print(f"❌ 配置保存失败: {e}")
        return False
    
    # 3. 验证加载
    print("\n3. 验证配置加载...")
    
    # 强制重新加载
    load_dotenv(override=True)
    
    new_email = os.getenv('SENDER_EMAIL', 'NOT_SET')
    new_password = os.getenv('SENDER_PASSWORD', 'NOT_SET')
    new_recipient = os.getenv('RECIPIENT_EMAILS', 'NOT_SET')
    new_provider = os.getenv('EMAIL_PROVIDER', 'NOT_SET')
    
    print(f"新发送邮箱: {new_email}")
    print(f"新邮箱密码: {'*' * len(new_password) if new_password != 'NOT_SET' else 'NOT_SET'}")
    print(f"新接收邮箱: {new_recipient}")
    print(f"新邮件服务商: {new_provider}")
    
    # 4. 验证配置是否正确保存
    print("\n4. 配置验证结果:")
    
    success = True
    if new_email != test_config['sender_email']:
        print(f"❌ 发送邮箱不匹配: 期望 {test_config['sender_email']}, 实际 {new_email}")
        success = False
    else:
        print("✅ 发送邮箱匹配")
    
    if new_password != test_config['sender_password']:
        print(f"❌ 邮箱密码不匹配: 期望 {test_config['sender_password']}, 实际 {new_password}")
        success = False
    else:
        print("✅ 邮箱密码匹配")
    
    if new_recipient != test_config['recipient_emails']:
        print(f"❌ 接收邮箱不匹配: 期望 {test_config['recipient_emails']}, 实际 {new_recipient}")
        success = False
    else:
        print("✅ 接收邮箱匹配")
    
    if new_provider != test_config['email_provider']:
        print(f"❌ 邮件服务商不匹配: 期望 {test_config['email_provider']}, 实际 {new_provider}")
        success = False
    else:
        print("✅ 邮件服务商匹配")
    
    # 5. 测试EmailSender加载
    print("\n5. 测试EmailSender配置加载...")
    
    try:
        from backend.services.email_config import EmailSender
        
        sender = EmailSender()
        print(f"EmailSender发送邮箱: {sender.sender_email}")
        print(f"EmailSender密码长度: {len(sender.sender_password) if sender.sender_password else 0}")
        print(f"EmailSender接收邮箱: {sender.recipient_emails}")
        print(f"EmailSender服务商: {sender.email_provider}")
        
        if (sender.sender_email == test_config['sender_email'] and
            sender.sender_password == test_config['sender_password'] and
            ','.join(sender.recipient_emails) == test_config['recipient_emails'] and
            sender.email_provider == test_config['email_provider']):
            print("✅ EmailSender配置加载正确")
        else:
            print("❌ EmailSender配置加载有误")
            success = False
            
    except Exception as e:
        print(f"❌ EmailSender测试失败: {e}")
        success = False
    
    # 6. 测试结果
    print(f"\n6. 总体测试结果: {'✅ 通过' if success else '❌ 失败'}")
    
    if success:
        print("\n🎉 恭喜！配置缓存问题已解决！")
        print("现在你可以：")
        print("1. 在Web界面正常保存邮件配置")
        print("2. 新的授权码会立即生效")
        print("3. 测试邮件功能会使用最新配置")
    else:
        print("\n⚠️ 配置缓存问题仍然存在，请检查：")
        print("1. .env文件权限是否正确")
        print("2. load_dotenv调用是否正确")
        print("3. 环境变量加载顺序是否有问题")
    
    return success

if __name__ == "__main__":
    test_config_save_load()