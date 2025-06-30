#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 集合竞价指标设计
为现有算法添加竞价数据分析，提高选股精确度
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

class AuctionIndicators:
    """集合竞价指标计算器"""
    
    def __init__(self):
        self.auction_features = {}
    
    def get_auction_data(self, symbol: str, date: str = None) -> pd.DataFrame:
        """获取集合竞价数据"""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取集合竞价数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00", 
                end_time="09:30:00"
            )
            
            if pre_market_df.empty:
                return pd.DataFrame()
            
            # 筛选集合竞价时间段 (9:15-9:25)
            auction_df = pre_market_df[
                pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]')
            ].copy()
            
            return auction_df
            
        except Exception as e:
            print(f"获取{symbol}竞价数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_auction_indicators(self, symbol: str, auction_df: pd.DataFrame, 
                                   prev_close: float) -> dict:
        """计算集合竞价核心指标"""
        if auction_df.empty:
            return self._get_default_indicators()
        
        try:
            # 基础数据
            final_auction_price = float(auction_df.iloc[-1]['开盘'])  # 9:25的竞价价格
            auction_volume = auction_df['成交量'].sum()  # 总竞价成交量
            auction_amount = auction_df['成交额'].sum()  # 总竞价成交额
            
            # 1. 竞价比率 (相对于前一日收盘价)
            auction_ratio = (final_auction_price - prev_close) / prev_close * 100
            
            # 2. 竞价强度分析
            high_price = auction_df['最高'].max()
            low_price = auction_df['最低'].min()
            price_volatility = (high_price - low_price) / prev_close * 100
            
            # 3. 资金流向分析 (基于成交量分布)
            early_phase = auction_df[auction_df['时间'].str.contains('09:1[5-9]')]  # 9:15-9:19
            late_phase = auction_df[auction_df['时间'].str.contains('09:2[0-5]')]   # 9:20-9:25
            
            early_volume = early_phase['成交量'].sum()
            late_volume = late_phase['成交量'].sum()
            
            # 资金流向偏好 (后期成交占比越高，说明资金越坚决)
            capital_flow_bias = late_volume / (early_volume + late_volume + 1e-10)
            
            # 4. 开盘缺口分析
            gap_type = self._analyze_gap(final_auction_price, prev_close)
            
            # 5. 竞价活跃度
            auction_activity = auction_volume / (auction_df.shape[0] + 1e-10)  # 平均每分钟成交量
            
            # 6. 价格一致性 (竞价期间价格稳定性)
            price_consistency = 1 - (auction_df['最高'].std() / auction_df['最高'].mean())
            
            # 7. 竞价趋势方向
            price_trend = self._calculate_price_trend(auction_df)
            
            # 8. 综合竞价信号强度
            signal_strength = self._calculate_signal_strength(
                auction_ratio, price_volatility, capital_flow_bias, 
                auction_activity, price_consistency
            )
            
            return {
                'symbol': symbol,
                'auction_price': final_auction_price,
                'prev_close': prev_close,
                'auction_ratio': round(auction_ratio, 2),
                'auction_volume': auction_volume,
                'auction_amount': auction_amount,
                'price_volatility': round(price_volatility, 2),
                'capital_flow_bias': round(capital_flow_bias, 3),
                'gap_type': gap_type,
                'auction_activity': round(auction_activity, 2),
                'price_consistency': round(price_consistency, 3),
                'price_trend': price_trend,
                'signal_strength': round(signal_strength, 3),
                'bullish_signals': self._count_bullish_signals(
                    auction_ratio, capital_flow_bias, price_consistency, price_trend
                ),
                'risk_signals': self._count_risk_signals(
                    price_volatility, auction_volume
                )
            }
            
        except Exception as e:
            print(f"计算{symbol}竞价指标失败: {e}")
            return self._get_default_indicators()
    
    def _analyze_gap(self, auction_price: float, prev_close: float) -> str:
        """分析开盘缺口类型"""
        gap_ratio = (auction_price - prev_close) / prev_close
        
        if gap_ratio > 0.03:
            return "high_gap_up"      # 高开缺口 (>3%)
        elif gap_ratio > 0.01:
            return "gap_up"           # 普通高开 (1-3%)
        elif gap_ratio > -0.01:
            return "flat_open"        # 平开 (-1% ~ +1%)
        elif gap_ratio > -0.03:
            return "gap_down"         # 普通低开 (-3% ~ -1%)
        else:
            return "low_gap_down"     # 低开缺口 (<-3%)
    
    def _calculate_price_trend(self, auction_df: pd.DataFrame) -> str:
        """计算竞价期间价格趋势"""
        if len(auction_df) < 3:
            return "insufficient_data"
        
        prices = auction_df['开盘'].values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        if slope > prices[0] * 0.001:  # 斜率>0.1%
            return "rising"
        elif slope < -prices[0] * 0.001:  # 斜率<-0.1%
            return "falling"
        else:
            return "stable"
    
    def _calculate_signal_strength(self, auction_ratio: float, price_volatility: float,
                                 capital_flow_bias: float, auction_activity: float,
                                 price_consistency: float) -> float:
        """计算综合竞价信号强度 (0-1)"""
        strength = 0.5  # 基础分
        
        # 竞价比率贡献 (25%)
        if 0 < auction_ratio <= 3:
            strength += 0.25 * (auction_ratio / 3)
        elif 3 < auction_ratio <= 6:
            strength += 0.25 * (1 - (auction_ratio - 3) / 3)  # 过高反而扣分
        
        # 资金流向贡献 (25%)
        strength += 0.25 * capital_flow_bias
        
        # 价格一致性贡献 (20%)
        strength += 0.20 * price_consistency
        
        # 活跃度贡献 (15%)
        if auction_activity > 0:
            activity_score = min(auction_activity / 1000, 1.0)  # 标准化
            strength += 0.15 * activity_score
        
        # 波动率惩罚 (15%)
        if price_volatility > 5:  # 波动过大扣分
            strength -= 0.15 * min((price_volatility - 5) / 10, 1.0)
        
        return max(0, min(1, strength))
    
    def _count_bullish_signals(self, auction_ratio: float, capital_flow_bias: float,
                             price_consistency: float, price_trend: str) -> int:
        """统计看涨信号数量"""
        signals = 0
        
        if auction_ratio > 0.5:  # 温和高开
            signals += 1
        if capital_flow_bias > 0.6:  # 后期资金坚决
            signals += 1
        if price_consistency > 0.8:  # 价格稳定
            signals += 1
        if price_trend == "rising":  # 竞价期间上升
            signals += 1
        
        return signals
    
    def _count_risk_signals(self, price_volatility: float, auction_volume: float) -> int:
        """统计风险信号数量"""
        signals = 0
        
        if price_volatility > 8:  # 波动过大
            signals += 1
        if auction_volume == 0:  # 无成交量
            signals += 1
        
        return signals
    
    def _get_default_indicators(self) -> dict:
        """获取默认指标值"""
        return {
            'symbol': '',
            'auction_price': 0,
            'prev_close': 0,
            'auction_ratio': 0,
            'auction_volume': 0,
            'auction_amount': 0,
            'price_volatility': 0,
            'capital_flow_bias': 0,
            'gap_type': 'no_data',
            'auction_activity': 0,
            'price_consistency': 0,
            'price_trend': 'no_data',
            'signal_strength': 0,
            'bullish_signals': 0,
            'risk_signals': 1
        }

