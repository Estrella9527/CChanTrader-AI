#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI Smart Alpha Engine Web Platform
基于 shadcn/ui 的现代化智能交易管理平台
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

def create_sample_data():
    """创建示例数据"""
    try:
        from web_app import WebAppManager
        
        manager = WebAppManager()
        
        # 创建高质量示例推荐数据
        sample_recommendations = [
            {
                'symbol': 'sh.600036',
                'stock_name': '招商银行',
                'market': '上海主板',
                'current_price': 38.56,
                'total_score': 0.892,
                'tech_score': 0.875,
                'auction_score': 0.834,
                'auction_ratio': 2.3,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '强势突破，建议重点关注',
                'entry_price': 38.56,
                'stop_loss': 35.44,
                'target_price': 44.23
            },
            {
                'symbol': 'sz.000858',
                'stock_name': '五粮液',
                'market': '深圳主板',
                'current_price': 168.88,
                'total_score': 0.867,
                'tech_score': 0.845,
                'auction_score': 0.798,
                'auction_ratio': 1.8,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '消费龙头，长期价值显现',
                'entry_price': 168.88,
                'stop_loss': 155.36,
                'target_price': 194.22
            },
            {
                'symbol': 'sh.600000',
                'stock_name': '浦发银行',
                'market': '上海主板',
                'current_price': 13.65,
                'total_score': 0.834,
                'tech_score': 0.820,
                'auction_score': 0.756,
                'auction_ratio': 1.2,
                'gap_type': 'gap_up',
                'confidence': 'very_high',
                'strategy': '温和高开，适合稳健投资',
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
                'tech_score': 0.775,
                'auction_score': 0.723,
                'auction_ratio': 0.8,
                'gap_type': 'flat',
                'confidence': 'high',
                'strategy': '平开强势，关注买入时机',
                'entry_price': 12.38,
                'stop_loss': 11.39,
                'target_price': 14.24
            },
            {
                'symbol': 'sz.002475',
                'stock_name': '立讯精密',
                'market': '中小板',
                'current_price': 35.20,
                'total_score': 0.756,
                'tech_score': 0.742,
                'auction_score': 0.698,
                'auction_ratio': -0.3,
                'gap_type': 'gap_down',
                'confidence': 'high',
                'strategy': '技术修复，逢低布局机会',
                'entry_price': 35.20,
                'stop_loss': 32.38,
                'target_price': 40.48
            },
            {
                'symbol': 'sz.300015',
                'stock_name': '爱尔眼科',
                'market': '创业板',
                'current_price': 45.88,
                'total_score': 0.734,
                'tech_score': 0.720,
                'auction_score': 0.688,
                'auction_ratio': 1.5,
                'gap_type': 'gap_up',
                'confidence': 'high',
                'strategy': '医疗板块复苏，中期看好',
                'entry_price': 45.88,
                'stop_loss': 42.22,
                'target_price': 52.65
            },
            {
                'symbol': 'sz.000002',
                'stock_name': '万科A',
                'market': '深圳主板',
                'current_price': 18.95,
                'total_score': 0.712,
                'tech_score': 0.698,
                'auction_score': 0.665,
                'auction_ratio': 0.5,
                'gap_type': 'flat',
                'confidence': 'medium',
                'strategy': '地产龙头，政策底部配置',
                'entry_price': 18.95,
                'stop_loss': 17.44,
                'target_price': 21.78
            },
            {
                'symbol': 'sh.600519',
                'stock_name': '贵州茅台',
                'market': '上海主板',
                'current_price': 1685.50,
                'total_score': 0.698,
                'tech_score': 0.684,
                'auction_score': 0.654,
                'auction_ratio': 0.2,
                'gap_type': 'flat',
                'confidence': 'medium',
                'strategy': '白酒龙头，长期价值投资',
                'entry_price': 1685.50,
                'stop_loss': 1550.26,
                'target_price': 1938.33
            },
            {
                'symbol': 'sz.300750',
                'stock_name': '宁德时代',
                'market': '创业板',
                'current_price': 198.76,
                'total_score': 0.685,
                'tech_score': 0.672,
                'auction_score': 0.641,
                'auction_ratio': -0.8,
                'gap_type': 'gap_down',
                'confidence': 'medium',
                'strategy': '新能源龙头，回调后关注',
                'entry_price': 198.76,
                'stop_loss': 182.84,
                'target_price': 228.57
            },
            {
                'symbol': 'sh.600276',
                'stock_name': '恒瑞医药',
                'market': '上海主板',
                'current_price': 58.43,
                'total_score': 0.673,
                'tech_score': 0.659,
                'auction_score': 0.628,
                'auction_ratio': 0.3,
                'gap_type': 'flat',
                'confidence': 'medium',
                'strategy': '医药龙头，创新药布局',
                'entry_price': 58.43,
                'stop_loss': 53.76,
                'target_price': 67.19
            }
        ]
        
        today = datetime.now().strftime('%Y-%m-%d')
        manager.save_recommendations(sample_recommendations, today)
        
        print("✅ 高质量示例数据已创建")
        return True
        
    except Exception as e:
        print(f"⚠️ 创建示例数据失败: {e}")
        return False

def show_startup_banner():
    """显示启动横幅"""
    banner = """
╭─────────────────────────────────────────────────────────────╮
│  🎯 Smart Alpha Engine - CChanTrader AI                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                             │
│  🎨 基于 shadcn/ui 的现代化设计系统                           │
│  📊 专业级数据密度与层次感                                     │
│  ⚡ Tailwind CSS + Lucide Icons + Framer Motion           │
│  🔧 极简主义但功能表达清晰                                     │
│  📈 智能量化策略管理平台                                       │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
"""
    print(banner)

def start_web_app():
    """启动Web应用"""
    try:
        print("🚀 启动 Smart Alpha Engine...")
        
        # 启动Flask应用
        import web_app
        
        # 创建示例数据
        create_sample_data()
        
        print("\n🌐 访问地址: http://localhost:8080")
        print("🛑 停止服务: Ctrl+C")
        print("═" * 60)
        print("🎯 核心功能模块:")
        print("   📊 Dashboard    - 智能驾驶舱与实时监控")
        print("   🎯 Signals      - 高密度选股结果展示") 
        print("   ⚙️ Strategy     - 专业因子权重配置")
        print("   📈 Analytics    - 多维度回测分析")
        print("   🔧 Settings     - 系统参数管理")
        print("═" * 60)
        
        # 延迟2秒后自动打开浏览器
        import threading
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open('http://localhost:8080')
                print("🌍 已自动打开浏览器")
            except:
                print("⚠️ 无法自动打开浏览器，请手动访问 http://localhost:8080")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动应用
        web_app.app.run(debug=False, host='0.0.0.0', port=8080)
        
    except KeyboardInterrupt:
        print("\n🛑 Smart Alpha Engine 已停止")
        print("感谢使用智能量化策略管理平台！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    show_startup_banner()
    
    # 检查依赖
    print("📦 检查系统依赖...")
    if not check_dependencies():
        return
    
    print("✅ 系统检查完成\n")
    
    # 显示特性介绍
    print("🎨 设计特色:")
    print("   • 现代化 shadcn/ui 组件设计系统")
    print("   • 专业级数据密度与信息层次")
    print("   • 克制而优雅的交互设计")
    print("   • 响应式布局适配多端设备")
    print("   • 高性能数据可视化图表")
    print()
    
    # 启动Web应用
    start_web_app()

if __name__ == "__main__":
    main()