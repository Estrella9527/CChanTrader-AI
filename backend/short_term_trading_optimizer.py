#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 短线交易优化器 (2-5天操作周期)
专门针对短线交易策略的选股算法优化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests
import re

class ShortTermTradingOptimizer:
    """短线交易优化器"""
    
    def __init__(self):
        self.short_term_params = {
            # 技术指标参数（适合短线）
            'rsi_period': 7,           # RSI周期缩短到7天
            'ma_short': 3,             # 短期均线3天
            'ma_medium': 5,            # 中期均线5天  
            'volume_period': 3,        # 成交量对比周期3天
            
            # 筛选条件 (调整以包含低价股)
            'min_price': 2.0,          # 最低价格2元（包含低价股机会）
            'max_price': 300.0,        # 最高价格300元
            'min_volume_ratio': 1.5,   # 最低成交量比1.5倍
            'min_price_change': 1.0,   # 最近3天涨幅至少1%
            
            # 市值筛选（专注中小盘股）
            'mktcap_min': 40e8,        # 最小市值40亿元
            'mktcap_max': 200e8,       # 最大市值200亿元
            'mktcap_preference': 'small_mid_cap',  # 偏好中小盘
            
            # 短线特有条件
            'max_rsi': 75,             # RSI不超过75（避免超买）
            'min_rsi': 25,             # RSI不低于25（避免超卖）
            'min_auction_ratio': 0.5,  # 集合竞价比率至少0.5%
            
            # 行业过滤（排除低波动行业）
            'excluded_sectors': [
                '银行', '保险', '房地产', '公用事业', 
                '钢铁', '煤炭', '石化'
            ],
            
            # 重点关注行业（高波动性）
            'preferred_sectors': [
                '新能源', '芯片', '医药', '消费电子', 
                '软件', '人工智能', '新材料', '白酒'
            ]
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_market_cap(self, symbol: str) -> float:
        """
        获取股票市值（亿元）
        
        Args:
            symbol: 股票代码
            
        Returns:
            市值（亿元），失败返回0
        """
        try:
            # 清理股票代码格式
            clean_symbol = symbol.replace('sh.', '').replace('sz.', '')
            
            # 多数据源尝试获取市值
            sources = [
                self._get_mktcap_from_sina,
                self._get_mktcap_from_eastmoney,
                self._get_mktcap_fallback
            ]
            
            for source_func in sources:
                try:
                    market_cap = source_func(clean_symbol)
                    if market_cap and market_cap > 0:
                        return market_cap / 1e8  # 转换为亿元
                except Exception as e:
                    self.logger.debug(f"数据源获取失败 {source_func.__name__}: {e}")
                    continue
            
            # 如果所有数据源都失败，返回模拟值（基于股价和行业）
            return self._estimate_market_cap(symbol)
            
        except Exception as e:
            self.logger.warning(f"获取市值失败 {symbol}: {e}")
            return 0
    
    def _get_mktcap_from_sina(self, symbol: str) -> float:
        """从新浪财经获取市值"""
        url = f"http://hq.sinajs.cn/list={symbol}"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.text
            # 解析新浪财经数据
            if 'var hq_str_' in data:
                parts = data.split('"')[1].split(',')
                if len(parts) > 20:
                    try:
                        # 估算市值：股价 * 流通股本
                        price = float(parts[3])
                        shares = float(parts[18]) if parts[18] else 0  # 流通股本
                        return price * shares * 10000 if shares > 0 else 0
                    except (ValueError, IndexError):
                        pass
        return 0
    
    def _get_mktcap_from_eastmoney(self, symbol: str) -> float:
        """从东方财富获取市值"""
        # 简化的东方财富API调用
        market_prefix = '1' if symbol.startswith('6') else '0'
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market_prefix}.{symbol}&fields=f116,f117"
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    # f116是总市值，f117是流通市值
                    market_cap = data['data'].get('f116', 0)
                    return float(market_cap) if market_cap else 0
        except Exception:
            pass
        return 0
    
    def _get_mktcap_fallback(self, symbol: str) -> float:
        """备用市值获取方法"""
        # 这里可以添加其他数据源
        return 0
    
    def _estimate_market_cap(self, symbol: str) -> float:
        """
        估算市值（当无法获取真实数据时）
        基于股票代码特征和行业平均值
        """
        clean_symbol = symbol.replace('sh.', '').replace('sz.', '')
        
        # 基于代码特征的粗略估算
        if clean_symbol.startswith('688'):  # 科创板
            return 80e8  # 平均80亿
        elif clean_symbol.startswith('300'):  # 创业板
            return 60e8  # 平均60亿
        elif clean_symbol.startswith('002'):  # 中小板
            return 100e8  # 平均100亿
        elif clean_symbol.startswith('6'):  # 沪市主板
            return 150e8  # 平均150亿
        else:  # 深市主板
            return 120e8  # 平均120亿
    
    def calculate_short_term_score(self, stock_data: dict) -> dict:
        """
        计算短线交易评分
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            评分结果字典
        """
        scores = {}
        
        # 1. 动量评分 (25%) - 短线最重要
        momentum_score = self._calculate_momentum_score(stock_data)
        
        # 2. 成交量评分 (20%) - 资金关注度
        volume_score = self._calculate_volume_score(stock_data)
        
        # 3. 技术位置评分 (18%) - 技术面强度
        technical_score = self._calculate_technical_score(stock_data)
        
        # 4. 竞价表现评分 (15%) - 开盘活跃度
        auction_score = self._calculate_auction_score(stock_data)
        
        # 5. 市值适配评分 (12%) - 中小盘偏好
        mktcap_score = self._calculate_mktcap_score(stock_data)
        
        # 6. 行业热度评分 (10%) - 板块轮动
        sector_score = self._calculate_sector_score(stock_data)
        
        # 计算总分
        total_score = (
            momentum_score * 0.25 +
            volume_score * 0.20 +
            technical_score * 0.18 +
            auction_score * 0.15 +
            mktcap_score * 0.12 +
            sector_score * 0.10
        )
        
        return {
            'total_score': total_score,
            'momentum_score': momentum_score,
            'volume_score': volume_score,
            'technical_score': technical_score,
            'auction_score': auction_score,
            'mktcap_score': mktcap_score,
            'sector_score': sector_score,
            'trade_duration': self._estimate_trade_duration(stock_data),
            'confidence_level': self._determine_confidence(total_score),
            'strategy_note': self._generate_strategy_note(stock_data, total_score),
            'market_cap_billion': stock_data.get('market_cap', 0)
        }
    
    def _calculate_momentum_score(self, data: dict) -> float:
        """计算动量评分（适合短线）"""
        try:
            # 3日涨幅
            price_change_3d = data.get('price_change_3d', 0)
            # 5日涨幅  
            price_change_5d = data.get('price_change_5d', 0)
            # RSI强度
            rsi = data.get('rsi', 50)
            
            score = 0.0
            
            # 3日涨幅评分 (0-0.4)
            if price_change_3d >= 5:
                score += 0.4
            elif price_change_3d >= 2:
                score += 0.3
            elif price_change_3d >= 1:
                score += 0.2
            elif price_change_3d >= 0:
                score += 0.1
            
            # 5日涨幅评分 (0-0.3)
            if price_change_5d >= 10:
                score += 0.3
            elif price_change_5d >= 5:
                score += 0.2
            elif price_change_5d >= 2:
                score += 0.1
            
            # RSI评分 (0-0.3) - 50-70为最佳短线区间
            if 50 <= rsi <= 70:
                score += 0.3
            elif 45 <= rsi <= 75:
                score += 0.2
            elif 40 <= rsi <= 80:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"计算动量评分失败: {e}")
            return 0.0
    
    def _calculate_volume_score(self, data: dict) -> float:
        """计算成交量评分"""
        try:
            volume_ratio = data.get('volume_ratio', 1.0)
            volume_surge = data.get('volume_surge', False)
            
            score = 0.0
            
            # 成交量比率评分
            if volume_ratio >= 3.0:
                score += 0.6  # 放巨量
            elif volume_ratio >= 2.0:
                score += 0.5  # 明显放量
            elif volume_ratio >= 1.5:
                score += 0.3  # 适度放量
            elif volume_ratio >= 1.2:
                score += 0.1  # 略有放量
            
            # 连续放量奖励
            if volume_surge:
                score += 0.2
            
            # 成交活跃度
            turnover_rate = data.get('turnover_rate', 0)
            if turnover_rate >= 8:
                score += 0.2  # 高换手率
            elif turnover_rate >= 5:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"计算成交量评分失败: {e}")
            return 0.0
    
    def _calculate_technical_score(self, data: dict) -> float:
        """计算技术位置评分"""
        try:
            # 均线排列
            ma_alignment = data.get('ma_alignment', 'bearish')
            # 突破情况
            breakout_signal = data.get('breakout_signal', False)
            # 支撑压力位
            support_level = data.get('near_support', False)
            resistance_level = data.get('near_resistance', False)
            
            score = 0.0
            
            # 均线排列评分
            if ma_alignment == 'bullish':
                score += 0.4  # 多头排列
            elif ma_alignment == 'neutral':
                score += 0.2  # 中性
            
            # 突破信号评分
            if breakout_signal:
                score += 0.3
            
            # 位置评分
            if support_level and not resistance_level:
                score += 0.2  # 在支撑位附近且远离压力位
            elif not resistance_level:
                score += 0.1  # 远离压力位
            
            # MACD状态
            macd_signal = data.get('macd_signal', 'neutral')
            if macd_signal == 'bullish':
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"计算技术评分失败: {e}")
            return 0.0
    
    def _calculate_auction_score(self, data: dict) -> float:
        """计算竞价表现评分"""
        try:
            auction_ratio = data.get('auction_ratio', 0)
            auction_volume = data.get('auction_volume_ratio', 1.0)
            
            score = 0.0
            
            # 竞价涨幅评分
            if auction_ratio >= 3:
                score += 0.6  # 强势高开
            elif auction_ratio >= 1:
                score += 0.4  # 适度高开
            elif auction_ratio >= 0.5:
                score += 0.2  # 略微高开
            elif auction_ratio >= 0:
                score += 0.1  # 平开
            else:
                score -= 0.1  # 低开扣分
            
            # 竞价成交量评分
            if auction_volume >= 2.0:
                score += 0.3  # 竞价放量
            elif auction_volume >= 1.5:
                score += 0.1
            
            return max(min(score, 1.0), 0.0)
            
        except Exception as e:
            self.logger.warning(f"计算竞价评分失败: {e}")
            return 0.0
    
    def _calculate_sector_score(self, data: dict) -> float:
        """计算行业热度评分"""
        try:
            sector = data.get('sector', '')
            concept = data.get('concept', '')
            
            score = 0.0
            
            # 优先行业加分
            for preferred in self.short_term_params['preferred_sectors']:
                if preferred in sector or preferred in concept:
                    score += 0.6
                    break
            
            # 排除行业扣分
            for excluded in self.short_term_params['excluded_sectors']:
                if excluded in sector:
                    score -= 0.8
                    break
            
            # 热点概念加分
            hot_concepts = ['ChatGPT', 'AI', '新能源', '芯片', '数字经济']
            for hot in hot_concepts:
                if hot in concept:
                    score += 0.2
                    break
            
            return max(min(score, 1.0), 0.0)
            
        except Exception as e:
            self.logger.warning(f"计算行业评分失败: {e}")
            return 0.0
    
    def _calculate_mktcap_score(self, data: dict) -> float:
        """
        计算市值适配评分
        专注于40-200亿中小盘股，这类股票短线弹性更好
        """
        try:
            symbol = data.get('symbol', '')
            market_cap = data.get('market_cap', 0)
            
            # 如果没有市值数据，尝试获取
            if not market_cap and symbol:
                market_cap = self.get_market_cap(symbol)
                data['market_cap'] = market_cap  # 缓存结果
            
            if not market_cap:
                return 0.2  # 无数据时给予基础分
            
            # 市值区间评分（亿元）
            if 40 <= market_cap <= 200:
                # 目标区间：满分
                if 60 <= market_cap <= 150:
                    score = 1.0  # 最佳区间
                else:
                    score = 0.8  # 良好区间
            elif 20 <= market_cap < 40:
                # 微盘股：有风险但短线弹性大
                score = 0.6
            elif 200 < market_cap <= 500:
                # 中大盘股：流动性好但弹性一般
                score = 0.4
            elif market_cap > 500:
                # 大盘股：流动性好但短线机会少
                score = 0.2
            else:
                # 超微盘股：风险过大
                score = 0.1
            
            # 根据短线偏好调整
            if data.get('volume_ratio', 1) >= 2.0 and 40 <= market_cap <= 200:
                score += 0.1  # 中小盘股放量时额外加分
            
            # 行业调整
            sector = data.get('sector', '')
            if any(preferred in sector for preferred in self.short_term_params['preferred_sectors']):
                if 40 <= market_cap <= 200:
                    score += 0.05  # 热门行业中小盘股额外加分
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"计算市值评分失败: {e}")
            return 0.0
    
    def _estimate_trade_duration(self, data: dict) -> str:
        """估算交易周期"""
        momentum_score = self._calculate_momentum_score(data)
        volume_score = self._calculate_volume_score(data)
        
        if momentum_score >= 0.8 and volume_score >= 0.8:
            return "2-3天"  # 强势股，快进快出
        elif momentum_score >= 0.6:
            return "3-4天"  # 中等强势
        else:
            return "4-5天"  # 较弱，需要更长时间
    
    def _determine_confidence(self, total_score: float) -> str:
        """确定信心等级"""
        if total_score >= 0.8:
            return "very_high"
        elif total_score >= 0.65:
            return "high"
        elif total_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _generate_strategy_note(self, data: dict, score: float) -> str:
        """生成策略说明"""
        notes = []
        
        # 基于评分生成建议
        if score >= 0.8:
            notes.append("强势短线机会")
        elif score >= 0.65:
            notes.append("适合短线操作")
        else:
            notes.append("短线谨慎观察")
        
        # 基于技术面
        if data.get('breakout_signal'):
            notes.append("突破信号")
        
        # 基于成交量
        if data.get('volume_ratio', 1) >= 2:
            notes.append("放量上涨")
        
        # 基于竞价
        auction_ratio = data.get('auction_ratio', 0)
        if auction_ratio >= 2:
            notes.append("强势高开")
        elif auction_ratio >= 1:
            notes.append("适度高开")
        
        # 交易周期建议
        duration = self._estimate_trade_duration(data)
        notes.append(f"建议持仓{duration}")
        
        return "+".join(notes)
    
    def filter_short_term_candidates(self, stock_list: list) -> list:
        """筛选适合短线交易的股票"""
        filtered_stocks = []
        
        for stock in stock_list:
            # 价格筛选
            price = stock.get('current_price', 0)
            if not (self.short_term_params['min_price'] <= price <= self.short_term_params['max_price']):
                continue
            
            # 成交量筛选
            volume_ratio = stock.get('volume_ratio', 0)
            if volume_ratio < self.short_term_params['min_volume_ratio']:
                continue
            
            # RSI筛选
            rsi = stock.get('rsi', 50)
            if not (self.short_term_params['min_rsi'] <= rsi <= self.short_term_params['max_rsi']):
                continue
            
            # 竞价表现筛选
            auction_ratio = stock.get('auction_ratio', 0)
            if auction_ratio < self.short_term_params['min_auction_ratio']:
                continue
            
            # 行业筛选
            sector = stock.get('sector', '')
            if any(excluded in sector for excluded in self.short_term_params['excluded_sectors']):
                continue
            
            # 市值筛选（核心功能）
            symbol = stock.get('symbol', '')
            market_cap = stock.get('market_cap', 0)
            
            # 获取市值（如果没有的话）
            if not market_cap and symbol:
                market_cap = self.get_market_cap(symbol)
                stock['market_cap'] = market_cap
            
            # 严格的市值筛选：优先40-200亿区间
            if market_cap > 0:
                mktcap_billion = market_cap / 1e8 if market_cap > 1e8 else market_cap
                
                # 核心筛选：40-200亿范围
                if not (self.short_term_params['mktcap_min']/1e8 <= mktcap_billion <= self.short_term_params['mktcap_max']/1e8):
                    # 如果不在目标范围内，可以放宽到20-500亿，但会降低评分
                    if not (20 <= mktcap_billion <= 500):
                        continue  # 完全排除过小或过大的
                
                stock['market_cap'] = mktcap_billion  # 标准化为亿元
            
            # 计算短线评分
            score_result = self.calculate_short_term_score(stock)
            
            # 只保留评分>=0.5的股票
            if score_result['total_score'] >= 0.5:
                stock.update(score_result)
                filtered_stocks.append(stock)
        
        # 按评分排序，市值适配性也会影响总分
        filtered_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 分层返回：优先返回目标市值区间的股票
        target_range_stocks = [s for s in filtered_stocks 
                              if 40 <= s.get('market_cap', 0) <= 200]
        other_stocks = [s for s in filtered_stocks 
                       if s not in target_range_stocks]
        
        # 优先返回目标区间股票，不足时补充其他
        result = target_range_stocks[:8] + other_stocks[:2]
        
        return result[:10]  # 返回前10只

if __name__ == "__main__":
    # 测试短线优化器
    optimizer = ShortTermTradingOptimizer()
    
    # 示例股票数据（包含市值）
    test_stock = {
        'symbol': '300750',
        'stock_name': '宁德时代',
        'current_price': 189.50,
        'price_change_3d': 3.2,
        'price_change_5d': 7.8,
        'rsi': 58.6,
        'volume_ratio': 2.1,
        'volume_surge': True,
        'turnover_rate': 6.8,
        'ma_alignment': 'bullish',
        'breakout_signal': True,
        'auction_ratio': 3.2,
        'auction_volume_ratio': 1.8,
        'sector': '新能源',
        'concept': '锂电池+新能源汽车',
        'market_cap': 850  # 850亿元（大盘股示例）
    }
    
    result = optimizer.calculate_short_term_score(test_stock)
    print("短线交易评分结果:")
    for key, value in result.items():
        print(f"{key}: {value}")