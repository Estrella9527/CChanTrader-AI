#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaoStock 股票选股系统
使用BaoStock免费股票数据接口进行技术分析和选股
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv

def main():
    # 加载环境变量
    load_dotenv()
    
    print('=== BaoStock 股票选股系统 ===')
    
    # 登录BaoStock
    lg = bs.login()
    print(f'BaoStock 登录状态: {lg.error_code} - {lg.error_msg}')
    
    try:
        # ---------- STEP 1: 获取股票列表 ----------
        print('\n1. 获取股票列表...')
        
        # 尝试最近几个交易日
        for days_back in range(0, 10):
            query_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            stock_rs = bs.query_all_stock(query_date)
            stock_df = stock_rs.get_data()
            
            if not stock_df.empty:
                print(f'使用日期: {query_date}')
                break
        
        if stock_df.empty:
            print('无法获取股票列表数据')
            return
        
        print(f'股票数据列名: {stock_df.columns.tolist()}')
        print(f'股票数据前3行:\n{stock_df.head(3)}')
        
        # 过滤A股
        if 'code' in stock_df.columns:
            a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')].head(15)
        else:
            print('未找到code列，使用所有数据')
            a_stocks = stock_df.head(15)
        
        print(f'获取到 {len(a_stocks)} 只股票进行测试')
        
        # ---------- STEP 2: 获取K线数据 ----------
        print('\n2. 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        kdata = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='获取K线'):
            code = stock['code']
            try:
                # 获取日K线
                rs_day = bs.query_history_k_data_plus(code, 
                    'date,code,open,high,low,close,volume,amount',
                    start_date=start_date, end_date=end_date, frequency='d')
                day_df = rs_day.get_data()
                
                if not day_df.empty:
                    # 转换数据类型
                    day_df['close'] = pd.to_numeric(day_df['close'], errors='coerce')
                    day_df['open'] = pd.to_numeric(day_df['open'], errors='coerce')
                    day_df['volume'] = pd.to_numeric(day_df['volume'], errors='coerce')
                    
                    # 过滤掉无效数据
                    day_df = day_df.dropna()
                    
                    if len(day_df) > 10:  # 确保有足够数据
                        kdata[code] = {
                            'D': day_df,
                            'name': stock['code_name']
                        }
            except Exception as e:
                print(f'获取 {code} 数据失败: {e}')
                continue
        
        print(f'成功获取 {len(kdata)} 只股票的K线数据')
        
        # ---------- STEP 3: 简化的技术分析 ----------
        print('\n3. 进行技术分析...')
        
        def simple_analysis(day_df):
            if day_df.empty or len(day_df) < 10:
                return None
                
            # 日线趋势判断
            day_close = day_df['close'].iloc[-10:]  # 最近10天
            trend_up = day_close.iloc[-1] > day_close.iloc[0]
            
            # 简单MA信号
            current_price = day_close.iloc[-1]
            ma5 = day_close.iloc[-5:].mean()
            ma10 = day_close.iloc[-10:].mean()
            
            # 成交量分析
            recent_vol = day_df['volume'].iloc[-5:].mean()
            prev_vol = day_df['volume'].iloc[-10:-5].mean()
            volume_factor = recent_vol / prev_vol if prev_vol > 0 else 1
            
            signal = '2_buy' if current_price > ma5 > ma10 else 'hold'
            
            return {
                'trend': 'up' if trend_up else 'down',
                'signal': signal,
                'entry_price': float(current_price),
                'stop_loss': float(current_price * 0.95),
                'volume_factor': float(volume_factor),
                'ma5': float(ma5),
                'ma10': float(ma10)
            }
        
        analysis_results = {}
        for code, data in kdata.items():
            result = simple_analysis(data['D'])
            if result:
                analysis_results[code] = {
                    'name': data['name'],
                    'analysis': result
                }
        
        # ---------- STEP 4: 选股过滤 ----------
        print('\n4. 应用选股条件...')
        
        selected_stocks = []
        for code, info in analysis_results.items():
            analysis = info['analysis']
            
            # 过滤条件
            if analysis['trend'] != 'up':
                continue
            if analysis['signal'] not in ('2_buy',):
                continue
            if analysis['volume_factor'] < 1.1:  # 成交量放大
                continue
                
            selected_stocks.append({
                'symbol': code,
                'name': info['name'],
                'entry': analysis['entry_price'],
                'stop': analysis['stop_loss'],
                'signal': analysis['signal'],
                'volume_factor': round(analysis['volume_factor'], 2),
                'trend': analysis['trend']
            })
        
        # ---------- 输出结果 ----------
        print('\n=== 选股结果 ===')
        if selected_stocks:
            for stock in selected_stocks:
                print(f'股票: {stock["symbol"]} ({stock["name"]})')
                print(f'  信号: {stock["signal"]}, 趋势: {stock["trend"]}')
                print(f'  入场价: {stock["entry"]:.2f}, 止损: {stock["stop"]:.2f}')
                print(f'  成交量放大: {stock["volume_factor"]}倍')
                print()
        else:
            print('未找到符合条件的股票')
        
        print(f'\n总计筛选出 {len(selected_stocks)} 只股票')
        
        # 保存结果到JSON
        with open('/Users/yang/selected_stocks.json', 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        print('结果已保存到 selected_stocks.json')

    finally:
        # 登出BaoStock
        bs.logout()
        print('\nBaoStock 已登出')

if __name__ == '__main__':
    main()