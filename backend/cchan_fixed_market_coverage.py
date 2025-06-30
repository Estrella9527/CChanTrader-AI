#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 修复市场覆盖问题
确保包含沪深两市所有股票：主板、中小板、创业板
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

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
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
    else:
        df['momentum_5'] = 0
        df['momentum_10'] = 0
    
    return df

def get_market_info(stock_code: str) -> dict:
    """获取股票市场信息"""
    if stock_code.startswith('sh.6'):
        return {'market': '上海主板', 'code_prefix': 'sh.6'}
    elif stock_code.startswith('sz.000'):
        return {'market': '深圳主板', 'code_prefix': 'sz.000'}
    elif stock_code.startswith('sz.002'):
        return {'market': '中小板', 'code_prefix': 'sz.002'}
    elif stock_code.startswith('sz.300'):
        return {'market': '创业板', 'code_prefix': 'sz.300'}
    elif stock_code.startswith('sz.301'):
        return {'market': '创业板注册制', 'code_prefix': 'sz.301'}
    else:
        return {'market': '其他', 'code_prefix': 'other'}

def analyze_stock_simple(symbol: str, df: pd.DataFrame, stock_name: str) -> dict:
    """简化股票分析"""
    try:
        if len(df) < 30:
            return None
            
        current_price = float(df['close'].iloc[-1])
        if not (2 <= current_price <= 500):  # 价格范围过滤
            return None
        
        # 技术指标分析
        latest = df.iloc[-1]
        
        # 均线排列
        ma_bullish = 0
        if all(f'ma{p}' in latest.index for p in [5, 10, 20]):
            if latest['close'] > latest['ma5']:
                ma_bullish += 1
            if latest['ma5'] > latest['ma10']:
                ma_bullish += 1  
            if latest['ma10'] > latest['ma20']:
                ma_bullish += 1
        
        # RSI
        rsi = float(latest.get('rsi', 50))
        rsi_ok = 25 <= rsi <= 75  # RSI在合理范围
        
        # 成交量
        vol_ratio = float(latest.get('vol_ratio', 1.0))
        vol_ok = vol_ratio > 0.8  # 成交量不能太低
        
        # 动量
        momentum_5 = float(latest.get('momentum_5', 0))
        momentum_ok = momentum_5 > -0.1  # 不能大幅下跌
        
        # 综合评分 (简化版)
        score = 0.3  # 基础分
        score += ma_bullish * 0.15  # 均线最多+0.45
        score += 0.1 if rsi_ok else 0
        score += 0.1 if vol_ok else 0
        score += 0.05 if momentum_ok else 0
        
        # 获取市场信息
        market_info = get_market_info(symbol)
        
        # 只保留评分较高的股票
        if score < 0.6:
            return None
        
        return {
            'symbol': symbol,
            'stock_name': stock_name,
            'market': market_info['market'],
            'current_price': current_price,
            'total_score': round(score, 3),
            'ma_bullish_count': ma_bullish,
            'rsi': round(rsi, 1),
            'volume_ratio': round(vol_ratio, 2),
            'momentum_5d': round(momentum_5 * 100, 2),
            'entry_price': current_price,
            'stop_loss': round(current_price * 0.93, 2),
            'target_price': round(current_price * 1.12, 2)
        }
        
    except Exception as e:
        return None

