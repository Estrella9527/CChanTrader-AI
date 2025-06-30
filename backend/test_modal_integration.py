#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试美化表格和Modal功能集成
"""

import os
import sys
import json

def test_files_exist():
    """测试文件是否存在"""
    print("🧪 测试文件存在性...")
    
    files_to_check = [
        ('static/js/pick_modal.js', 'Pick Modal JavaScript'),
        ('templates/base.html', 'Base Template'),
        ('templates/recommendations.html', 'Recommendations Template')
    ]
    
    passed = 0
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {description}: 存在")
            passed += 1
        else:
            print(f"❌ {description}: 不存在")
    
    return passed == len(files_to_check)

def test_base_html_scripts():
    """测试base.html中的脚本引用"""
    print("🧪 测试base.html脚本引用...")
    
    try:
        with open('frontend/templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_scripts = [
            ('htmx.org@1.9.6', 'HTMX 1.9.6'),
            ('hyperscript.org@0.9.7', 'Hyperscript 0.9.7'),
            ('chart.js', 'Chart.js'),
            ('pick_modal.js', 'Pick Modal Script')
        ]
        
        passed = 0
        for script_ref, description in required_scripts:
            if script_ref in content:
                print(f"✅ {description}: 已引用")
                passed += 1
            else:
                print(f"❌ {description}: 未引用")
        
        return passed == len(required_scripts)
        
    except Exception as e:
        print(f"❌ 读取base.html失败: {e}")
        return False

def test_recommendations_html_modifications():
    """测试recommendations.html的修改"""
    print("🧪 测试recommendations.html修改...")
    
    try:
        with open('frontend/templates/recommendations.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('策略解释', '策略解释列标题'),
            ('hx-get="/api/stocks', 'HTMX GET请求'),
            ('hx-target="#pickModalBody"', 'HTMX目标'),
            ('id="pickModal"', 'Pick Modal容器'),
            ('backdrop-blur', '玻璃效果'),
            ('id="pickModalBody"', 'Modal主体')
        ]
        
        passed = 0
        for check, description in checks:
            if check in content:
                print(f"✅ {description}: 存在")
                passed += 1
            else:
                print(f"❌ {description}: 不存在")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ 读取recommendations.html失败: {e}")
        return False

def test_pick_modal_js():
    """测试pick_modal.js脚本"""
    print("🧪 测试pick_modal.js脚本...")
    
    try:
        with open('static/js/pick_modal.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('htmx:afterSwap', 'HTMX事件监听'),
            ('pickModalBody', 'Modal主体处理'),
            ('Chart.js', 'Chart.js集成'),
            ('miniChart', '迷你图表'),
            ('addEventListener', '事件监听器'),
            ('Escape', 'ESC键处理')
        ]
        
        passed = 0
        for check, description in checks:
            if check in content:
                print(f"✅ {description}: 存在")
                passed += 1
            else:
                print(f"❌ {description}: 不存在")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ 读取pick_modal.js失败: {e}")
        return False

def test_web_app_api():
    """测试web_app.py API端点"""
    print("🧪 测试web_app.py API端点...")
    
    try:
        with open('web_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('/api/stocks/<symbol>/analysis', 'HTMX API端点'),
            ('get_stock_analysis_detail', 'API处理函数'),
            ('canvas id="miniChart"', 'Chart.js canvas'),
            ('data-prices=', '价格数据属性'),
            ('bg-gradient-to-r', 'Tailwind渐变样式'),
            ('backdrop-blur', '玻璃效果样式')
        ]
        
        passed = 0
        for check, description in checks:
            if check in content:
                print(f"✅ {description}: 存在")
                passed += 1
            else:
                print(f"❌ {description}: 不存在")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ 读取web_app.py失败: {e}")
        return False

def test_modal_functionality():
    """测试Modal功能逻辑"""
    print("🧪 测试Modal功能逻辑...")
    
    # 检查JavaScript逻辑
    try:
        with open('static/js/pick_modal.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 检查HTML模板
        with open('frontend/templates/recommendations.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        functionality_checks = [
            # JavaScript功能检查
            ('document.addEventListener("htmx:afterSwap"' in js_content, 'HTMX响应处理'),
            ('new Chart(' in js_content, 'Chart.js图表创建'),
            ('toggle .hidden' in js_content, '模态框显示/隐藏'),
            ('keydown' in js_content, '键盘事件处理'),
            
            # HTML模板检查
            ('_="on click toggle .hidden' in html_content, 'Hyperscript点击处理'),
            ('hx-trigger="click"' in html_content, 'HTMX点击触发'),
            ('bg-white/90 backdrop-blur-lg' in html_content, '玻璃卡片样式'),
            ('absolute inset-0 bg-black/60' in html_content, '背景遮罩')
        ]
        
        passed = 0
        for check, description in functionality_checks:
            if check:
                print(f"✅ {description}: 正常")
                passed += 1
            else:
                print(f"❌ {description}: 异常")
        
        return passed == len(functionality_checks)
        
    except Exception as e:
        print(f"❌ Modal功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 CChanTrader-AI 美化表格和Modal功能测试")
    print("=" * 60)
    
    tests = [
        ("文件存在性", test_files_exist),
        ("Base HTML脚本", test_base_html_scripts),
        ("Recommendations HTML修改", test_recommendations_html_modifications),
        ("Pick Modal JS脚本", test_pick_modal_js),
        ("Web App API端点", test_web_app_api),
        ("Modal功能逻辑", test_modal_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n📋 {name}测试:")
        if test_func():
            passed += 1
        print("-" * 40)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！美化功能集成成功！")
        print("\n✨ 新增功能:")
        print("  • HTMX无刷新加载股票详情")
        print("  • 玻璃卡片Modal设计")
        print("  • Chart.js迷你K线图")
        print("  • Hyperscript交互增强")
        print("  • 响应式设计优化")
        
        print("\n📋 修改的文件:")
        modified_files = [
            "static/js/pick_modal.js (新建)",
            "templates/base.html (修改)",
            "templates/recommendations.html (修改)",
            "web_app.py (新增API端点)"
        ]
        
        for file_path in modified_files:
            print(f"  • {file_path}")
            
        print("\n🚀 使用方法:")
        print("  1. 启动服务器: python web_app.py")
        print("  2. 访问推荐页面: http://localhost:8080/recommendations")
        print("  3. 点击策略解释列的'查看'按钮")
        print("  4. 享受美化的Modal和K线图体验！")
        
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    return passed == total

if __name__ == '__main__':
    main()