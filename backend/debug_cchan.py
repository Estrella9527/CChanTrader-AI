#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader调试版本 - 定位数据类型问题
"""

import pandas as pd
import numpy as np
import baostock as bs
from datetime import datetime, timedelta

def debug_data_types():
    """调试BaoStock数据类型"""
    
    # 登录
    lg = bs.login()
    print(f'登录状态: {lg.error_code}')
    
    try:
        # 获取一只股票数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        rs = bs.query_history_k_data_plus('sh.600000',
            'date,code,open,high,low,close,volume,amount',
            start_date=start_date, end_date=end_date, frequency='d')
        df = rs.get_data()
        
        print(f"原始数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print(f"数据类型:")
        print(df.dtypes)
        print(f"\n前3行数据:")
        print(df.head(3))
        
        # 尝试数据转换
        print(f"\n=== 数据转换测试 ===")
        
        # 检查每列的样本数据
        for col in df.columns:
            if col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                print(f"\n{col}列样本数据:")
                print(df[col].head(3).tolist())
                
                # 尝试转换
                try:
                    converted = pd.to_numeric(df[col], errors='coerce')
                    print(f"{col} 转换成功: {converted.dtype}")
                    print(f"转换后样本: {converted.head(3).tolist()}")
                except Exception as e:
                    print(f"{col} 转换失败: {e}")
        
        # 测试比较操作
        print(f"\n=== 比较操作测试 ===")
        try:
            df_test = df.copy()
            df_test['close'] = pd.to_numeric(df_test['close'], errors='coerce')
            df_test = df_test.dropna(subset=['close'])
            
            print(f"close列类型: {df_test['close'].dtype}")
            print(f"close列样本: {df_test['close'].head(3).tolist()}")
            
            # 测试比较
            result = df_test['close'] > 10
            print(f"比较操作成功: {result.head(3).tolist()}")
            
        except Exception as e:
            print(f"比较操作失败: {e}")
            
        # 测试RSI计算
        print(f"\n=== RSI计算测试 ===")
        try:
            close_prices = pd.to_numeric(df['close'], errors='coerce').dropna()
            print(f"收盘价类型: {close_prices.dtype}")
            
            delta = close_prices.diff()
            print(f"价格变化类型: {delta.dtype}")
            
            gain = delta.where(delta > 0, 0)
            print(f"涨幅类型: {gain.dtype}")
            
            # 这里可能是问题所在
            gain_mean = gain.rolling(window=14).mean()
            print(f"涨幅均值类型: {gain_mean.dtype}")
            
        except Exception as e:
            print(f"RSI计算失败: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        bs.logout()

if __name__ == '__main__':
    debug_data_types()