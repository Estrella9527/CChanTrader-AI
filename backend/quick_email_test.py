#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速邮件发送测试
验证新授权码是否有效
"""

import sys
sys.path.append('/Users/yang')

from backend.services.email_config import EmailSender
from web_app import generate_test_report_data

def quick_email_test():
    """快速邮件测试"""
    print("=== 快速邮件发送测试 ===")
    
    try:
        # 创建邮件发送器
        sender = EmailSender()
        
        print(f"发送邮箱: {sender.sender_email}")
        print(f"邮件服务商: {sender.email_provider}")
        print(f"接收邮箱: {sender.recipient_emails}")
        print(f"授权码长度: {len(sender.sender_password)}")
        
        if not all([sender.sender_email, sender.sender_password, sender.recipient_emails]):
            print("❌ 邮件配置不完整")
            return False
        
        print("\n正在生成测试邮件内容...")
        test_data = generate_test_report_data()
        
        print("正在发送测试邮件...")
        success = sender.send_daily_report(test_data)
        
        if success:
            print("✅ 邮件发送成功！")
            print("请检查收件箱，新授权码已生效！")
            return True
        else:
            print("❌ 邮件发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_email_test()
    if success:
        print("\n🎉 邮件配置问题已彻底解决！")
    else:
        print("\n⚠️ 仍需检查授权码或网络设置")