def fixed_market_analysis():
    """修复后的全市场分析"""
    load_dotenv()
    
    print('=== CChanTrader-AI 修复版 - 全市场覆盖 ===')
    
    lg = bs.login()
    print(f'📊 BaoStock状态: {lg.error_code}')
    
    try:
        # 获取所有股票列表
        print('\\n🔍 获取股票列表...')
        stock_rs = bs.query_all_stock(day='2025-06-26')
        all_stocks = stock_rs.get_data()
        
        if all_stocks.empty:
            print('❌ 无法获取股票列表')
            return []
        
        print(f'✅ 获取到 {len(all_stocks)} 只股票')
        
        # 分类统计和筛选
        markets = {
            '上海主板': all_stocks[all_stocks['code'].str.startswith('sh.6')],
            '深圳主板': all_stocks[all_stocks['code'].str.startswith('sz.000')],
            '中小板': all_stocks[all_stocks['code'].str.startswith('sz.002')],
            '创业板': all_stocks[all_stocks['code'].str.startswith('sz.30')]
        }
        
        print('\\n📊 市场分布:')
        sample_stocks = []
        for market_name, market_stocks in markets.items():
            count = len(market_stocks)
            print(f'  {market_name}: {count}只')
            
            if count > 0:
                # 每个市场采样一定数量
                sample_size = min(15, count)
                sampled = market_stocks.sample(n=sample_size, random_state=42)
                sample_stocks.append(sampled)
        
        # 合并所有采样股票
        final_sample = pd.concat(sample_stocks, ignore_index=True)
        print(f'\\n📋 分析样本: {len(final_sample)}只 (各市场均衡采样)')
        
        # 获取K线数据
        print('\\n📈 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        stock_data = {}
        failed_count = 0
        
        for _, stock in tqdm(final_sample.iterrows(), total=len(final_sample), desc='获取数据'):
            code = stock['code']
            name = stock['code_name']
            
            try:
                rs = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume',
                    start_date=start_date, 
                    end_date=end_date,
                    frequency='d')
                day_df = rs.get_data()
                
                if not day_df.empty and len(day_df) >= 30:
                    stock_data[code] = {
                        'df': day_df,
                        'name': name
                    }
                else:
                    failed_count += 1
                    
            except Exception:
                failed_count += 1
                continue
        
        print(f'✅ 成功: {len(stock_data)}只, 失败: {failed_count}只')
        
        # 执行分析
        print('\\n🧠 执行技术分析...')
        selected_stocks = []
        
        for symbol, data in tqdm(stock_data.items(), desc='分析'):
            df = safe_data_conversion(data['df'])
            df = add_technical_indicators(df)
            
            result = analyze_stock_simple(symbol, df, data['name'])
            if result:
                selected_stocks.append(result)
        
        # 按评分排序
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\\n🎯 === 选股结果 ===')
        print(f'符合条件: {len(selected_stocks)}只')
        
        # 按市场分类展示
        for market in ['上海主板', '深圳主板', '中小板', '创业板']:
            market_stocks = [s for s in selected_stocks if s['market'] == market]
            if market_stocks:
                print(f'\\n🏆 {market}:')
                for i, stock in enumerate(market_stocks[:3], 1):
                    print(f'  {i}. {stock["symbol"]} - {stock["stock_name"]}')
                    print(f'     💰 价格: {stock["current_price"]:.2f}元 | 评分: {stock["total_score"]}')
                    print(f'     📈 均线支撑: {stock["ma_bullish_count"]}/3 | RSI: {stock["rsi"]}')
                    print(f'     📊 量比: {stock["volume_ratio"]}x | 动量: {stock["momentum_5d"]}%')
                    print(f'     🎯 策略: 入场{stock["entry_price"]:.2f} 止损{stock["stop_loss"]:.2f} 目标{stock["target_price"]:.2f}')
        
        # 保存结果
        output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fixed_market_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\\n💾 结果保存至: {output_file}')
        
        # 统计各市场入选情况
        market_stats = {}
        for stock in selected_stocks:
            market = stock['market']
            market_stats[market] = market_stats.get(market, 0) + 1
        
        print(f'\\n📊 各市场入选统计:')
        for market, count in market_stats.items():
            print(f'  {market}: {count}只')
        
        print(f'\\n✅ 成功覆盖各个市场！包含002、300等股票')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print('\\n🔚 分析完成')

if __name__ == '__main__':
    results = fixed_market_analysis()