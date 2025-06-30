#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证股票数据的准确性
"""

import baostock as bs
import pandas as pd
from datetime import datetime

def verify_stock_info():
    """验证股票基本信息"""
    
    lg = bs.login()
    print(f'BaoStock连接状态: {lg.error_code}')
    
    # 需要验证的股票代码
    stocks_to_verify = ['sh.600110', 'sh.600072', 'sh.600036', 'sh.600063', 'sh.600057']
    
    try:
        # 1. 验证股票基本信息
        print('\n=== 验证股票基本信息 ===')
        query_date = '2025-06-23'
        stock_rs = bs.query_all_stock(query_date)
        all_stocks = stock_rs.get_data()
        
        for code in stocks_to_verify:
            stock_info = all_stocks[all_stocks['code'] == code]
            if not stock_info.empty:
                print(f'{code}: {stock_info.iloc[0]["code_name"]} (交易状态: {stock_info.iloc[0]["tradeStatus"]})')
            else:
                print(f'{code}: 未找到股票信息')
        
        # 2. 验证价格数据
        print(f'\n=== 验证{query_date}收盘价数据 ===')
        for code in stocks_to_verify:
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume',
                    start_date='2025-06-20', 
                    end_date=query_date,
                    frequency='d')
                df = rs.get_data()
                
                if not df.empty:
                    latest = df.iloc[-1]
                    print(f'{code}:')
                    print(f'  日期: {latest["date"]}')
                    print(f'  收盘价: {latest["close"]}')
                    print(f'  成交量: {latest["volume"]}')
                    print()
                else:
                    print(f'{code}: 无K线数据')
                    
            except Exception as e:
                print(f'{code}: 数据获取错误 - {e}')
        
        # 3. 检查是否是真实的交易日
        print(f'=== 验证{query_date}是否为交易日 ===')
        # 查询一个确定存在的大盘股
        rs_test = bs.query_history_k_data_plus('sh.000001',  # 上证指数
            'date,code,open,high,low,close',
            start_date='2025-06-20', 
            end_date=query_date,
            frequency='d')
        test_df = rs_test.get_data()
        
        print('最近几个交易日:')
        for _, row in test_df.tail(5).iterrows():
            print(f'  {row["date"]}: 上证指数收盘 {row["close"]}')
            
    finally:
        bs.logout()

if __name__ == '__main__':
    verify_stock_info()