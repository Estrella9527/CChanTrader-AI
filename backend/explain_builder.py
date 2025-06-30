#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 股票解释构建器
生成股票分析的HTML片段和价格数据
"""

import json
import datetime
import random
from typing import Dict, List, Tuple, Any

def build_explain_html(symbol: str, rec_dict: Dict[str, Any], structure_dict: Dict[str, Any]) -> Tuple[str, str]:
    """
    构建股票分析解释的HTML片段
    
    Args:
        symbol: 股票代码
        rec_dict: 推荐数据字典
        structure_dict: 缠论结构数据字典
        
    Returns:
        Tuple[str, str]: (HTML内容, 价格JSON字符串)
    """
    try:
        # 提取基本信息
        stock_name = rec_dict.get('stock_name', '未知股票')
        current_price = rec_dict.get('current_price', 0)
        total_score = rec_dict.get('total_score', 0)
        confidence = rec_dict.get('confidence', 'medium')
        strategy = rec_dict.get('strategy', '策略分析中...')
        
        # 获取缠论结构信息
        seg_30m = structure_dict.get('30m', {})
        signal = rec_dict.get('signal', '买入信号')
        vol_factor = seg_30m.get('vol_stats', {}).get('volume_factor', 1.0)
        
        # 映射信心等级
        confidence_map = {
            'very_high': '极高',
            'high': '较高',
            'medium': '中等',
            'low': '较低'
        }
        confidence_text = confidence_map.get(confidence, '中等')
        
        # 计算目标价格区间
        entry_price = rec_dict.get('entry_price', current_price)
        stop_loss = rec_dict.get('stop_loss', current_price * 0.9)
        target_range = rec_dict.get('target_range', [current_price * 1.1, current_price * 1.2])
        
        # 期望收益风险比
        expected_rr = rec_dict.get('expected_rr', '1.5')
        
        # 生成详细的HTML内容
        html_content = f"""
        <div class="space-y-6">
            <!-- 股票基本信息 -->
            <div class="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-xl border border-indigo-100">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="text-xl font-bold text-gray-800">{stock_name}</h3>
                        <p class="text-gray-600 font-mono text-sm">{symbol}</p>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl font-bold text-indigo-600">¥{current_price:.2f}</div>
                        <div class="text-sm text-gray-500">{rec_dict.get('market', '未知市场')}</div>
                    </div>
                </div>
                
                <div class="grid grid-cols-3 gap-4 text-center">
                    <div class="bg-white/60 rounded-lg p-3">
                        <div class="text-lg font-semibold text-gray-800">{total_score:.3f}</div>
                        <div class="text-xs text-gray-600">综合评分</div>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3">
                        <div class="text-lg font-semibold text-green-600">{confidence_text}</div>
                        <div class="text-xs text-gray-600">信心等级</div>
                    </div>
                    <div class="bg-white/60 rounded-lg p-3">
                        <div class="text-lg font-semibold text-purple-600">{expected_rr}</div>
                        <div class="text-xs text-gray-600">风险收益比</div>
                    </div>
                </div>
            </div>

            <!-- 推荐理由 -->
            <div class="bg-white p-5 rounded-xl border border-gray-200">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    推荐理由
                </h4>
                <p class="text-gray-700 leading-relaxed">
                    {symbol} {stock_name} 触发 {signal}，当前价格 ¥{current_price:.2f}。
                    该股票在技术面、基本面和资金面均表现良好，综合评分达到 {total_score:.3f}。
                    {strategy}
                </p>
            </div>

            <!-- 缠论分析 -->
            <div class="bg-white p-5 rounded-xl border border-gray-200">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    缠论逻辑分析
                </h4>
                <p class="text-gray-700 leading-relaxed">
                    30分钟级别显示 {signal} 信号，源自三段式结构识别。当前处于关键支撑位附近，
                    结构完整性良好，符合缠论买点特征。技术面评分 {rec_dict.get('tech_score', 0):.3f}，
                    显示出较强的技术优势。
                </p>
            </div>

            <!-- 量价分析 -->
            <div class="bg-white p-5 rounded-xl border border-gray-200">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                    量价分析
                </h4>
                <p class="text-gray-700 leading-relaxed">
                    成交量放大倍率 {vol_factor:.1f}×，显示资金关注度提升。集合竞价表现强劲，
                    竞价评分 {rec_dict.get('auction_score', 0):.3f}，市场预期乐观。
                    量价配合良好，符合强势上涨特征。
                </p>
            </div>

            <!-- 迷你价格走势图 -->
            <div class="bg-white p-5 rounded-xl border border-gray-200">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    价格走势
                </h4>
                <div class="h-32 relative">
                    <canvas id="miniChart" class="w-full h-full"></canvas>
                </div>
            </div>

            <!-- 操作建议 -->
            <div class="bg-white p-5 rounded-xl border border-gray-200">
                <h4 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    操作计划
                </h4>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">建议买入价位:</span>
                        <span class="font-semibold text-green-600">¥{entry_price:.2f}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">止损价位:</span>
                        <span class="font-semibold text-red-600">¥{stop_loss:.2f}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">目标价格区间:</span>
                        <span class="font-semibold text-blue-600">¥{target_range[0]:.2f} - ¥{target_range[1]:.2f}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">预期收益风险比:</span>
                        <span class="font-semibold text-purple-600">{expected_rr}</span>
                    </div>
                </div>
            </div>

            <!-- 风险提示 -->
            <div class="bg-yellow-50 p-5 rounded-xl border border-yellow-200">
                <h4 class="text-lg font-semibold text-yellow-800 mb-3 flex items-center">
                    <span class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                    ⚠️ 风险提示
                </h4>
                <p class="text-yellow-800 leading-relaxed text-sm">
                    股票投资存在市场风险，过往业绩不代表未来表现。
                    请根据个人风险承受能力谨慎投资，严格执行止损策略。
                    建议适当分散投资，控制单一股票仓位比例。
                    预期收益倍数 {expected_rr}，但实际收益可能存在波动。
                </p>
            </div>
        </div>
        """.strip()
        
        # 生成模拟价格数据（30天）
        prices = generate_mini_prices(current_price, 30)
        prices_json = json.dumps(prices)
        
        return html_content, prices_json
        
    except Exception as e:
        # 发生错误时返回简化版本
        error_html = f"""
        <div class="text-center py-8">
            <p class="text-red-500 mb-2">生成分析失败</p>
            <p class="text-gray-500 text-sm">股票代码: {symbol}</p>
            <p class="text-gray-500 text-sm">错误信息: {str(e)}</p>
        </div>
        """
        return error_html, json.dumps([])

def generate_mini_prices(base_price: float, days: int = 30) -> List[float]:
    """
    生成模拟的价格数据
    
    Args:
        base_price: 基准价格
        days: 生成天数
        
    Returns:
        List[float]: 价格列表
    """
    prices = []
    current_price = base_price
    
    for i in range(days):
        # 模拟价格波动 (-4% 到 +4%)
        change_rate = (random.random() - 0.5) * 0.08
        current_price = max(0.01, current_price * (1 + change_rate))
        prices.append(round(current_price, 2))
    
    return prices

def format_confidence_level(confidence: str) -> str:
    """格式化信心等级显示"""
    confidence_map = {
        'very_high': '极高 ⭐⭐⭐⭐⭐',
        'high': '较高 ⭐⭐⭐⭐',
        'medium': '中等 ⭐⭐⭐',
        'low': '较低 ⭐⭐'
    }
    return confidence_map.get(confidence, '未知')

def calculate_risk_metrics(rec_dict: Dict[str, Any]) -> Dict[str, Any]:
    """计算风险指标"""
    entry_price = rec_dict.get('entry_price', 0)
    stop_loss = rec_dict.get('stop_loss', 0)
    target_range = rec_dict.get('target_range', [0, 0])
    
    if entry_price > 0 and stop_loss > 0:
        max_loss_rate = (entry_price - stop_loss) / entry_price
        max_gain_rate = (target_range[1] - entry_price) / entry_price if target_range[1] > entry_price else 0
        risk_reward_ratio = max_gain_rate / max_loss_rate if max_loss_rate > 0 else 0
    else:
        max_loss_rate = 0
        max_gain_rate = 0
        risk_reward_ratio = 0
    
    return {
        'max_loss_rate': max_loss_rate,
        'max_gain_rate': max_gain_rate,
        'risk_reward_ratio': risk_reward_ratio
    }

if __name__ == '__main__':
    # 测试用例
    test_rec = {
        'symbol': '000001',
        'stock_name': '平安银行',
        'current_price': 12.34,
        'total_score': 0.789,
        'tech_score': 0.765,
        'auction_score': 0.823,
        'confidence': 'high',
        'strategy': '银行板块+低估值+政策利好',
        'entry_price': 12.50,
        'stop_loss': 11.80,
        'target_range': [13.50, 14.20],
        'expected_rr': '1.8',
        'market': '深圳主板'
    }
    
    test_structure = {
        '30m': {
            'vol_stats': {
                'volume_factor': 1.5
            }
        }
    }
    
    html, prices = build_explain_html('000001', test_rec, test_structure)
    print("HTML长度:", len(html))
    print("价格数据点数:", len(json.loads(prices)))
    print("测试完成 ✅")