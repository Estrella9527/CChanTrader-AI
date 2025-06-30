#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 市值筛选工具
专门用于40-200亿中小盘股筛选和评分
"""

import requests
import re
import json
from typing import Dict, List, Optional
import logging

class MarketCapFilter:
    """市值筛选工具"""
    
    def __init__(self):
        """初始化市值筛选器"""
        self.params = {
            'mktcap_min': 40e8,        # 最小市值40亿元
            'mktcap_max': 200e8,       # 最大市值200亿元
            'preferred_range': [60e8, 150e8],  # 最佳区间60-150亿
            'acceptable_range': [20e8, 500e8], # 可接受范围20-500亿
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_market_cap(self, symbol: str) -> Dict:
        """
        获取股票市值信息
        
        Args:
            symbol: 股票代码（支持多种格式）
            
        Returns:
            包含市值信息的字典
        """
        try:
            clean_symbol = symbol.replace('sh.', '').replace('sz.', '')
            
            # 多数据源获取市值
            sources = [
                self._fetch_from_eastmoney,
                self._fetch_from_sina,
                self._estimate_by_code
            ]
            
            for source_func in sources:
                try:
                    result = source_func(clean_symbol)
                    if result and result.get('market_cap', 0) > 0:
                        return self._format_result(symbol, result)
                except Exception as e:
                    self.logger.debug(f"数据源 {source_func.__name__} 失败: {e}")
                    continue
            
            # 兜底估算
            return self._format_result(symbol, self._estimate_by_code(clean_symbol))
            
        except Exception as e:
            self.logger.error(f"获取市值失败 {symbol}: {e}")
            return {'symbol': symbol, 'market_cap': 0, 'source': 'failed'}
    
    def _fetch_from_eastmoney(self, symbol: str) -> Optional[Dict]:
        """从东方财富获取市值"""
        market_prefix = '1' if symbol.startswith('6') else '0'
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market_prefix}.{symbol}&fields=f116,f117,f162"
        
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                market_cap = data['data'].get('f116', 0)  # 总市值
                circulating_cap = data['data'].get('f117', 0)  # 流通市值
                if market_cap and market_cap > 0:
                    return {
                        'market_cap': float(market_cap),
                        'circulating_cap': float(circulating_cap) if circulating_cap else market_cap,
                        'source': 'eastmoney'
                    }
        return None
    
    def _fetch_from_sina(self, symbol: str) -> Optional[Dict]:
        """从新浪财经获取市值"""
        url = f"http://hq.sinajs.cn/list={symbol}"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200 and 'var hq_str_' in response.text:
            try:
                data_parts = response.text.split('"')[1].split(',')
                if len(data_parts) > 20:
                    price = float(data_parts[3])  # 当前价格
                    shares = float(data_parts[18]) if data_parts[18] else 0  # 流通股本
                    if price > 0 and shares > 0:
                        market_cap = price * shares * 10000  # 万元转元
                        return {
                            'market_cap': market_cap,
                            'circulating_cap': market_cap,
                            'source': 'sina'
                        }
            except (ValueError, IndexError):
                pass
        return None
    
    def _estimate_by_code(self, symbol: str) -> Dict:
        """基于股票代码估算市值"""
        estimates = {
            '688': 80e8,   # 科创板平均80亿
            '300': 65e8,   # 创业板平均65亿  
            '002': 95e8,   # 中小板平均95亿
            '6': 180e8,    # 沪市主板平均180亿
            '0': 120e8,    # 深市主板平均120亿
        }
        
        estimated_cap = 100e8  # 默认100亿
        for prefix, cap in estimates.items():
            if symbol.startswith(prefix):
                estimated_cap = cap
                break
        
        return {
            'market_cap': estimated_cap,
            'circulating_cap': estimated_cap * 0.7,  # 假设70%流通
            'source': 'estimated'
        }
    
    def _format_result(self, symbol: str, raw_data: Dict) -> Dict:
        """格式化结果"""
        market_cap = raw_data.get('market_cap', 0)
        market_cap_billion = market_cap / 1e8 if market_cap > 1e8 else market_cap
        
        return {
            'symbol': symbol,
            'market_cap': market_cap,
            'market_cap_billion': round(market_cap_billion, 2),
            'circulating_cap': raw_data.get('circulating_cap', market_cap),
            'source': raw_data.get('source', 'unknown'),
            'category': self._categorize_market_cap(market_cap_billion),
            'filter_score': self.calculate_filter_score(market_cap_billion)
        }
    
    def _categorize_market_cap(self, cap_billion: float) -> str:
        """市值分类"""
        if cap_billion < 20:
            return '微盘股'
        elif 20 <= cap_billion < 50:
            return '小盘股'
        elif 50 <= cap_billion < 200:
            return '中盘股'
        elif 200 <= cap_billion < 1000:
            return '大盘股'
        else:
            return '超大盘股'
    
    def calculate_filter_score(self, market_cap_billion: float) -> float:
        """
        计算市值筛选评分
        
        Args:
            market_cap_billion: 市值（亿元）
            
        Returns:
            评分 (0-1)
        """
        if not market_cap_billion or market_cap_billion <= 0:
            return 0.2
        
        # 核心算法：40-200亿为目标区间
        target_min = self.params['mktcap_min'] / 1e8
        target_max = self.params['mktcap_max'] / 1e8
        optimal_min = self.params['preferred_range'][0] / 1e8
        optimal_max = self.params['preferred_range'][1] / 1e8
        
        if optimal_min <= market_cap_billion <= optimal_max:
            # 最佳区间：60-150亿
            return 1.0
        elif target_min <= market_cap_billion <= target_max:
            # 目标区间：40-200亿
            if market_cap_billion < optimal_min:
                # 40-60亿：线性递增
                return 0.75 + 0.25 * (market_cap_billion - target_min) / (optimal_min - target_min)
            else:
                # 150-200亿：线性递减
                return 1.0 - 0.15 * (market_cap_billion - optimal_max) / (target_max - optimal_max)
        elif 20 <= market_cap_billion < target_min:
            # 小盘股：20-40亿
            return 0.5 + 0.25 * (market_cap_billion - 20) / (target_min - 20)
        elif target_max < market_cap_billion <= 500:
            # 中大盘股：200-500亿
            return 0.6 - 0.35 * (market_cap_billion - target_max) / (500 - target_max)
        elif market_cap_billion > 500:
            # 大盘股：>500亿
            return max(0.1, 0.25 - 0.15 * min((market_cap_billion - 500) / 500, 1))
        else:
            # 微盘股：<20亿
            return 0.1
    
    def filter_stocks(self, stock_list: List[str], strict_mode: bool = False) -> List[Dict]:
        """
        批量筛选股票
        
        Args:
            stock_list: 股票代码列表
            strict_mode: 严格模式（只返回目标区间40-200亿的股票）
            
        Returns:
            筛选结果列表
        """
        results = []
        
        for symbol in stock_list:
            try:
                cap_info = self.get_market_cap(symbol)
                market_cap_billion = cap_info.get('market_cap_billion', 0)
                
                # 筛选逻辑
                if strict_mode:
                    # 严格模式：只要40-200亿
                    if 40 <= market_cap_billion <= 200:
                        results.append(cap_info)
                else:
                    # 宽松模式：排除过小(<20亿)和过大(>1000亿)
                    if 20 <= market_cap_billion <= 1000:
                        results.append(cap_info)
                        
            except Exception as e:
                self.logger.warning(f"处理股票 {symbol} 失败: {e}")
                continue
        
        # 按市值筛选评分排序
        results.sort(key=lambda x: x['filter_score'], reverse=True)
        return results
    
    def analyze_portfolio_market_cap(self, portfolio: List[Dict]) -> Dict:
        """
        分析投资组合的市值分布
        
        Args:
            portfolio: 投资组合，每个股票包含market_cap_billion字段
            
        Returns:
            市值分析报告
        """
        if not portfolio:
            return {'error': '投资组合为空'}
        
        market_caps = [stock.get('market_cap_billion', 0) for stock in portfolio]
        market_caps = [cap for cap in market_caps if cap > 0]
        
        if not market_caps:
            return {'error': '无有效市值数据'}
        
        # 分类统计
        categories = {
            '微盘股(<20亿)': len([cap for cap in market_caps if cap < 20]),
            '小盘股(20-50亿)': len([cap for cap in market_caps if 20 <= cap < 50]),
            '中盘股(50-200亿)': len([cap for cap in market_caps if 50 <= cap < 200]),
            '大盘股(200-1000亿)': len([cap for cap in market_caps if 200 <= cap < 1000]),
            '超大盘股(>1000亿)': len([cap for cap in market_caps if cap >= 1000]),
        }
        
        # 目标区间统计
        target_range_count = len([cap for cap in market_caps if 40 <= cap <= 200])
        optimal_range_count = len([cap for cap in market_caps if 60 <= cap <= 150])
        
        return {
            'total_stocks': len(market_caps),
            'avg_market_cap': round(sum(market_caps) / len(market_caps), 2),
            'median_market_cap': round(sorted(market_caps)[len(market_caps)//2], 2),
            'target_range_count': target_range_count,
            'target_range_ratio': round(target_range_count / len(market_caps), 3),
            'optimal_range_count': optimal_range_count,
            'optimal_range_ratio': round(optimal_range_count / len(market_caps), 3),
            'categories': categories,
            'recommendation': self._generate_portfolio_recommendation(categories, len(market_caps))
        }
    
    def _generate_portfolio_recommendation(self, categories: Dict, total: int) -> str:
        """生成投资组合建议"""
        target_ratio = (categories.get('小盘股(20-50亿)', 0) + categories.get('中盘股(50-200亿)', 0)) / total
        
        if target_ratio >= 0.8:
            return "✅ 投资组合市值配置优秀，符合中小盘偏好"
        elif target_ratio >= 0.6:
            return "✅ 投资组合市值配置良好，建议适当增加中小盘股比例"
        elif target_ratio >= 0.4:
            return "⚠️ 投资组合市值配置一般，建议重点关注40-200亿市值股票"
        else:
            return "❌ 投资组合市值配置不佳，过度偏向大盘股或微盘股"

def demo_usage():
    """演示使用方法"""
    # 创建筛选器
    filter_tool = MarketCapFilter()
    
    # 测试股票列表
    test_symbols = [
        'sh.600036',  # 招商银行 (大盘股)
        'sz.000858',  # 五粮液 (大盘股)  
        'sz.002460',  # 赣锋锂业 (中盘股)
        'sz.300750',  # 宁德时代 (大盘股)
        'sz.002812',  # 恩捷股份 (中盘股)
        'sz.300782',  # 卓胜微 (小盘股)
    ]
    
    print("=== CChanTrader-AI 市值筛选工具演示 ===")
    print()
    
    # 1. 单个股票市值查询
    print("1. 单股票市值查询:")
    for symbol in test_symbols[:3]:
        cap_info = filter_tool.get_market_cap(symbol)
        print(f"  {symbol}: {cap_info['market_cap_billion']}亿元 ({cap_info['category']}) "
              f"- 评分: {cap_info['filter_score']:.3f}")
    print()
    
    # 2. 批量筛选（严格模式）
    print("2. 批量筛选 (严格模式: 40-200亿):")
    strict_results = filter_tool.filter_stocks(test_symbols, strict_mode=True)
    for stock in strict_results:
        print(f"  ✅ {stock['symbol']}: {stock['market_cap_billion']}亿元 "
              f"({stock['category']}) - 评分: {stock['filter_score']:.3f}")
    print()
    
    # 3. 批量筛选（宽松模式）
    print("3. 批量筛选 (宽松模式: 20-1000亿):")
    loose_results = filter_tool.filter_stocks(test_symbols, strict_mode=False)
    for stock in loose_results:
        print(f"  {'✅' if 40 <= stock['market_cap_billion'] <= 200 else '⚠️'} "
              f"{stock['symbol']}: {stock['market_cap_billion']}亿元 "
              f"({stock['category']}) - 评分: {stock['filter_score']:.3f}")
    print()
    
    # 4. 投资组合分析
    print("4. 投资组合市值分析:")
    portfolio_analysis = filter_tool.analyze_portfolio_market_cap(loose_results)
    print(f"  总股票数: {portfolio_analysis['total_stocks']}")
    print(f"  平均市值: {portfolio_analysis['avg_market_cap']}亿元")
    print(f"  目标区间(40-200亿)占比: {portfolio_analysis['target_range_ratio']*100:.1f}%")
    print(f"  最佳区间(60-150亿)占比: {portfolio_analysis['optimal_range_ratio']*100:.1f}%")
    print(f"  建议: {portfolio_analysis['recommendation']}")
    print()
    
    print("=== 优化建议 ===")
    print("1. 市值筛选策略:")
    print("   - 核心目标: 40-200亿中小盘股")
    print("   - 最佳区间: 60-150亿")
    print("   - 可接受范围: 20-500亿")
    print()
    print("2. 与短线交易结合:")
    print("   - 中小盘股波动性更大，适合短线操作")
    print("   - 流动性充足，进出相对容易")
    print("   - 避免微盘股风险和大盘股弹性不足")
    print()
    print("3. 风险控制:")
    print("   - 定期检查持仓市值分布")
    print("   - 根据市场环境调整市值偏好")
    print("   - 结合技术面和基本面综合筛选")

if __name__ == "__main__":
    demo_usage()