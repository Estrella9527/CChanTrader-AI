#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 高级版本
- 精准缠论算法升级
- 多因子融合系统
- 实盘验证测试框架
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 高级参数配置
# ============================================================================

ADVANCED_PARAMS = {
    # 缠论核心参数
    "chan": {
        "min_segment_bars": 5,      # 最小线段K线数
        "pivot_confirm_bars": 3,    # 中枢确认K线数
        "breakout_threshold": 0.02, # 突破阈值2%
        "pivot_strength_min": 0.05, # 中枢强度最小值5%
    },
    
    # 技术指标参数
    "technical": {
        "ma_periods": [5, 10, 20, 34, 55],
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "vol_period": 20,
    },
    
    # 多因子权重
    "factors": {
        "technical_weight": 0.4,    # 技术面权重
        "volume_weight": 0.25,      # 量能权重
        "momentum_weight": 0.2,     # 动量权重
        "volatility_weight": 0.15,  # 波动率权重
    },
    
    # 选股阈值
    "selection": {
        "min_score": 0.6,           # 最低综合评分
        "max_volatility": 0.8,      # 最大波动率
        "min_liquidity": 1000000,   # 最小流动性(成交额)
        "price_range": [3, 300],    # 价格范围
    },
    
    # 风控参数
    "risk": {
        "max_single_risk": 0.02,    # 单笔最大风险
        "max_total_risk": 0.08,     # 总体最大风险
        "stop_loss_pct": 0.08,      # 止损比例
        "take_profit_ratio": 3,     # 止盈比例(风报比)
    }
}

# ============================================================================
# 高级数据结构
# ============================================================================

@dataclass
class AdvancedSegment:
    """高级线段结构"""
    start_idx: int
    end_idx: int
    direction: str          # 'up' | 'down'
    start_price: float
    end_price: float
    high: float
    low: float
    strength: float         # 线段强度
    volume_profile: float   # 成交量分布
    duration: int           # 持续时间

@dataclass
class AdvancedPivot:
    """高级中枢结构"""
    start_idx: int
    end_idx: int
    high: float
    low: float
    center: float
    strength: float         # 中枢强度
    volume_density: float   # 成交量密度
    breakout_probability: float  # 突破概率
    direction_bias: str     # 方向偏向

@dataclass
class MultiFactorScore:
    """多因子评分"""
    technical_score: float      # 技术面评分
    volume_score: float         # 量能评分
    momentum_score: float       # 动量评分
    volatility_score: float     # 波动率评分
    total_score: float          # 综合评分
    risk_score: float           # 风险评分

# ============================================================================
# 1. 高级缠论算法实现
# ============================================================================

