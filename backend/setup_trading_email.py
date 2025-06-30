#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 交易日报邮件系统快速配置脚本
"""

import os
import sys
from datetime import datetime

def setup_email_config():
    """配置邮件设置"""
    print("📧 CChanTrader-AI 交易日报邮件系统配置")
    print("=" * 50)
    
    # 获取用户输入
    sender_email = input("📮 请输入发送邮箱地址: ").strip()
    sender_password = input("🔑 请输入邮箱授权码/密码: ").strip()
    recipient_email = input("📬 请输入接收邮箱地址: ").strip()
    
    # 选择邮件服务商
    print("\n📡 请选择邮件服务商:")
    print("1. QQ邮箱")
    print("2. 163邮箱") 
    print("3. Gmail")
    print("4. Outlook")
    print("5. 新浪邮箱")
    
    provider_choice = input("请输入数字选择 (默认1): ").strip() or "1"
    
    provider_map = {
        "1": "qq",
        "2": "163", 
        "3": "gmail",
        "4": "outlook",
        "5": "sina"
    }
    
    email_provider = provider_map.get(provider_choice, "qq")
    
    # 生成.env文件
    env_content = f"""# CChanTrader-AI 交易日报邮件配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 发送邮箱
SENDER_EMAIL={sender_email}

# 邮箱授权码/密码
SENDER_PASSWORD={sender_password}

# 接收邮箱
RECIPIENT_EMAIL={recipient_email}

# 邮件服务商
EMAIL_PROVIDER={email_provider}

# 其他配置 (如果需要)
AIHUBMIX_API_KEY=your_api_key_here
"""
    
    # 保存配置文件
    env_path = '/Users/yang/.env'
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ 邮件配置已保存到: {env_path}")
    
    # 提供邮箱配置指导
    print(f"\n📋 {email_provider.upper()}邮箱配置提示:")
    if email_provider == "qq":
        print("1. 登录QQ邮箱 → 设置 → 账户")
        print("2. 开启'SMTP服务'")
        print("3. 生成授权码（注意：不是QQ密码）")
        print("4. 使用生成的授权码作为密码")
    elif email_provider == "163":
        print("1. 登录163邮箱 → 设置 → 客户端授权密码")
        print("2. 开启'SMTP服务'")
        print("3. 设置客户端授权密码")
        print("4. 使用授权密码登录")
    elif email_provider == "gmail":
        print("1. 开启两步验证")
        print("2. 生成应用专用密码")
        print("3. 使用应用密码而非Gmail密码")
    
    return True

def test_email_system():
    """测试邮件系统"""
    print("\n🧪 测试邮件系统...")
    
    try:
        from backend.services.email_config import EmailSender
        
        email_sender = EmailSender()
        
        # 检查配置
        if not all([email_sender.sender_email, email_sender.sender_password, email_sender.recipient_email]):
            print("❌ 邮件配置不完整")
            return False
        
        # 发送测试邮件
        success = email_sender.test_email_connection()
        
        if success:
            print("✅ 邮件系统测试成功!")
            print(f"📧 测试邮件已发送到: {email_sender.recipient_email}")
            return True
        else:
            print("❌ 邮件系统测试失败")
            print("请检查邮箱配置和网络连接")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_daily_report():
    """测试日报生成"""
    print("\n📊 测试日报生成...")
    
    try:
        from daily_report_generator import DailyReportGenerator
        
        generator = DailyReportGenerator()
        
        # 模拟测试数据
        test_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'recommendations': [
                {
                    'symbol': 'TEST001',
                    'stock_name': '测试股票',
                    'market': '测试市场',
                    'current_price': 10.00,
                    'total_score': 0.850,
                    'tech_score': 0.800,
                    'auction_score': 0.750,
                    'auction_ratio': 1.5,
                    'gap_type': 'gap_up',
                    'capital_bias': 0.65,
                    'rsi': 60.0,
                    'volume_ratio': 1.2,
                    'entry_price': 10.00,
                    'stop_loss': 9.20,
                    'target_price': 11.50,
                    'confidence': 'high',
                    'strategy': '温和高开，建议买入'
                }
            ],
            'market_summary': {
                'total_analyzed': 100,
                'total_recommended': 1,
                'avg_score': 0.850
            },
            'auction_analysis': {
                'avg_auction_ratio': 1.0,
                'gap_up_count': 40,
                'flat_count': 35,
                'gap_down_count': 25
            }
        }
        
        # 发送测试日报
        success = generator.email_sender.send_daily_report(test_data)
        
        if success:
            print("✅ 测试日报发送成功!")
            print("📧 请查收您的邮箱")
            return True
        else:
            print("❌ 测试日报发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def setup_scheduler():
    """设置调度器"""
    print("\n⏰ 设置交易日调度器...")
    
    print("📅 调度器配置:")
    print("  - 执行时间: 交易日 9:25-9:29")
    print("  - 备用时间: 9:30, 15:05")
    print("  - 自动判断交易日")
    print("  - 防重复发送")
    
    choice = input("\n是否立即启动调度器? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("\n🚀 启动调度器...")
        print("💡 提示: 按 Ctrl+C 可停止调度器")
        
        try:
            from analysis.trading_day_scheduler import TradingDayScheduler
            
            scheduler = TradingDayScheduler()
            scheduler.start_scheduler()
            
        except KeyboardInterrupt:
            print("\n🛑 调度器已停止")
        except Exception as e:
            print(f"❌ 调度器启动失败: {e}")
    else:
        print("\n💡 可以稍后使用以下命令启动调度器:")
        print("python3 trading_day_scheduler.py")
        print("python3 trading_day_scheduler.py --daemon  # 后台运行")

def main():
    """主函数"""
    print("🚀 CChanTrader-AI 交易日报邮件系统")
    print("📧 自动化股票分析 + 邮件推送")
    print("=" * 50)
    
    # 步骤1: 配置邮件
    if not setup_email_config():
        print("❌ 邮件配置失败")
        return
    
    # 步骤2: 测试邮件系统
    if not test_email_system():
        print("❌ 邮件系统测试失败，请检查配置")
        retry = input("是否重新配置? (y/n): ").strip().lower()
        if retry == 'y':
            setup_email_config()
            test_email_system()
        else:
            return
    
    # 步骤3: 测试日报生成
    test_choice = input("\n是否测试发送日报? (y/n): ").strip().lower()
    if test_choice == 'y':
        test_daily_report()
    
    # 步骤4: 设置调度器
    setup_choice = input("\n是否设置交易日调度器? (y/n): ").strip().lower()
    if setup_choice == 'y':
        setup_scheduler()
    
    print("\n🎉 配置完成!")
    print("\n📋 使用说明:")
    print("1. 每个交易日9:25-9:29会自动发送日报")
    print("2. 可查看日志: tail -f /Users/yang/trading_scheduler.log")
    print("3. 手动测试: python3 trading_day_scheduler.py --test")
    print("4. 查看状态: python3 trading_day_scheduler.py --status")
    print("\n📧 详细使用指南: trading_email_setup_guide.md")

if __name__ == "__main__":
    main()