class EnhancedStockAnalyzer:
    """增强版股票分析器 (整合竞价数据)"""
    
    def __init__(self):
        self.auction_analyzer = AuctionIndicators()
    
    def comprehensive_analysis_with_auction(self, symbol: str, df: pd.DataFrame) -> dict:
        """结合竞价数据的综合分析"""
        try:
            if len(df) < 30:
                return None
            
            current_price = float(df['close'].iloc[-1])
            prev_close = float(df['close'].iloc[-2])
            
            # 获取竞价数据分析
            auction_df = self.auction_analyzer.get_auction_data(symbol)
            auction_indicators = self.auction_analyzer.calculate_auction_indicators(
                symbol, auction_df, prev_close
            )
            
            # 原有技术分析 (简化版)
            latest = df.iloc[-1]
            
            # 技术指标基础分析
            tech_score = self._calculate_tech_score(df, latest)
            
            # 竞价分析权重
            auction_score = auction_indicators['signal_strength']
            bullish_signals = auction_indicators['bullish_signals']
            risk_signals = auction_indicators['risk_signals']
            
            # 综合评分 = 技术分析70% + 竞价分析30%
            total_score = tech_score * 0.7 + auction_score * 0.3
            
            # 竞价增强调整
            if bullish_signals >= 3:
                total_score += 0.1  # 强烈看涨信号加分
            if risk_signals >= 2:
                total_score -= 0.2  # 高风险信号扣分
            
            # 筛选条件
            if total_score < 0.65:
                return None
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'total_score': round(total_score, 3),
                'tech_score': round(tech_score, 3),
                'auction_score': round(auction_score, 3),
                
                # 竞价数据
                'auction_ratio': auction_indicators['auction_ratio'],
                'gap_type': auction_indicators['gap_type'],
                'capital_flow_bias': auction_indicators['capital_flow_bias'],
                'price_trend': auction_indicators['price_trend'],
                'bullish_signals': bullish_signals,
                'risk_signals': risk_signals,
                
                # 交易建议
                'entry_price': current_price,
                'stop_loss': round(current_price * 0.92, 2),
                'target_price': round(current_price * 1.15, 2),
                'confidence': 'high' if total_score > 0.8 else 'medium',
                
                # 竞价策略建议
                'auction_strategy': self._generate_auction_strategy(auction_indicators)
            }
            
        except Exception as e:
            print(f"分析{symbol}失败: {e}")
            return None
    
    def _calculate_tech_score(self, df: pd.DataFrame, latest: pd.Series) -> float:
        """计算技术分析得分"""
        score = 0.5
        
        # 简化的技术指标评分
        try:
            # 均线排列
            if len(df) >= 20:
                ma5 = df['close'].rolling(5).mean().iloc[-1]
                ma10 = df['close'].rolling(10).mean().iloc[-1]
                ma20 = df['close'].rolling(20).mean().iloc[-1]
                
                if latest['close'] > ma5 > ma10 > ma20:
                    score += 0.3
                elif latest['close'] > ma5 > ma10:
                    score += 0.2
            
            # RSI
            if len(df) >= 15:
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / (loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                if 30 <= current_rsi <= 70:
                    score += 0.15
            
            # 成交量
            if len(df) >= 10:
                vol_ma = df['volume'].rolling(10).mean().iloc[-1]
                if latest['volume'] > vol_ma * 0.8:
                    score += 0.05
        
        except Exception:
            pass
        
        return min(1.0, score)
    
    def _generate_auction_strategy(self, auction_indicators: dict) -> str:
        """生成竞价策略建议"""
        gap_type = auction_indicators['gap_type']
        auction_ratio = auction_indicators['auction_ratio']
        bullish_signals = auction_indicators['bullish_signals']
        
        if gap_type == "high_gap_up":
            return "高开缺口，建议谨慎，等待回踩确认"
        elif gap_type == "gap_up" and bullish_signals >= 2:
            return "温和高开+多信号确认，可考虑开盘买入"
        elif gap_type == "flat_open" and bullish_signals >= 3:
            return "平开强势，竞价信号良好，推荐买入"
        elif gap_type == "gap_down" and auction_ratio > -2:
            return "低开幅度可控，可等待反弹机会"
        else:
            return "竞价信号一般，建议观望"

# 使用示例
if __name__ == "__main__":
    # 竞价指标测试
    auction_analyzer = AuctionIndicators()
    
    # 测试单只股票
    test_symbol = "000001"
    print(f"=== {test_symbol} 集合竞价分析 ===")
    
    auction_df = auction_analyzer.get_auction_data(test_symbol)
    if not auction_df.empty:
        print(f"获取到 {len(auction_df)} 条竞价数据")
        
        # 模拟前一日收盘价
        prev_close = 12.50
        indicators = auction_analyzer.calculate_auction_indicators(
            test_symbol, auction_df, prev_close
        )
        
        print(f"竞价价格: {indicators['auction_price']}")
        print(f"竞价比率: {indicators['auction_ratio']}%")
        print(f"缺口类型: {indicators['gap_type']}")
        print(f"信号强度: {indicators['signal_strength']}")
        print(f"看涨信号: {indicators['bullish_signals']}")
        print(f"风险信号: {indicators['risk_signals']}")
    else:
        print("暂无竞价数据")