class AdvancedChanAnalyzer:
    """高级缠论分析器"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = self._preprocess_data(df)
        self.segments = []
        self.pivots = []
        
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        df = df.copy()
        
        # 数据类型转换
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 过滤无效数据
        df = df.dropna(subset=['high', 'low', 'close'])
        df = df[(df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
        
        # 计算技术指标
        df = self._add_technical_indicators(df)
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        # 移动平均线
        for period in ADVANCED_PARAMS["technical"]["ma_periods"]:
            if len(df) >= period:
                df[f'ma{period}'] = df['close'].rolling(period).mean()
        
        # RSI
        if len(df) >= ADVANCED_PARAMS["technical"]["rsi_period"] + 1:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(ADVANCED_PARAMS["technical"]["rsi_period"]).mean()
            loss = -delta.where(delta < 0, 0).rolling(ADVANCED_PARAMS["technical"]["rsi_period"]).mean()
            rs = gain / (loss + 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
        else:
            df['rsi'] = 50
            
        # MACD
        if len(df) >= ADVANCED_PARAMS["technical"]["macd_slow"]:
            ema12 = df['close'].ewm(span=ADVANCED_PARAMS["technical"]["macd_fast"]).mean()
            ema26 = df['close'].ewm(span=ADVANCED_PARAMS["technical"]["macd_slow"]).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=ADVANCED_PARAMS["technical"]["macd_signal"]).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 成交量指标
        if len(df) >= ADVANCED_PARAMS["technical"]["vol_period"]:
            df['vol_ma'] = df['volume'].rolling(ADVANCED_PARAMS["technical"]["vol_period"]).mean()
            df['vol_ratio'] = df['volume'] / df['vol_ma']
        
        return df
    
    def identify_fractal_points(self) -> Tuple[List[int], List[int]]:
        """识别分型点（高点和低点）"""
        highs, lows = [], []
        
        for i in range(2, len(self.df) - 2):
            # 顶分型：前后两K线的高点都小于当前K线
            if (self.df['high'].iloc[i] > self.df['high'].iloc[i-1] and
                self.df['high'].iloc[i] > self.df['high'].iloc[i+1] and
                self.df['high'].iloc[i] > self.df['high'].iloc[i-2] and
                self.df['high'].iloc[i] > self.df['high'].iloc[i+2]):
                highs.append(i)
            
            # 底分型：前后两K线的低点都大于当前K线
            if (self.df['low'].iloc[i] < self.df['low'].iloc[i-1] and
                self.df['low'].iloc[i] < self.df['low'].iloc[i+1] and
                self.df['low'].iloc[i] < self.df['low'].iloc[i-2] and
                self.df['low'].iloc[i] < self.df['low'].iloc[i+2]):
                lows.append(i)
        
        return highs, lows
    
    def identify_segments(self) -> List[AdvancedSegment]:
        """识别线段"""
        highs, lows = self.identify_fractal_points()
        
        # 合并所有极值点
        all_points = []
        for h in highs:
            all_points.append((h, self.df['high'].iloc[h], 'high'))
        for l in lows:
            all_points.append((l, self.df['low'].iloc[l], 'low'))
        
        # 按时间排序
        all_points.sort(key=lambda x: x[0])
        
        segments = []
        for i in range(len(all_points) - 1):
            start_idx, start_price, start_type = all_points[i]
            end_idx, end_price, end_type = all_points[i + 1]
            
            # 高低点交替才能形成线段
            if start_type != end_type:
                direction = 'up' if start_type == 'low' else 'down'
                
                # 计算线段区间的高低点
                segment_data = self.df.iloc[start_idx:end_idx+1]
                high = segment_data['high'].max()
                low = segment_data['low'].min()
                
                # 计算线段强度
                strength = abs(end_price - start_price) / start_price
                
                # 计算成交量分布
                volume_profile = segment_data['volume'].mean()
                
                # 线段长度（K线数）
                duration = end_idx - start_idx + 1
                
                # 过滤太短的线段
                if duration >= ADVANCED_PARAMS["chan"]["min_segment_bars"]:
                    segment = AdvancedSegment(
                        start_idx=start_idx,
                        end_idx=end_idx,
                        direction=direction,
                        start_price=start_price,
                        end_price=end_price,
                        high=high,
                        low=low,
                        strength=strength,
                        volume_profile=volume_profile,
                        duration=duration
                    )
                    segments.append(segment)
        
        return segments
    
    def identify_pivots(self, segments: List[AdvancedSegment]) -> List[AdvancedPivot]:
        """识别中枢"""
        pivots = []
        
        if len(segments) < 3:
            return pivots
        
        for i in range(len(segments) - 2):
            seg1, seg2, seg3 = segments[i], segments[i+1], segments[i+2]
            
            # 检查三段式中枢：上-下-上 或 下-上-下
            if (seg1.direction != seg2.direction and 
                seg2.direction != seg3.direction and
                seg1.direction == seg3.direction):
                
                # 计算中枢边界
                if seg1.direction == 'up':  # 上-下-上型中枢
                    pivot_high = min(seg1.end_price, seg3.end_price)
                    pivot_low = seg2.end_price
                else:  # 下-上-下型中枢
                    pivot_high = seg2.end_price
                    pivot_low = max(seg1.end_price, seg3.end_price)
                
                # 检查中枢有效性
                if pivot_high > pivot_low:
                    center = (pivot_high + pivot_low) / 2
                    strength = (pivot_high - pivot_low) / center
                    
                    # 过滤强度不足的中枢
                    if strength >= ADVANCED_PARAMS["chan"]["pivot_strength_min"]:
                        # 计算成交量密度
                        pivot_data = self.df.iloc[seg1.start_idx:seg3.end_idx+1]
                        volume_density = pivot_data['volume'].mean()
                        
                        # 计算突破概率（基于历史数据）
                        breakout_prob = self._calculate_breakout_probability(pivot_data)
                        
                        # 方向偏向
                        direction_bias = 'up' if seg3.strength > seg1.strength else 'down'
                        
                        pivot = AdvancedPivot(
                            start_idx=seg1.start_idx,
                            end_idx=seg3.end_idx,
                            high=pivot_high,
                            low=pivot_low,
                            center=center,
                            strength=strength,
                            volume_density=volume_density,
                            breakout_probability=breakout_prob,
                            direction_bias=direction_bias
                        )
                        pivots.append(pivot)
        
        return pivots
    
    def _calculate_breakout_probability(self, pivot_data: pd.DataFrame) -> float:
        """计算突破概率"""
        try:
            # 基于成交量和波动率的简化概率模型
            vol_ratio = pivot_data['vol_ratio'].mean() if 'vol_ratio' in pivot_data.columns else 1.0
            volatility = pivot_data['close'].pct_change().std()
            
            # 简化的概率计算
            prob = min(0.9, max(0.1, vol_ratio * 0.3 + volatility * 100 * 0.2))
            return prob
        except:
            return 0.5
    
    def analyze(self) -> Dict:
        """完整分析"""
        if len(self.df) < 10:
            return self._empty_result()
        
        # 识别线段和中枢
        self.segments = self.identify_segments()
        self.pivots = self.identify_pivots(self.segments)
        
        # 趋势判断
        trend = self._determine_trend()
        
        # 信号识别
        signals = self._identify_signals()
        
        # 量价分析
        volume_analysis = self._analyze_volume()
        
        return {
            'segments': self.segments,
            'pivots': self.pivots,
            'trend': trend,
            'signals': signals,
            'volume_analysis': volume_analysis,
            'technical_data': self.df.iloc[-1].to_dict() if not self.df.empty else {}
        }
    
    def _determine_trend(self) -> str:
        """判断趋势"""
        if not self.segments:
            return 'side'
        
        # 基于最近几个线段的高低点
        recent_segments = self.segments[-3:] if len(self.segments) >= 3 else self.segments
        
        if len(recent_segments) >= 2:
            last_high = max(seg.high for seg in recent_segments if seg.direction == 'up')
            last_low = min(seg.low for seg in recent_segments if seg.direction == 'down')
            
            current_price = self.df['close'].iloc[-1]
            
            # 结合均线趋势
            ma5 = self.df['ma5'].iloc[-1] if 'ma5' in self.df.columns else current_price
            ma20 = self.df['ma20'].iloc[-1] if 'ma20' in self.df.columns else current_price
            
            if current_price > ma5 > ma20 and current_price > last_low * 1.02:
                return 'up'
            elif current_price < ma5 < ma20 and current_price < last_high * 0.98:
                return 'down'
        
        return 'side'
    
    def _identify_signals(self) -> Dict:
        """识别买卖信号"""
        signals = {'1_buy': [], '2_buy': [], '3_buy': [], '1_sell': [], '2_sell': []}
        
        if not self.pivots:
            return signals
        
        current_price = self.df['close'].iloc[-1]
        
        # 检查最近的中枢
        for pivot in self.pivots[-2:]:
            # 二买信号：突破中枢上沿
            if current_price > pivot.high * (1 + ADVANCED_PARAMS["chan"]["breakout_threshold"]):
                signals['2_buy'].append({
                    'price': current_price,
                    'pivot_center': pivot.center,
                    'breakout_strength': (current_price - pivot.high) / pivot.high,
                    'confidence': pivot.breakout_probability
                })
            
            # 三买信号：回踩中枢后再次向上
            elif pivot.low <= current_price <= pivot.high and pivot.direction_bias == 'up':
                signals['3_buy'].append({
                    'price': current_price,
                    'pivot_center': pivot.center,
                    'support_strength': (current_price - pivot.low) / (pivot.high - pivot.low),
                    'confidence': pivot.breakout_probability * 0.8
                })
        
        return signals
    
    def _analyze_volume(self) -> Dict:
        """量价分析"""
        try:
            recent_data = self.df.iloc[-20:]  # 最近20个周期
            
            volume_trend = 'increasing' if recent_data['volume'].iloc[-5:].mean() > recent_data['volume'].iloc[-10:-5].mean() else 'decreasing'
            
            # 量价配合度
            price_change = recent_data['close'].pct_change()
            volume_change = recent_data['volume'].pct_change()
            correlation = price_change.corr(volume_change)
            
            return {
                'volume_trend': volume_trend,
                'price_volume_correlation': correlation if not pd.isna(correlation) else 0,
                'current_volume_ratio': recent_data['vol_ratio'].iloc[-1] if 'vol_ratio' in recent_data.columns else 1.0,
                'volume_surge': recent_data['volume'].iloc[-1] > recent_data['volume'].mean() * 2
            }
        except:
            return {'volume_trend': 'stable', 'price_volume_correlation': 0, 'current_volume_ratio': 1.0, 'volume_surge': False}
    
    def _empty_result(self) -> Dict:
        """空结果"""
        return {
            'segments': [],
            'pivots': [],
            'trend': 'side',
            'signals': {'1_buy': [], '2_buy': [], '3_buy': [], '1_sell': [], '2_sell': []},
            'volume_analysis': {'volume_trend': 'stable', 'price_volume_correlation': 0, 'current_volume_ratio': 1.0},
            'technical_data': {}
        }

# ============================================================================
# 2. 多因子融合系统
# ============================================================================

class MultiFactorAnalyzer:
    """多因子分析器"""
    
    def __init__(self, df: pd.DataFrame, chan_result: Dict):
        self.df = df
        self.chan_result = chan_result
        
    def calculate_technical_score(self) -> float:
        """技术面评分 (0-1)"""
        score = 0.0
        
        try:
            latest = self.df.iloc[-1]
            
            # 均线排列得分
            ma_score = 0
            if all(col in latest.index for col in ['ma5', 'ma10', 'ma20']):
                if latest['ma5'] > latest['ma10'] > latest['ma20']:
                    ma_score = 1.0
                elif latest['ma5'] > latest['ma10']:
                    ma_score = 0.6
                elif latest['close'] > latest['ma5']:
                    ma_score = 0.3
            
            # RSI得分
            rsi_score = 0
            if 'rsi' in latest.index:
                rsi = latest['rsi']
                if 30 <= rsi <= 70:
                    rsi_score = 1.0
                elif 25 <= rsi <= 75:
                    rsi_score = 0.7
                elif 20 <= rsi <= 80:
                    rsi_score = 0.4
            
            # MACD得分
            macd_score = 0
            if all(col in latest.index for col in ['macd', 'macd_signal']):
                if latest['macd'] > latest['macd_signal'] and latest['macd'] > 0:
                    macd_score = 1.0
                elif latest['macd'] > latest['macd_signal']:
                    macd_score = 0.7
            
            # 缠论信号得分
            chan_score = 0
            if self.chan_result['signals']['2_buy']:
                chan_score = 0.9
            elif self.chan_result['signals']['3_buy']:
                chan_score = 0.7
            elif self.chan_result['trend'] == 'up':
                chan_score = 0.5
            
            score = (ma_score * 0.3 + rsi_score * 0.2 + macd_score * 0.2 + chan_score * 0.3)
            
        except Exception as e:
            print(f"技术面评分计算错误: {e}")
            
        return min(1.0, max(0.0, score))
    
    def calculate_volume_score(self) -> float:
        """量能评分 (0-1)"""
        try:
            vol_analysis = self.chan_result['volume_analysis']
            
            # 成交量趋势得分
            trend_score = 1.0 if vol_analysis['volume_trend'] == 'increasing' else 0.3
            
            # 量价配合得分
            correlation = vol_analysis['price_volume_correlation']
            corr_score = max(0, correlation) if correlation > 0 else 0
            
            # 成交量放大得分
            vol_ratio = vol_analysis['current_volume_ratio']
            ratio_score = min(1.0, vol_ratio / 2.0) if vol_ratio > 1 else 0.2
            
            # 突然放量得分
            surge_score = 0.8 if vol_analysis['volume_surge'] else 0.4
            
            score = trend_score * 0.3 + corr_score * 0.3 + ratio_score * 0.2 + surge_score * 0.2
            
        except:
            score = 0.5
            
        return min(1.0, max(0.0, score))
    
    def calculate_momentum_score(self) -> float:
        """动量评分 (0-1)"""
        try:
            # 价格动量
            price_data = self.df['close'].iloc[-20:]
            returns = price_data.pct_change().dropna()
            
            # 近期收益率
            recent_return = (price_data.iloc[-1] / price_data.iloc[-10] - 1) * 100
            momentum_score = min(1.0, max(0.0, recent_return / 20 + 0.5))
            
            # 收益率稳定性
            return_std = returns.std()
            stability_score = max(0, 1 - return_std * 10)
            
            # 趋势持续性
            up_days = (returns > 0).sum()
            trend_score = up_days / len(returns)
            
            score = momentum_score * 0.5 + stability_score * 0.3 + trend_score * 0.2
            
        except:
            score = 0.5
            
        return min(1.0, max(0.0, score))
    
    def calculate_volatility_score(self) -> float:
        """波动率评分 (0-1，波动率越低分数越高)"""
        try:
            returns = self.df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            
            # 波动率评分（波动率越低越好）
            if volatility < 0.2:
                score = 1.0
            elif volatility < 0.4:
                score = 0.8
            elif volatility < 0.6:
                score = 0.6
            elif volatility < 0.8:
                score = 0.4
            else:
                score = 0.2
                
        except:
            score = 0.5
            
        return score
    
    def calculate_multi_factor_score(self) -> MultiFactorScore:
        """计算多因子综合评分"""
        technical_score = self.calculate_technical_score()
        volume_score = self.calculate_volume_score()
        momentum_score = self.calculate_momentum_score()
        volatility_score = self.calculate_volatility_score()
        
        # 加权计算总分
        weights = ADVANCED_PARAMS["factors"]
        total_score = (
            technical_score * weights["technical_weight"] +
            volume_score * weights["volume_weight"] +
            momentum_score * weights["momentum_weight"] +
            volatility_score * weights["volatility_weight"]
        )
        
        # 风险评分（波动率的倒数）
        risk_score = volatility_score
        
        return MultiFactorScore(
            technical_score=round(technical_score, 3),
            volume_score=round(volume_score, 3),
            momentum_score=round(momentum_score, 3),
            volatility_score=round(volatility_score, 3),
            total_score=round(total_score, 3),
            risk_score=round(risk_score, 3)
        )

# ============================================================================
# 3. 实盘验证系统
# ============================================================================

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, symbol: str, df: pd.DataFrame, signals: List[Dict]) -> Dict:
        """运行回测"""
        portfolio_value = self.initial_capital
        max_drawdown = 0
        max_portfolio_value = self.initial_capital
        
        for i, signal in enumerate(signals):
            if signal['action'] == 'buy':
                # 买入逻辑
                price = signal['price']
                shares = int(portfolio_value * 0.1 / price)  # 10%仓位
                
                if shares > 0:
                    cost = shares * price
                    portfolio_value -= cost
                    
                    self.positions[symbol] = {
                        'shares': shares,
                        'entry_price': price,
                        'entry_date': signal['date'],
                        'stop_loss': signal.get('stop_loss', price * 0.9)
                    }
                    
            elif signal['action'] == 'sell' and symbol in self.positions:
                # 卖出逻辑
                position = self.positions[symbol]
                price = signal['price']
                proceeds = position['shares'] * price
                portfolio_value += proceeds
                
                # 记录交易
                profit = proceeds - (position['shares'] * position['entry_price'])
                self.trades.append({
                    'symbol': symbol,
                    'entry_price': position['entry_price'],
                    'exit_price': price,
                    'shares': position['shares'],
                    'profit': profit,
                    'return_pct': profit / (position['shares'] * position['entry_price'])
                })
                
                del self.positions[symbol]
            
            # 更新组合价值
            max_portfolio_value = max(max_portfolio_value, portfolio_value)
            drawdown = (max_portfolio_value - portfolio_value) / max_portfolio_value
            max_drawdown = max(max_drawdown, drawdown)
            
            self.equity_curve.append({
                'date': signal['date'],
                'portfolio_value': portfolio_value,
                'drawdown': drawdown
            })
        
        return self._calculate_performance_metrics(max_drawdown)
    
    def _calculate_performance_metrics(self, max_drawdown: float) -> Dict:
        """计算绩效指标"""
        if not self.trades:
            return {'error': '无交易记录'}
        
        # 基本统计
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['profit'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 收益统计
        total_return = sum(t['profit'] for t in self.trades)
        total_return_pct = total_return / self.initial_capital
        
        avg_win = np.mean([t['profit'] for t in self.trades if t['profit'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['profit'] for t in self.trades if t['profit'] < 0]) if (total_trades - winning_trades) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 夏普比率
        returns = [t['return_pct'] for t in self.trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 3),
            'total_return_pct': round(total_return_pct * 100, 2),
            'max_drawdown': round(max_drawdown * 100, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2)
        }

# ============================================================================
# 4. 高级选股引擎
# ============================================================================

def advanced_stock_selection(symbol: str, df: pd.DataFrame) -> Optional[Dict]:
    """高级选股函数"""
    try:
        # 数据质量检查
        if len(df) < 60 or df['volume'].sum() == 0:
            return None
        
        # 价格范围过滤
        current_price = float(df['close'].iloc[-1])
        price_range = ADVANCED_PARAMS["selection"]["price_range"]
        if not (price_range[0] <= current_price <= price_range[1]):
            return None
        
        # 流动性过滤
        avg_amount = df['amount'].iloc[-20:].mean() if 'amount' in df.columns else 0
        if avg_amount < ADVANCED_PARAMS["selection"]["min_liquidity"]:
            return None
        
        # 缠论分析
        chan_analyzer = AdvancedChanAnalyzer(df)
        chan_result = chan_analyzer.analyze()
        
        # 多因子分析
        multi_factor = MultiFactorAnalyzer(df, chan_result)
        factor_score = multi_factor.calculate_multi_factor_score()
        
        # 综合评分过滤
        if factor_score.total_score < ADVANCED_PARAMS["selection"]["min_score"]:
            return None
        
        # 波动率过滤
        if factor_score.volatility_score < (1 - ADVANCED_PARAMS["selection"]["max_volatility"]):
            return None
        
        # 信号确认
        has_buy_signal = bool(chan_result['signals']['2_buy'] or chan_result['signals']['3_buy'])
        if not has_buy_signal:
            return None
        
        # 计算入场点和止损点
        entry_price = current_price
        
        # 基于中枢计算止损
        stop_loss = entry_price * (1 - ADVANCED_PARAMS["risk"]["stop_loss_pct"])
        if chan_result['pivots']:
            latest_pivot = chan_result['pivots'][-1]
            pivot_stop = latest_pivot.low * 0.98
            stop_loss = max(stop_loss, pivot_stop)  # 取较高的止损价
        
        # 目标价位
        risk_amount = entry_price - stop_loss
        take_profit = entry_price + risk_amount * ADVANCED_PARAMS["risk"]["take_profit_ratio"]
        
        # 信号类型
        signal_type = '2_buy' if chan_result['signals']['2_buy'] else '3_buy'
        
        return {
            'symbol': symbol,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'signal_type': signal_type,
            'technical_score': factor_score.technical_score,
            'volume_score': factor_score.volume_score,
            'momentum_score': factor_score.momentum_score,
            'volatility_score': factor_score.volatility_score,
            'total_score': factor_score.total_score,
            'risk_score': factor_score.risk_score,
            'trend': chan_result['trend'],
            'segments_count': len(chan_result['segments']),
            'pivots_count': len(chan_result['pivots']),
            'risk_reward_ratio': round((take_profit - entry_price) / (entry_price - stop_loss), 2)
        }
        
    except Exception as e:
        print(f"高级选股分析 {symbol} 错误: {e}")
        return None

# ============================================================================
# 5. 主程序
# ============================================================================

def advanced_cchan_main(test_mode: bool = True, max_stocks: int = 50):
    """高级缠论选股主程序"""
    load_dotenv()
    
    print('=== CChanTrader-AI 高级版本 ===')
    print('✨ 精准缠论算法 + 多因子融合 + 实盘验证')
    
    lg = bs.login()
    print(f'📊 BaoStock连接: {lg.error_code}')
    
    try:
        # 获取股票列表
        print('\\n🔍 获取股票列表...')
        for days_back in range(0, 10):
            query_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            stock_rs = bs.query_all_stock(query_date)
            stock_df = stock_rs.get_data()
            if not stock_df.empty:
                break
        
        # 过滤股票
        a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')]
        if test_mode:
            a_stocks = a_stocks.head(max_stocks)
        
        print(f'📋 待分析股票: {len(a_stocks)}只')
        
        # 获取K线数据
        print('\\n📈 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
        
        kline_data = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='数据获取'):
            code = stock['code']
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume,amount',
                    start_date=start_date, end_date=end_date, frequency='d')
                day_df = rs.get_data()
                
                if not day_df.empty and len(day_df) >= 60:
                    kline_data[code] = day_df
                    
            except Exception:
                continue
        
        print(f'✅ 获取数据: {len(kline_data)}只')
        
        # 高级选股分析
        print('\\n🧠 执行高级选股分析...')
        selected_stocks = []
        
        for symbol, df in tqdm(kline_data.items(), desc='智能选股'):
            result = advanced_stock_selection(symbol, df)
            if result:
                selected_stocks.append(result)
        
        # 按总分排序
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\\n🎯 === 高级选股结果 ({len(selected_stocks)}只) ===')
        
        # 显示结果
        if selected_stocks:
            for i, stock in enumerate(selected_stocks[:10], 1):
                print(f'\\n{i}. 🏆 {stock["symbol"]} - {stock["signal_type"]}')
                print(f'   💰 入场: {stock["entry_price"]}, 止损: {stock["stop_loss"]}, 目标: {stock["take_profit"]}')
                print(f'   📊 总分: {stock["total_score"]} (技术:{stock["technical_score"]} 量能:{stock["volume_score"]} 动量:{stock["momentum_score"]})')
                print(f'   ⚖️  风险回报比: 1:{stock["risk_reward_ratio"]} | 趋势: {stock["trend"]}')
                print(f'   🔧 线段: {stock["segments_count"]} | 中枢: {stock["pivots_count"]}')
        else:
            print('❌ 当前市场条件下未找到符合条件的股票')
        
        # 保存详细结果
        output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cchan_advanced_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\\n💾 详细结果已保存至: {output_file}')
        
        # 简单回测验证
        if selected_stocks:
            print('\\n📊 执行简单回测验证...')
            backtest_engine = BacktestEngine()
            
            # 模拟信号（实际应用中从历史数据生成）
            sample_signals = [
                {'date': '2025-06-01', 'action': 'buy', 'price': selected_stocks[0]['entry_price'], 'stop_loss': selected_stocks[0]['stop_loss']},
                {'date': '2025-06-15', 'action': 'sell', 'price': selected_stocks[0]['take_profit']}
            ]
            
            performance = backtest_engine.run_backtest(selected_stocks[0]['symbol'], kline_data[selected_stocks[0]['symbol']], sample_signals)
            
            if 'error' not in performance:
                print(f'\\n📈 回测结果示例:')
                print(f'   交易次数: {performance["total_trades"]}')
                print(f'   胜率: {performance["win_rate"]*100:.1f}%')
                print(f'   总收益: {performance["total_return_pct"]:.2f}%')
                print(f'   最大回撤: {performance["max_drawdown"]:.2f}%')
                print(f'   盈亏比: {performance["profit_factor"]:.2f}')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print('\\n🔚 BaoStock已断开')

if __name__ == '__main__':
    results = advanced_cchan_main(test_mode=True, max_stocks=50)