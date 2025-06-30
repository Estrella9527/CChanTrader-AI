#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI Web管理平台启动脚本
"""

import os
import sys
import subprocess
import time
import webbrowser
from datetime import datetime

def check_dependencies():
    """检查依赖包"""
    required_packages = ['flask', 'pandas', 'numpy', 'akshare', 'baostock', 'schedule']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 安装命令:")
        print(f"pip3 install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """检查环境配置"""
    env_file = '/Users/yang/.env'
    
    if not os.path.exists(env_file):
        print("⚠️ 未找到环境配置文件 .env")
        print("请先运行 python3 setup_trading_email.py 进行配置")
        return False
    
    return True

def create_sample_data():
    """创建示例数据"""
    try:
        from web_app import WebAppManager
        
        manager = WebAppManager()
        
        # 创建示例推荐数据
        sample_recommendations = [
            {
                'symbol': 'sh.600000',
                'stock_name': '浦发银行',
                'market': '上海主板',
                'current_price': 13.65,
                'total_score': 0.856,
                'tech_score': 0.800,
                'auction_score': 0.720,
                'auction_ratio': 1.2,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '温和高开，建议买入',
                'entry_price': 13.65,
                'stop_loss': 12.56,
                'target_price': 15.70
            },
            {
                'symbol': 'sz.000001',
                'stock_name': '平安银行',
                'market': '深圳主板',
                'current_price': 12.38,
                'total_score': 0.789,
                'tech_score': 0.750,
                'auction_score': 0.680,
                'auction_ratio': 0.8,
                'gap_type': 'flat',
                'confidence': 'high',
                'strategy': '平开强势，关注买入',
                'entry_price': 12.38,
                'stop_loss': 11.39,
                'target_price': 14.24
            },
            {
                'symbol': 'sz.002475',
                'stock_name': '立讯精密',
                'market': '中小板',
                'current_price': 35.20,
                'total_score': 0.743,
                'tech_score': 0.720,
                'auction_score': 0.650,
                'auction_ratio': -0.5,
                'gap_type': 'gap_down',
                'confidence': 'medium',
                'strategy': '小幅低开，可逢低买入',
                'entry_price': 35.20,
                'stop_loss': 32.38,
                'target_price': 40.48
            },
            {
                'symbol': 'sz.300015',
                'stock_name': '爱尔眼科',
                'market': '创业板',
                'current_price': 12.38,
                'total_score': 0.698,
                'tech_score': 0.680,
                'auction_score': 0.630,
                'auction_ratio': 2.1,
                'gap_type': 'gap_up',
                'confidence': 'medium',
                'strategy': '高开适中，可考虑买入',
                'entry_price': 12.38,
                'stop_loss': 11.39,
                'target_price': 14.24
            }
        ]
        
        today = datetime.now().strftime('%Y-%m-%d')
        manager.save_recommendations(sample_recommendations, today)
        
        print("✅ 示例数据已创建")
        return True
        
    except Exception as e:
        print(f"⚠️ 创建示例数据失败: {e}")
        return False

def start_web_app():
    """启动Web应用"""
    try:
        print("🚀 启动 CChanTrader-AI Web管理平台...")
        
        # 启动Flask应用
        import web_app
        
        # 创建示例数据
        create_sample_data()
        
        print("🌐 访问地址: http://localhost:8080")
        print("🛑 停止服务: Ctrl+C")
        print("="*50)
        
        # 延迟2秒后自动打开浏览器
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:8080')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动应用
        web_app.app.run(debug=False, host='0.0.0.0', port=8080)
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 CChanTrader-AI Web管理平台")
    print("📊 智能股票分析与交易决策管理系统")
    print("=" * 60)
    
    # 检查依赖
    print("📦 检查系统依赖...")
    if not check_dependencies():
        return
    
    # 检查环境
    print("⚙️ 检查环境配置...")
    if not check_environment():
        return
    
    print("✅ 系统检查完成\n")
    
    # 显示功能介绍
    print("🎯 主要功能:")
    print("   📊 实时系统监控面板")
    print("   🎯 股票推荐可视化展示") 
    print("   ⚙️ 邮件配置管理")
    print("   📈 数据分析和筛选")
    print("   🔧 系统控制和调度管理")
    print()
    
    # 启动Web应用
    start_web_app()

if __name__ == "__main__":
    main()