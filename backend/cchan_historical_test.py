#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 历史回测 - 截止2025年6月23日
仅使用6月24日之前的数据进行选股分析
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# 设定历史截止日期
HISTORICAL_END_DATE = '2025-06-23'  # 仅使用此日期之前的数据

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
    
    # 成交量指标
    if len(df) >= 20:
        df['vol_ma'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / (df['vol_ma'] + 1e-10)
    else:
        df['vol_ratio'] = 1.0
    
    # 价格动量
    if len(df) >= 10:
        df['momentum'] = df['close'].pct_change(10)
    else:
        df['momentum'] = 0
    
    return df

class ChanAnalysis:
    """缠论分析类"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = safe_data_conversion(df)
        self.df = add_technical_indicators(self.df)
    
    def find_pivots(self) -> list:
        """寻找关键转折点"""
        pivots = []
        if len(self.df) < 10:
            return pivots
            
        for i in range(5, len(self.df)-2):  # 注意：不能超出数据范围
            # 局部高点
            if (i < len(self.df) - 5 and 
                self.df['high'].iloc[i] == self.df['high'].iloc[max(0, i-5):min(len(self.df), i+6)].max()):
                pivots.append({
                    'idx': i,
                    'price': self.df['high'].iloc[i],
                    'type': 'high',
                    'date': self.df.index[i] if hasattr(self.df.index, 'date') else i
                })
            
            # 局部低点
            if (i < len(self.df) - 5 and 
                self.df['low'].iloc[i] == self.df['low'].iloc[max(0, i-5):min(len(self.df), i+6)].min()):
                pivots.append({
                    'idx': i,
                    'price': self.df['low'].iloc[i],
                    'type': 'low',
                    'date': self.df.index[i] if hasattr(self.df.index, 'date') else i
                })
        
        return sorted(pivots, key=lambda x: x['idx'])
    
    def analyze_trend_structure(self) -> dict:
        """分析趋势结构"""
        try:
            latest = self.df.iloc[-1]
            
            # 均线排列分析
            ma_alignment = 'neutral'
            if all(col in latest.index for col in ['ma5', 'ma10', 'ma20']):
                if latest['close'] > latest['ma5'] > latest['ma10'] > latest['ma20']:
                    ma_alignment = 'strong_bullish'
                elif latest['close'] > latest['ma5'] > latest['ma10']:
                    ma_alignment = 'bullish'
                elif latest['close'] < latest['ma5'] < latest['ma10'] < latest['ma20']:
                    ma_alignment = 'bearish'
                elif latest['close'] < latest['ma5'] < latest['ma10']:
                    ma_alignment = 'weak_bearish'
            
            # 缠论结构分析
            pivots = self.find_pivots()
            structure_signal = self.analyze_chan_structure(pivots)
            
            # RSI状态
            rsi = latest.get('rsi', 50)
            rsi_status = 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'normal'
            
            # 成交量状态
            vol_ratio = latest.get('vol_ratio', 1.0)
            volume_status = 'high' if vol_ratio > 2.0 else 'elevated' if vol_ratio > 1.5 else 'normal'
            
            # 动量分析
            momentum = latest.get('momentum', 0)
            momentum_status = 'strong_up' if momentum > 0.05 else 'up' if momentum > 0.02 else 'down' if momentum < -0.02 else 'neutral'
            
            return {
                'current_price': float(latest['close']),
                'ma_alignment': ma_alignment,
                'structure_signal': structure_signal,
                'rsi': float(rsi),
                'rsi_status': rsi_status,
                'volume_ratio': float(vol_ratio),
                'volume_status': volume_status,
                'momentum': float(momentum),
                'momentum_status': momentum_status,
                'pivots_count': len(pivots),
                'latest_pivot': pivots[-1] if pivots else None
            }
            
        except Exception as e:
            print(f"趋势分析错误: {e}")
            return {
                'current_price': float(self.df['close'].iloc[-1]) if not self.df.empty else 0,
                'ma_alignment': 'neutral',
                'structure_signal': 'none',
                'rsi': 50,
                'rsi_status': 'normal',
                'volume_ratio': 1.0,
                'volume_status': 'normal',
                'momentum': 0,
                'momentum_status': 'neutral',
                'pivots_count': 0,
                'latest_pivot': None
            }
    
    def analyze_chan_structure(self, pivots: list) -> str:
        """分析缠论结构信号"""
        if len(pivots) < 3:
            return 'insufficient_data'
        
        # 查找最近的结构
        recent_pivots = pivots[-3:]
        
        # 检查是否形成买点结构
        if len(recent_pivots) >= 3:
            p1, p2, p3 = recent_pivots[-3:]
            
            # 二买信号：低-高-低，且最后一个低点高于第一个低点
            if (p1['type'] == 'low' and p2['type'] == 'high' and p3['type'] == 'low' and
                p3['price'] > p1['price'] * 1.02):
                return 'second_buy'
            
            # 三买信号：突破前高后的回调
            if (p1['type'] == 'high' and p2['type'] == 'low' and p3['type'] == 'high' and
                p3['price'] > p1['price'] * 1.01):
                return 'third_buy'
        
        # 趋势延续信号
        if len(pivots) >= 2:
            if pivots[-1]['type'] == 'low' and pivots[-2]['type'] == 'high':
                if pivots[-1]['price'] > pivots[-2]['price'] * 0.98:
                    return 'trend_continuation'
        
        return 'no_clear_signal'

def comprehensive_stock_analysis(symbol: str, df: pd.DataFrame) -> dict:
    """综合股票分析"""
    try:
        # 基础过滤
        if len(df) < 40:
            return None
            
        current_price = float(df['close'].iloc[-1])
        if not (3 <= current_price <= 200):
            return None
        
        # 缠论分析
        chan = ChanAnalysis(df)
        analysis = chan.analyze_trend_structure()
        
        # 综合评分计算
        score = 0.5  # 基础分
        
        # MA排列得分 (25%)
        ma_score = {
            'strong_bullish': 0.25,
            'bullish': 0.20,
            'neutral': 0.10,
            'weak_bearish': 0.05,
            'bearish': 0.0
        }.get(analysis['ma_alignment'], 0.10)
        score += ma_score
        
        # 缠论结构得分 (30%)
        structure_score = {
            'second_buy': 0.30,
            'third_buy': 0.25,
            'trend_continuation': 0.15,
            'no_clear_signal': 0.05,
            'insufficient_data': 0.0
        }.get(analysis['structure_signal'], 0.05)
        score += structure_score
        
        # RSI得分 (15%)
        rsi_score = 0.15 if analysis['rsi_status'] == 'normal' else 0.10 if analysis['rsi_status'] == 'oversold' else 0.05
        score += rsi_score
        
        # 成交量得分 (20%)
        vol_score = {
            'high': 0.20,
            'elevated': 0.15,
            'normal': 0.10
        }.get(analysis['volume_status'], 0.10)
        score += vol_score
        
        # 动量得分 (10%)
        momentum_score = {
            'strong_up': 0.10,
            'up': 0.08,
            'neutral': 0.05,
            'down': 0.02
        }.get(analysis['momentum_status'], 0.05)
        score += momentum_score
        
        # 只选择高分股票
        if score < 0.8:
            return None
        
        # 计算交易参数
        stop_loss = current_price * 0.93  # 7%止损
        take_profit = current_price * 1.20  # 20%目标
        
        return {
            'symbol': symbol,
            'analysis_date': HISTORICAL_END_DATE,
            'current_price': current_price,
            'total_score': round(score, 3),
            'ma_alignment': analysis['ma_alignment'],
            'structure_signal': analysis['structure_signal'],
            'rsi': analysis['rsi'],
            'rsi_status': analysis['rsi_status'],
            'volume_ratio': analysis['volume_ratio'],
            'volume_status': analysis['volume_status'],
            'momentum': analysis['momentum'],
            'momentum_status': analysis['momentum_status'],
            'entry_price': current_price,
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'risk_reward_ratio': round((take_profit - current_price) / (current_price - stop_loss), 2),
            'confidence_level': 'high' if score > 0.9 else 'medium'
        }
        
    except Exception as e:
        print(f"分析 {symbol} 时出错: {e}")
        return None

def historical_stock_selection():
    """历史时点选股分析"""
    load_dotenv()
    
    print(f'=== CChanTrader-AI 历史回测分析 ===')
    print(f'📅 分析截止日期: {HISTORICAL_END_DATE}')
    print(f'🎯 目标: 基于6月23日数据预测6月24日交易机会')
    
    lg = bs.login()
    print(f'📊 BaoStock连接状态: {lg.error_code}')
    
    try:
        # 获取股票列表 - 使用历史日期
        print(f'\\n🔍 获取{HISTORICAL_END_DATE}的股票列表...')
        stock_rs = bs.query_all_stock(HISTORICAL_END_DATE)
        stock_df = stock_rs.get_data()
        
        if stock_df.empty:
            print('无法获取股票列表')
            return []
        
        # 筛选A股
        a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')].head(100)  # 测试100只
        print(f'📋 待分析股票: {len(a_stocks)}只')
        
        # 获取历史K线数据
        print(f'\\n📈 获取历史K线数据...')
        start_date = '2025-04-01'  # 足够的历史数据用于技术分析
        
        historical_data = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='获取历史数据'):
            code = stock['code']
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume',
                    start_date=start_date, 
                    end_date=HISTORICAL_END_DATE,  # 重要：限制在6月23日
                    frequency='d')
                day_df = rs.get_data()
                
                if not day_df.empty and len(day_df) >= 40:
                    historical_data[code] = day_df
                    
            except Exception:
                continue
        
        print(f'✅ 获取到 {len(historical_data)} 只股票的历史数据')
        
        # 执行分析
        print(f'\\n🧠 执行综合技术分析...')
        selected_stocks = []
        
        for symbol, df in tqdm(historical_data.items(), desc='技术分析'):
            result = comprehensive_stock_analysis(symbol, df)
            if result:
                selected_stocks.append(result)
        
        # 按评分排序
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\\n🎯 === {HISTORICAL_END_DATE} 选股分析结果 ===')
        print(f'符合条件的股票: {len(selected_stocks)}只')
        
        if selected_stocks:
            print(f'\\n📊 重点推荐股票 (基于6月23日收盘数据):')
            for i, stock in enumerate(selected_stocks[:8], 1):
                print(f'\\n{i}. 🏆 {stock["symbol"]}')
                print(f'   💰 6月23日收盘价: {stock["current_price"]:.2f}元')
                print(f'   📊 综合评分: {stock["total_score"]} ({stock["confidence_level"]}置信度)')
                print(f'   📈 均线排列: {stock["ma_alignment"]}')
                print(f'   🎯 缠论信号: {stock["structure_signal"]}')
                print(f'   📊 RSI: {stock["rsi"]:.1f} ({stock["rsi_status"]})')
                print(f'   📊 成交量: {stock["volume_ratio"]:.2f}倍 ({stock["volume_status"]})')
                print(f'   ⚡ 动量: {stock["momentum"]:.3f} ({stock["momentum_status"]})')
                print(f'   🎯 建议入场: {stock["entry_price"]:.2f}元')
                print(f'   🛡️ 止损: {stock["stop_loss"]:.2f}元 (-7%)')
                print(f'   🎯 目标: {stock["take_profit"]:.2f}元 (+20%)')
                print(f'   ⚖️ 风险回报比: 1:{stock["risk_reward_ratio"]}')
        
        # 保存分析结果
        output_file = f'/Users/yang/historical_analysis_{HISTORICAL_END_DATE.replace("-", "")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\\n💾 分析结果已保存至: {output_file}')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print(f'\\n🔚 BaoStock已断开连接')

if __name__ == '__main__':
    results = historical_stock_selection()