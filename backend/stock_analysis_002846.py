#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单只股票分析 - 002846
"""

import pandas as pd
import numpy as np
import baostock as bs
from datetime import datetime, timedelta
from dotenv import load_dotenv

def analyze_stock(stock_code):
    # 加载环境变量
    load_dotenv()
    
    print(f'=== 股票 {stock_code} 详细分析 ===')
    
    # 登录BaoStock
    lg = bs.login()
    print(f'BaoStock 登录状态: {lg.error_code} - {lg.error_msg}')
    
    try:
        # 获取股票基本信息
        print(f'\n1. 获取股票基本信息...')
        
        # 尝试最近几个交易日获取股票列表
        stock_info = None
        for days_back in range(0, 10):
            query_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            stock_rs = bs.query_all_stock(query_date)
            stock_df = stock_rs.get_data()
            
            if not stock_df.empty:
                stock_info = stock_df[stock_df['code'] == f'sz.{stock_code}']
                if not stock_info.empty:
                    break
        
        if stock_info is not None and not stock_info.empty:
            print(f'股票名称: {stock_info.iloc[0]["code_name"]}')
            print(f'交易状态: {stock_info.iloc[0]["tradeStatus"]}')
        else:
            print(f'未找到股票 {stock_code} 的基本信息，继续进行K线分析')
        
        # 获取历史K线数据 (更长时间段)
        print(f'\n2. 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 一年数据
        
        # 获取日K线
        rs_day = bs.query_history_k_data_plus(f'sz.{stock_code}', 
            'date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ',
            start_date=start_date, end_date=end_date, frequency='d')
        day_df = rs_day.get_data()
        
        if day_df.empty:
            print(f'无法获取股票 {stock_code} 的K线数据')
            return
        
        # 数据清洗
        numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg', 'peTTM', 'pbMRQ']
        for col in numeric_cols:
            if col in day_df.columns:
                day_df[col] = pd.to_numeric(day_df[col], errors='coerce')
        
        day_df = day_df.dropna(subset=['close'])
        day_df['date'] = pd.to_datetime(day_df['date'])
        day_df = day_df.sort_values('date')
        
        print(f'获取到 {len(day_df)} 个交易日的数据')
        print(f'数据时间范围: {day_df["date"].min()} 至 {day_df["date"].max()}')
        
        # 基本信息分析
        print(f'\n3. 基本信息分析')
        latest = day_df.iloc[-1]
        print(f'最新交易日: {latest["date"].strftime("%Y-%m-%d")}')
        print(f'最新价格: {latest["close"]:.2f}')
        print(f'涨跌幅: {latest["pctChg"]:.2f}%')
        if not pd.isna(latest['turn']):
            print(f'换手率: {latest["turn"]:.2f}%')
        if not pd.isna(latest['peTTM']):
            print(f'市盈率TTM: {latest["peTTM"]:.2f}')
        if not pd.isna(latest['pbMRQ']):
            print(f'市净率: {latest["pbMRQ"]:.2f}')
        
        # 技术指标分析
        print(f'\n4. 技术指标分析')
        
        # 移动平均线
        day_df['ma5'] = day_df['close'].rolling(window=5).mean()
        day_df['ma10'] = day_df['close'].rolling(window=10).mean()
        day_df['ma20'] = day_df['close'].rolling(window=20).mean()
        day_df['ma60'] = day_df['close'].rolling(window=60).mean()
        
        latest_ma = day_df.iloc[-1]
        print(f'MA5:  {latest_ma["ma5"]:.2f}')
        print(f'MA10: {latest_ma["ma10"]:.2f}')
        print(f'MA20: {latest_ma["ma20"]:.2f}')
        print(f'MA60: {latest_ma["ma60"]:.2f}')
        
        # 趋势分析
        print(f'\n5. 趋势分析')
        
        # 短期趋势 (5日)
        short_trend = day_df['close'].iloc[-5:].iloc[-1] > day_df['close'].iloc[-5:].iloc[0]
        print(f'短期趋势 (5日): {"上升" if short_trend else "下降"}')
        
        # 中期趋势 (20日)
        if len(day_df) >= 20:
            mid_trend = day_df['close'].iloc[-20:].iloc[-1] > day_df['close'].iloc[-20:].iloc[0]
            print(f'中期趋势 (20日): {"上升" if mid_trend else "下降"}')
        
        # 长期趋势 (60日)
        if len(day_df) >= 60:
            long_trend = day_df['close'].iloc[-60:].iloc[-1] > day_df['close'].iloc[-60:].iloc[0]
            print(f'长期趋势 (60日): {"上升" if long_trend else "下降"}')
        
        # 均线排列
        current_price = latest_ma["close"]
        ma5 = latest_ma["ma5"]
        ma10 = latest_ma["ma10"]
        ma20 = latest_ma["ma20"]
        
        if current_price > ma5 > ma10 > ma20:
            trend_signal = "多头排列"
        elif current_price < ma5 < ma10 < ma20:
            trend_signal = "空头排列"
        else:
            trend_signal = "震荡整理"
        
        print(f'均线排列: {trend_signal}')
        
        # 成交量分析
        print(f'\n6. 成交量分析')
        recent_vol = day_df['volume'].iloc[-5:].mean()
        prev_vol = day_df['volume'].iloc[-15:-5].mean()
        vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1
        print(f'近5日平均成交量: {recent_vol:.0f}')
        print(f'前10日平均成交量: {prev_vol:.0f}')
        print(f'成交量比率: {vol_ratio:.2f} ({"放量" if vol_ratio > 1.5 else "缩量" if vol_ratio < 0.8 else "正常"})')
        
        # 波动率分析
        print(f'\n7. 波动率分析')
        day_df['daily_return'] = day_df['close'].pct_change()
        volatility_20 = day_df['daily_return'].iloc[-20:].std() * np.sqrt(252) * 100  # 年化波动率
        print(f'20日年化波动率: {volatility_20:.2f}%')
        
        # 支撑位和阻力位
        print(f'\n8. 支撑阻力位分析')
        recent_30 = day_df.iloc[-30:]
        support = recent_30['low'].min()
        resistance = recent_30['high'].max()
        print(f'近30日支撑位: {support:.2f}')
        print(f'近30日阻力位: {resistance:.2f}')
        print(f'当前位置: {((current_price - support) / (resistance - support) * 100):.1f}% (0%=支撑位, 100%=阻力位)')
        
        # 综合评分
        print(f'\n9. 综合评分')
        score = 0
        factors = []
        
        # 趋势评分
        if short_trend:
            score += 2
            factors.append("短期上升趋势 +2")
        if len(day_df) >= 20 and mid_trend:
            score += 2
            factors.append("中期上升趋势 +2")
        if trend_signal == "多头排列":
            score += 3
            factors.append("多头排列 +3")
        elif trend_signal == "震荡整理":
            score += 1
            factors.append("震荡整理 +1")
        
        # 成交量评分
        if vol_ratio > 1.5:
            score += 2
            factors.append("成交量放大 +2")
        elif vol_ratio > 1.2:
            score += 1
            factors.append("成交量温和放大 +1")
        
        # 位置评分
        position_pct = (current_price - support) / (resistance - support)
        if 0.2 <= position_pct <= 0.8:
            score += 1
            factors.append("价格位置适中 +1")
        
        print(f'总分: {score}/10')
        for factor in factors:
            print(f'  - {factor}')
        
        if score >= 7:
            recommendation = "强烈看好"
        elif score >= 5:
            recommendation = "谨慎看好"
        elif score >= 3:
            recommendation = "中性观望"
        else:
            recommendation = "谨慎回避"
        
        print(f'\n投资建议: {recommendation}')
        
        # 关键价位
        print(f'\n10. 关键价位')
        print(f'买入参考: {ma5:.2f} (MA5支撑)')
        print(f'止损参考: {support:.2f} (近期低点)')
        print(f'目标价位: {resistance:.2f} (近期高点)')
        
    finally:
        # 登出BaoStock
        bs.logout()
        print(f'\nBaoStock 已登出')

if __name__ == '__main__':
    analyze_stock('002846')