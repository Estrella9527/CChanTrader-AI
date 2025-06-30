#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 历史回测 - 截止2025年6月6日
基于6月6日收盘数据预测后续走势
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# 设定历史截止日期
ANALYSIS_DATE = '2025-06-06'  # 仅使用此日期之前的数据
PREDICTION_START = '2025-06-07'  # 预测起始日期

def safe_data_conversion(df: pd.DataFrame) -> pd.DataFrame:
    """安全的数据转换"""
    df = df.copy()
    
    basic_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in basic_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.split().str[0]
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['high', 'low', 'close'])
    df = df[(df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
    
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0)
        
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """添加技术指标"""
    if len(df) < 20:
        return df
        
    # 移动平均线
    for period in [5, 10, 20, 34]:
        if len(df) >= period:
            df[f'ma{period}'] = df['close'].rolling(period).mean()
    
    # RSI
    if len(df) >= 15:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
    else:
        df['rsi'] = 50
    
    # MACD
    if len(df) >= 26:
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 成交量指标
    if len(df) >= 20:
        df['vol_ma'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / (df['vol_ma'] + 1e-10)
    else:
        df['vol_ratio'] = 1.0
    
    # 价格动量和波动率
    if len(df) >= 10:
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
        df['volatility'] = df['close'].pct_change().rolling(10).std()
    
    return df

class EnhancedChanAnalysis:
    """增强版缠论分析"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = safe_data_conversion(df)
        self.df = add_technical_indicators(self.df)
    
    def find_fractal_points(self) -> list:
        """寻找分型点"""
        fractals = []
        if len(self.df) < 10:
            return fractals
            
        for i in range(3, len(self.df)-3):
            # 顶分型
            if (self.df['high'].iloc[i] > self.df['high'].iloc[i-1] and
                self.df['high'].iloc[i] > self.df['high'].iloc[i+1] and
                self.df['high'].iloc[i] >= self.df['high'].iloc[i-2] and
                self.df['high'].iloc[i] >= self.df['high'].iloc[i+2]):
                fractals.append({
                    'idx': i,
                    'price': self.df['high'].iloc[i],
                    'type': 'high',
                    'date': self.df.iloc[i].get('date', i)
                })
            
            # 底分型
            if (self.df['low'].iloc[i] < self.df['low'].iloc[i-1] and
                self.df['low'].iloc[i] < self.df['low'].iloc[i+1] and
                self.df['low'].iloc[i] <= self.df['low'].iloc[i-2] and
                self.df['low'].iloc[i] <= self.df['low'].iloc[i+2]):
                fractals.append({
                    'idx': i,
                    'price': self.df['low'].iloc[i],
                    'type': 'low',
                    'date': self.df.iloc[i].get('date', i)
                })
        
        return sorted(fractals, key=lambda x: x['idx'])
    
    def analyze_chan_structure(self) -> dict:
        """缠论结构分析"""
        fractals = self.find_fractal_points()
        
        if len(fractals) < 3:
            return {
                'signal': 'insufficient_data',
                'confidence': 0.1,
                'description': '数据不足，无法判断'
            }
        
        # 分析最近的结构
        recent_fractals = fractals[-5:] if len(fractals) >= 5 else fractals
        
        # 寻找买点结构
        signal_info = self._identify_buy_signals(recent_fractals)
        
        # 计算中枢
        pivot_info = self._analyze_pivot_structure(fractals)
        
        return {
            'signal': signal_info['type'],
            'confidence': signal_info['confidence'],
            'description': signal_info['description'],
            'pivot_info': pivot_info,
            'fractal_count': len(fractals)
        }
    
    def _identify_buy_signals(self, fractals: list) -> dict:
        """识别买点信号"""
        if len(fractals) < 3:
            return {'type': 'none', 'confidence': 0.1, 'description': '无明确信号'}
        
        # 检查二买信号 (底-顶-底，且后底高于前底)
        for i in range(len(fractals)-2):
            f1, f2, f3 = fractals[i], fractals[i+1], fractals[i+2]
            
            if (f1['type'] == 'low' and f2['type'] == 'high' and f3['type'] == 'low'):
                if f3['price'] > f1['price'] * 1.005:  # 底部抬高
                    return {
                        'type': 'second_buy',
                        'confidence': 0.8,
                        'description': f'二买信号：底部从{f1["price"]:.2f}抬高至{f3["price"]:.2f}'
                    }
        
        # 检查三买信号 (顶-底-顶，突破前高)
        for i in range(len(fractals)-2):
            f1, f2, f3 = fractals[i], fractals[i+1], fractals[i+2]
            
            if (f1['type'] == 'high' and f2['type'] == 'low' and f3['type'] == 'high'):
                if f3['price'] > f1['price'] * 1.01:  # 突破前高
                    return {
                        'type': 'third_buy',
                        'confidence': 0.7,
                        'description': f'三买信号：突破前高{f1["price"]:.2f}，达到{f3["price"]:.2f}'
                    }
        
        # 检查趋势延续
        if len(fractals) >= 2:
            if fractals[-1]['type'] == 'low' and fractals[-2]['type'] == 'high':
                current_price = self.df['close'].iloc[-1]
                if current_price > fractals[-1]['price'] * 1.02:
                    return {
                        'type': 'trend_follow',
                        'confidence': 0.6,
                        'description': f'趋势跟随：从低点{fractals[-1]["price"]:.2f}反弹'
                    }
        
        return {'type': 'no_signal', 'confidence': 0.3, 'description': '无明确买点信号'}
    
    def _analyze_pivot_structure(self, fractals: list) -> dict:
        """分析中枢结构"""
        if len(fractals) < 6:
            return {'has_pivot': False, 'description': '无中枢结构'}
        
        # 简化的中枢识别：连续的高低点形成的震荡区间
        recent_highs = [f['price'] for f in fractals[-6:] if f['type'] == 'high']
        recent_lows = [f['price'] for f in fractals[-6:] if f['type'] == 'low']
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            pivot_high = min(recent_highs[-2:])  # 最近两个高点的较低者
            pivot_low = max(recent_lows[-2:])    # 最近两个低点的较高者
            
            if pivot_high > pivot_low:
                current_price = self.df['close'].iloc[-1]
                return {
                    'has_pivot': True,
                    'high': pivot_high,
                    'low': pivot_low,
                    'center': (pivot_high + pivot_low) / 2,
                    'position': 'above' if current_price > pivot_high else 'below' if current_price < pivot_low else 'inside',
                    'description': f'中枢区间 {pivot_low:.2f}-{pivot_high:.2f}'
                }
        
        return {'has_pivot': False, 'description': '无清晰中枢'}

def comprehensive_analysis(symbol: str, df: pd.DataFrame) -> dict:
    """综合分析函数"""
    try:
        if len(df) < 40:
            return None
            
        current_price = float(df['close'].iloc[-1])
        if not (2 <= current_price <= 100):  # 价格过滤
            return None
        
        # 缠论分析
        chan = EnhancedChanAnalysis(df)
        chan_result = chan.analyze_chan_structure()
        
        # 技术指标分析
        latest = df.iloc[-1]
        
        # 均线排列分析
        ma_status = 'neutral'
        if all(f'ma{p}' in latest.index for p in [5, 10, 20]):
            if latest['close'] > latest['ma5'] > latest['ma10'] > latest['ma20']:
                ma_status = 'strong_bullish'
            elif latest['close'] > latest['ma5'] > latest['ma10']:
                ma_status = 'bullish'
            elif latest['close'] < latest['ma5'] < latest['ma10'] < latest['ma20']:
                ma_status = 'bearish'
        
        # MACD分析
        macd_status = 'neutral'
        if 'macd' in latest.index and 'macd_signal' in latest.index:
            if latest['macd'] > latest['macd_signal'] and latest['macd'] > 0:
                macd_status = 'bullish'
            elif latest['macd'] > latest['macd_signal']:
                macd_status = 'weak_bullish'
            else:
                macd_status = 'bearish'
        
        # RSI分析
        rsi = latest.get('rsi', 50)
        rsi_status = 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'normal'
        
        # 成交量分析
        vol_ratio = latest.get('vol_ratio', 1.0)
        vol_status = 'high' if vol_ratio > 2.0 else 'normal' if vol_ratio > 0.8 else 'low'
        
        # 动量分析
        momentum_5 = latest.get('momentum_5', 0)
        momentum_10 = latest.get('momentum_10', 0)
        
        # 综合评分
        score = 0.5
        
        # 缠论信号评分 (40%)
        chan_scores = {
            'second_buy': 0.35,
            'third_buy': 0.30,
            'trend_follow': 0.20,
            'no_signal': 0.05
        }
        score += chan_scores.get(chan_result['signal'], 0) * chan_result['confidence']
        
        # 技术指标评分 (35%)
        ma_scores = {'strong_bullish': 0.15, 'bullish': 0.10, 'neutral': 0.05, 'bearish': 0}
        macd_scores = {'bullish': 0.10, 'weak_bullish': 0.05, 'neutral': 0.03, 'bearish': 0}
        rsi_scores = {'normal': 0.10, 'oversold': 0.08, 'overbought': 0.03}
        
        score += ma_scores.get(ma_status, 0)
        score += macd_scores.get(macd_status, 0)
        score += rsi_scores.get(rsi_status, 0)
        
        # 成交量评分 (15%)
        vol_scores = {'high': 0.15, 'normal': 0.10, 'low': 0.05}
        score += vol_scores.get(vol_status, 0)
        
        # 动量评分 (10%)
        if momentum_5 > 0.03 and momentum_10 > 0.05:
            score += 0.10
        elif momentum_5 > 0.01:
            score += 0.05
        
        # 只返回高分股票
        if score < 0.75:
            return None
        
        return {
            'symbol': symbol,
            'analysis_date': ANALYSIS_DATE,
            'current_price': current_price,
            'total_score': round(score, 3),
            
            # 缠论分析
            'chan_signal': chan_result['signal'],
            'chan_confidence': chan_result['confidence'],
            'chan_description': chan_result['description'],
            
            # 技术指标
            'ma_status': ma_status,
            'macd_status': macd_status,
            'rsi': round(rsi, 1),
            'rsi_status': rsi_status,
            'volume_ratio': round(vol_ratio, 2),
            'volume_status': vol_status,
            'momentum_5d': round(momentum_5 * 100, 2),
            'momentum_10d': round(momentum_10 * 100, 2),
            
            # 交易建议
            'entry_price': current_price,
            'stop_loss': round(current_price * 0.92, 2),  # 8%止损
            'target_1': round(current_price * 1.12, 2),   # 12%目标
            'target_2': round(current_price * 1.25, 2),   # 25%目标
            'holding_period': '5-15个交易日',
            'confidence_level': 'high' if score > 0.85 else 'medium'
        }
        
    except Exception as e:
        return None

def june6_stock_analysis():
    """6月6日股票分析"""
    load_dotenv()
    
    print(f'=== CChanTrader-AI 6月6日选股分析 ===')
    print(f'📅 分析基准日期: {ANALYSIS_DATE}')
    print(f'🎯 预测验证期间: {PREDICTION_START} 及之后')
    
    lg = bs.login()
    print(f'📊 BaoStock连接状态: {lg.error_code}')
    
    try:
        # 获取股票列表
        print(f'\\n🔍 获取{ANALYSIS_DATE}股票列表...')
        stock_rs = bs.query_all_stock(ANALYSIS_DATE)
        stock_df = stock_rs.get_data()
        
        if stock_df.empty:
            print('无法获取股票列表')
            return []
        
        # 筛选活跃A股
        a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')].head(150)
        print(f'📋 待分析股票: {len(a_stocks)}只')
        
        # 获取历史数据
        print(f'\\n📈 获取历史K线数据...')
        start_date = '2025-04-01'
        
        historical_data = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='获取数据'):
            code = stock['code']
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume',
                    start_date=start_date, 
                    end_date=ANALYSIS_DATE,
                    frequency='d')
                day_df = rs.get_data()
                
                if not day_df.empty and len(day_df) >= 40:
                    historical_data[code] = day_df
                    
            except Exception:
                continue
        
        print(f'✅ 获取到 {len(historical_data)} 只股票数据')
        
        # 执行分析
        print(f'\\n🧠 执行综合分析...')
        selected_stocks = []
        
        for symbol, df in tqdm(historical_data.items(), desc='技术分析'):
            result = comprehensive_analysis(symbol, df)
            if result:
                selected_stocks.append(result)
        
        # 按评分排序
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\\n🎯 === {ANALYSIS_DATE} 选股分析结果 ===')
        print(f'符合条件股票: {len(selected_stocks)}只')
        
        # 获取股票名称
        stock_names = {}
        for code in [s['symbol'] for s in selected_stocks[:10]]:
            stock_info = stock_df[stock_df['code'] == code]
            if not stock_info.empty:
                stock_names[code] = stock_info.iloc[0]['code_name']
        
        if selected_stocks:
            print(f'\\n📊 重点推荐 (基于{ANALYSIS_DATE}收盘数据):')
            for i, stock in enumerate(selected_stocks[:8], 1):
                stock_name = stock_names.get(stock['symbol'], '未知')
                print(f'\\n🏆 第{i}名: {stock["symbol"]} ({stock_name})')
                print(f'   💰 {ANALYSIS_DATE}收盘价: {stock["current_price"]:.2f}元')
                print(f'   📊 综合评分: {stock["total_score"]} ({stock["confidence_level"]})')
                print(f'   🎯 缠论信号: {stock["chan_signal"]} (置信度{stock["chan_confidence"]:.1f})')
                print(f'   📈 均线状态: {stock["ma_status"]}')
                print(f'   📊 MACD: {stock["macd_status"]} | RSI: {stock["rsi"]} ({stock["rsi_status"]})')
                print(f'   📊 成交量: {stock["volume_ratio"]}倍 ({stock["volume_status"]})')
                print(f'   ⚡ 动量: 5日{stock["momentum_5d"]}% | 10日{stock["momentum_10d"]}%')
                print(f'   💡 {stock["chan_description"]}')
                print(f'   🎯 交易建议:')
                print(f'       入场: {stock["entry_price"]:.2f}元')
                print(f'       止损: {stock["stop_loss"]:.2f}元 (-8%)')
                print(f'       目标1: {stock["target_1"]:.2f}元 (+12%)')
                print(f'       目标2: {stock["target_2"]:.2f}元 (+25%)')
                print(f'       持仓: {stock["holding_period"]}')
        
        # 保存分析结果
        output_file = fos.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'analysis_june6_prediction.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\\n💾 详细分析结果已保存至: {output_file}')
        print(f'\\n🔮 请用6月7日及之后的实际走势验证预测准确性！')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print(f'\\n🔚 分析完成')

if __name__ == '__main__':
    results = june6_stock_analysis()