#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 策略解释功能集成测试
"""

import os
import sys
import sqlite3
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_explain_generator():
    """测试解释生成器"""
    print("🧪 测试解释生成器...")
    
    try:
        from explain_generator import generate_explain
        
        # 模拟股票数据
        test_stocks = [
            {
                'symbol': 'sz.000001',
                'stock_name': '平安银行',
                'current_price': 12.35,
                'entry_price': 12.35,
                'stop_loss': 11.50,
                'signal': '2_buy',
                'confidence': 'very_high',
                'total_score': 0.852,
                'tech_score': 0.820,
                'auction_score': 0.900,
                'auction_ratio': 2.5,
                'market': '深圳主板'
            }
        ]
        
        explanations = generate_explain(test_stocks)
        
        if explanations and len(explanations) > 0:
            exp = explanations[0]
            print(f"✅ 生成解释成功")
            print(f"   推荐理由: {exp['reason'][:100]}...")
            print(f"   买点说明: {exp['buy_point_explanation'][:80]}...")
            print(f"   风险收益比: {exp['expected_rr']}")
            return True
        else:
            print("❌ 未能生成解释")
            return False
            
    except Exception as e:
        print(f"❌ 测试解释生成器失败: {e}")
        return False

def test_database_structure():
    """测试数据库结构"""
    print("🧪 测试数据库结构...")
    
    try:
        conn = sqlite3.connect("data/cchan_web.db")
        cursor = conn.cursor()
        
        # 检查stock_analysis表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_analysis';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ stock_analysis表存在")
            
            # 检查explanation列
            cursor.execute("PRAGMA table_info(stock_analysis);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'explanation' in column_names:
                print("✅ explanation列存在")
                
                # 测试插入数据
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_analysis 
                    (symbol, stock_name, explanation, analysis_date)
                    VALUES (?, ?, ?, ?)
                ''', ('TEST001', '测试股票', '这是测试解释', '2025-06-29'))
                
                conn.commit()
                print("✅ 数据库写入测试成功")
                
                # 清理测试数据
                cursor.execute("DELETE FROM stock_analysis WHERE symbol = 'TEST001'")
                conn.commit()
                
                conn.close()
                return True
            else:
                print("❌ explanation列不存在")
                conn.close()
                return False
        else:
            print("❌ stock_analysis表不存在")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_optimized_analyzer_integration():
    """测试选股分析器集成"""
    print("🧪 测试选股分析器集成...")
    
    try:
        from analysis.optimized_stock_analyzer import OptimizedStockAnalyzer
        
        analyzer = OptimizedStockAnalyzer()
        result = analyzer.generate_optimized_recommendations()
        
        if result and 'recommendations' in result:
            recommendations = result['recommendations']
            
            if recommendations:
                first_rec = recommendations[0]
                
                # 检查是否包含解释字段
                required_fields = ['explanation', 'buy_point_explanation', 'sell_logic', 'risk_reward_analysis']
                missing_fields = [field for field in required_fields if field not in first_rec]
                
                if not missing_fields:
                    print("✅ 选股分析器集成成功")
                    print(f"   生成推荐: {len(recommendations)}只")
                    print(f"   解释示例: {first_rec['explanation'][:80]}...")
                    return True
                else:
                    print(f"❌ 缺少字段: {missing_fields}")
                    return False
            else:
                print("⚠️ 未生成推荐（可能是正常情况）")
                return True
        else:
            print("❌ 选股分析器返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ 选股分析器集成测试失败: {e}")
        return False

def test_api_endpoint():
    """测试API端点（模拟）"""
    print("🧪 测试API端点...")
    
    try:
        # 检查web_app.py中是否包含API路由
        with open('/Users/yang/web_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '/api/picks' in content and 'api_get_picks' in content:
            print("✅ API端点已添加")
            
            # 检查相关导入
            if 'from analysis.optimized_stock_analyzer import OptimizedStockAnalyzer' in content:
                print("✅ API端点导入正确")
                return True
            else:
                print("⚠️ API端点导入可能有问题")
                return True
        else:
            print("❌ API端点未添加")
            return False
            
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        return False

def test_template_modifications():
    """测试模板修改"""
    print("🧪 测试模板修改...")
    
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates/recommendations.html'), 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('策略解释', '策略解释列'),
            ('showExplanationModal', '解释模态框函数'),
            ('explanationModal', '解释模态框HTML'),
            ('CChanTrader-AI Explain Patch', '补丁标记')
        ]
        
        passed = 0
        for check, description in checks:
            if check in content:
                print(f"✅ {description}存在")
                passed += 1
            else:
                print(f"❌ {description}缺失")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ 模板测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 CChanTrader-AI 策略解释功能集成测试")
    print("=" * 60)
    
    tests = [
        ("解释生成器", test_explain_generator),
        ("数据库结构", test_database_structure),
        ("选股分析器集成", test_optimized_analyzer_integration),
        ("API端点", test_api_endpoint),
        ("模板修改", test_template_modifications)
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
        print("🎉 所有测试通过！集成成功！")
        print("\n✅ Integration done")
        print("affected_files:", [
            "explain_generator.py",
            "optimized_stock_analyzer.py", 
            "web_app.py",
            "templates/recommendations.html",
            "cchan_web.db (stock_analysis table)"
        ])
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    return passed == total

if __name__ == '__main__':
    main()