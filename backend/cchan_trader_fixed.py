#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 核心选股引擎 - 修复版本
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 全局参数 - 调整为更宽松的条件
PARAMS = {
    "ma_short": 5,
    "ma_mid": 20,  # 降低到20日均线
    "daily_up_cross_ratio": 1.00,  # 不要求突破，只要站上即可
    "v_break_min": 1.2,  # 降低成交量要求
    "v_pull_max": 0.8,   # 放宽缩量要求
    "vol_ma_period": 5,
    "price_strength_days": 10,
    "stop_buffer_pct": 0.03,
    "rsi_oversold": 25,  # 扩大RSI范围
    "rsi_overbought": 75,
}

def safe_numeric_convert(df):
    """安全的数据类型转换"""
    df = df.copy()
    
    # 确保数值列正确转换
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
    for col in numeric_cols:
        if col in df.columns:
            # 先确保是字符串，再转换
            df[col] = df[col].astype(str)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 过滤无效数据
    df = df.dropna(subset=['high', 'low', 'close'])
    df = df[(df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
    
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0)
        
    return df

def calculate_rsi(prices, period=14):
    """安全的RSI计算"""
    try:
        # 确保输入是数值类型
        prices = pd.to_numeric(prices, errors='coerce')
        prices = prices.dropna()
        
        if len(prices) < period + 1:
            return pd.Series([50] * len(prices), index=prices.index)
            
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 避免除零
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
        
    except Exception as e:
        print(f"RSI计算错误: {e}")
        return pd.Series([50] * len(prices), index=prices.index)

def simple_trend_analysis(df):
    """简化的趋势分析"""
    try:
        if len(df) < 10:
            return {
                'trend': 'side',
                'signals': {'2_buy': False, '3_buy': False},
                'volume_factor': 1.0,
                'rsi': 50.0,
                'ma5': df['close'].iloc[-1],
                'confidence': 0.3
            }
            
        # 移动平均线
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        
        current_price = float(df['close'].iloc[-1])
        ma5 = float(df['ma5'].iloc[-1])
        ma10 = float(df['ma10'].iloc[-1])
        
        # 趋势判断
        trend = 'up' if current_price > ma5 > ma10 else 'down' if current_price < ma5 < ma10 else 'side'
        
        # 成交量分析
        recent_vol = df['volume'].iloc[-5:].mean()
        prev_vol = df['volume'].iloc[-10:-5].mean()
        volume_factor = float(recent_vol / prev_vol) if prev_vol > 0 else 1.0
        
        # RSI计算
        rsi_series = calculate_rsi(df['close'])
        rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
        
        # 信号生成 - 放宽条件
        signals = {
            '2_buy': trend == 'up' and volume_factor > PARAMS["v_break_min"] and PARAMS["rsi_oversold"] <= rsi <= PARAMS["rsi_overbought"],
            '3_buy': trend == 'up' and current_price > ma5 * 0.99 and volume_factor > 1.0  # 更宽松的条件
        }
        
        # 置信度
        confidence = 0.5
        if signals['2_buy']: confidence += 0.3
        if signals['3_buy']: confidence += 0.2
        if trend == 'up': confidence += 0.1
        
        return {
            'trend': trend,
            'signals': signals,
            'volume_factor': volume_factor,
            'rsi': rsi,
            'ma5': ma5,
            'confidence': min(confidence, 1.0)
        }
        
    except Exception as e:
        print(f"趋势分析错误: {e}")
        return {
            'trend': 'side',
            'signals': {'2_buy': False, '3_buy': False},
            'volume_factor': 1.0,
            'rsi': 50.0,
            'ma5': df['close'].iloc[-1] if not df.empty else 0,
            'confidence': 0.1
        }

def is_daily_uptrend(df):
    """日线上升趋势判断"""
    try:
        if len(df) < PARAMS["ma_mid"]:
            return False
            
        current_price = float(df['close'].iloc[-1])
        ma34 = float(df['close'].rolling(PARAMS["ma_mid"]).mean().iloc[-1])
        
        # 价格突破和均线条件
        price_trend = current_price > ma34
        
        # 近期价格强度
        if len(df) >= PARAMS["price_strength_days"]:
            price_change = (current_price / float(df['close'].iloc[-PARAMS["price_strength_days"]]) - 1) * 100
            strength_ok = price_change > 0
        else:
            strength_ok = True
            
        return price_trend and strength_ok
        
    except Exception as e:
        print(f"趋势判断错误: {e}")
        return False

def is_hot_leader(symbol, df):
    """热点龙头判断"""
    try:
        if len(df) < PARAMS["price_strength_days"]:
            return False, "数据不足"
            
        # 价格强度
        current_price = float(df['close'].iloc[-1])
        old_price = float(df['close'].iloc[-PARAMS["price_strength_days"]])
        price_change = (current_price / old_price - 1) * 100
        
        # 成交量活跃度
        recent_vol = df['volume'].iloc[-5:].mean()
        prev_vol = df['volume'].iloc[-15:-5].mean()
        vol_activity = float(recent_vol / prev_vol) if prev_vol > 0 else 1.0
        
        # 热点判定 - 放宽条件
        is_hot = (price_change > 2.0 and vol_activity > 1.2) or price_change > 5.0 or vol_activity > 1.5
        
        return is_hot, "活跃股"
        
    except Exception as e:
        print(f"热点判断错误: {e}")
        return False, "判断失败"

def select_stock(symbol, kdict):
    """完整选股逻辑"""
    try:
        day_df = kdict.get("D")
        if day_df is None or day_df.empty:
            return None
            
        # 数据预处理
        day_df = safe_numeric_convert(day_df)
        if len(day_df) < 30:
            return None
            
        # Step 1: 日线趋势过滤
        if not is_daily_uptrend(day_df):
            return None
            
        # Step 2: 技术分析
        analysis = simple_trend_analysis(day_df)
        
        # Step 3: 信号过滤
        if not (analysis['signals']['2_buy'] or analysis['signals']['3_buy']):
            return None
            
        # Step 4: 热点验证
        hot_leader, industry = is_hot_leader(symbol, day_df)
        if not hot_leader:
            return None
            
        # Step 5: 生成结果
        current_price = float(day_df['close'].iloc[-1])
        entry_price = current_price
        stop_loss = entry_price * (1 - PARAMS["stop_buffer_pct"])
        
        # 计算价格强度
        price_strength = 0
        if len(day_df) >= PARAMS["price_strength_days"]:
            old_price = float(day_df['close'].iloc[-PARAMS["price_strength_days"]])
            price_strength = (current_price / old_price - 1) * 100
            
        signal_type = '2_buy' if analysis['signals']['2_buy'] else '3_buy'
        
        return {
            'symbol': symbol,
            'industry': industry,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'signal': signal_type,
            'price_strength': round(price_strength, 2),
            'volume_factor': round(analysis['volume_factor'], 2),
            'rsi': round(analysis['rsi'], 1),
            'trend': analysis['trend'],
            'confidence': round(analysis['confidence'], 2)
        }
        
    except Exception as e:
        print(f"处理股票 {symbol} 时出错: {e}")
        return None

def cchan_trader_main(test_mode=True, max_stocks=20):
    """主程序"""
    load_dotenv()
    
    print('=== CChanTrader-AI 修复版本 ===')
    
    lg = bs.login()
    print(f'BaoStock状态: {lg.error_code}')
    
    try:
        # 获取股票列表
        for days_back in range(0, 10):
            query_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            stock_rs = bs.query_all_stock(query_date)
            stock_df = stock_rs.get_data()
            if not stock_df.empty:
                break
                
        a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')]
        if test_mode:
            a_stocks = a_stocks.head(max_stocks)
            
        print(f'待分析股票: {len(a_stocks)}只')
        
        # 获取K线数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        
        kline_data = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='获取数据'):
            code = stock['code']
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume,amount',
                    start_date=start_date, end_date=end_date, frequency='d')
                day_df = rs.get_data()
                
                if not day_df.empty and len(day_df) >= 30:
                    kline_data[code] = {'D': day_df}
                    
            except Exception:
                continue
                
        print(f'获取数据: {len(kline_data)}只')
        
        # 选股分析
        results = []
        for symbol, kdict in tqdm(kline_data.items(), desc='选股分析'):
            result = select_stock(symbol, kdict)
            if result:
                results.append(result)
                
        # 排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f'\\n=== 选股结果 ({len(results)}只) ===')
        for i, stock in enumerate(results[:10], 1):  # 显示前10只
            print(f'{i}. {stock["symbol"]} - {stock["signal"]}')
            print(f'   入场: {stock["entry_price"]}, 止损: {stock["stop_loss"]}')
            print(f'   强度: {stock["price_strength"]}%, 量能: {stock["volume_factor"]}x')
            print(f'   置信度: {stock["confidence"]}')
            
        # 保存结果
        with open('/Users/yang/cchan_results_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        return results
        
    finally:
        bs.logout()

if __name__ == '__main__':
    results = cchan_trader_main(test_mode=True, max_stocks=30)