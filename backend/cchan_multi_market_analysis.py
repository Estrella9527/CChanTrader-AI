#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 全市场股票分析
修正市场覆盖问题，包含沪深两市所有板块
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
        return {'market': '上海主板', 'type': 'main_board', 'exchange': 'SSE'}
    elif stock_code.startswith('sz.000'):
        return {'market': '深圳主板', 'type': 'main_board', 'exchange': 'SZSE'}
    elif stock_code.startswith('sz.002'):
        return {'market': '中小板', 'type': 'sme_board', 'exchange': 'SZSE'}
    elif stock_code.startswith('sz.300'):
        return {'market': '创业板', 'type': 'growth_board', 'exchange': 'SZSE'}
    elif stock_code.startswith('sz.301'):
        return {'market': '创业板', 'type': 'growth_board', 'exchange': 'SZSE'}
    else:
        return {'market': '其他', 'type': 'other', 'exchange': 'OTHER'}

def analyze_stock_comprehensive(symbol: str, df: pd.DataFrame) -> dict:
    """综合股票分析"""
    try:
        if len(df) < 30:
            return None
            
        current_price = float(df['close'].iloc[-1])
        if not (2 <= current_price <= 300):
            return None
        
        # 技术指标分析
        latest = df.iloc[-1]
        
        # 均线排列
        ma_status = 'neutral'
        if all(f'ma{p}' in latest.index for p in [5, 10, 20]):
            ma5, ma10, ma20 = latest['ma5'], latest['ma10'], latest['ma20']
            if current_price > ma5 > ma10 > ma20:
                ma_status = 'strong_bullish'
            elif current_price > ma5 > ma10:
                ma_status = 'bullish'
            elif current_price < ma5 < ma10 < ma20:
                ma_status = 'bearish'
            elif current_price < ma5 < ma10:
                ma_status = 'weak_bearish'
        
        # RSI分析
        rsi = float(latest.get('rsi', 50))
        rsi_status = 'oversold' if rsi < 30 else 'overbought' if rsi > 75 else 'normal'
        
        # 成交量分析
        vol_ratio = float(latest.get('vol_ratio', 1.0))
        vol_status = 'high' if vol_ratio > 2.0 else 'normal' if vol_ratio > 0.8 else 'low'
        
        # 动量分析
        momentum_5 = float(latest.get('momentum_5', 0))
        momentum_10 = float(latest.get('momentum_10', 0))
        momentum_status = 'strong' if momentum_5 > 0.05 else 'moderate' if momentum_5 > 0.02 else 'weak'
        
        # 波动率
        volatility = float(df['close'].pct_change().tail(20).std())
        vol_level = 'high' if volatility > 0.05 else 'normal' if volatility > 0.02 else 'low'
        
        # 综合评分
        score = 0.5
        
        # 技术面评分 (40%)
        ma_scores = {'strong_bullish': 0.20, 'bullish': 0.15, 'neutral': 0.08, 'weak_bearish': 0.03, 'bearish': 0}
        score += ma_scores.get(ma_status, 0)
        
        # RSI评分 (20%)
        rsi_scores = {'normal': 0.20, 'oversold': 0.15, 'overbought': 0.05}
        score += rsi_scores.get(rsi_status, 0)
        
        # 成交量评分 (20%)
        vol_scores = {'high': 0.20, 'normal': 0.15, 'low': 0.05}
        score += vol_scores.get(vol_status, 0)
        
        # 动量评分 (15%)
        momentum_scores = {'strong': 0.15, 'moderate': 0.10, 'weak': 0.05}
        score += momentum_scores.get(momentum_status, 0)
        
        # 波动率评分 (5%) - 适中的波动率更好
        vol_scores_dict = {'normal': 0.05, 'low': 0.03, 'high': 0.01}
        score += vol_scores_dict.get(vol_level, 0)
        
        # 获取市场信息
        market_info = get_market_info(symbol)
        
        # 只返回评分较高的股票
        if score < 0.7:
            return None
        
        return {
            'symbol': symbol,
            'market': market_info['market'],
            'market_type': market_info['type'],
            'exchange': market_info['exchange'],
            'current_price': current_price,
            'total_score': round(score, 3),
            
            # 技术指标
            'ma_status': ma_status,
            'rsi': round(rsi, 1),
            'rsi_status': rsi_status,
            'volume_ratio': round(vol_ratio, 2),
            'volume_status': vol_status,
            'momentum_5d': round(momentum_5 * 100, 2),
            'momentum_10d': round(momentum_10 * 100, 2),
            'momentum_status': momentum_status,
            'volatility': round(volatility * 100, 2),
            'volatility_level': vol_level,
            
            # 交易建议
            'entry_price': current_price,
            'stop_loss': round(current_price * 0.92, 2),
            'target_price': round(current_price * 1.15, 2),
            'confidence': 'high' if score > 0.85 else 'medium'
        }
        
    except Exception as e:
        return None

def multi_market_analysis():
    """全市场股票分析"""
    load_dotenv()
    
    print('=== CChanTrader-AI 全市场股票分析 ===')
    print('🎯 覆盖沪深两市所有板块：主板、中小板、创业板')
    
    lg = bs.login()
    print(f'📊 BaoStock连接状态: {lg.error_code}')
    
    try:
        # 获取所有股票列表
        print('\\n🔍 获取全市场股票列表...')
        stock_rs = bs.query_all_stock()
        all_stocks = stock_rs.get_data()
        
        print(f'📊 市场覆盖统计:')
        sh_count = len(all_stocks[all_stocks['code'].str.startswith('sh.')])
        sz_main = len(all_stocks[all_stocks['code'].str.contains('sz.000')])
        sz_sme = len(all_stocks[all_stocks['code'].str.contains('sz.002')])
        sz_growth = len(all_stocks[all_stocks['code'].str.contains('sz.30')])
        
        print(f'  上海主板: {sh_count}只')
        print(f'  深圳主板: {sz_main}只')
        print(f'  中小板: {sz_sme}只')
        print(f'  创业板: {sz_growth}只')
        print(f'  总计: {len(all_stocks)}只')
        
        # 均衡采样各个板块
        sample_stocks = []
        
        # 上海主板 (sh.6)
        sh_stocks = all_stocks[all_stocks['code'].str.contains('sh.6')].sample(n=min(30, len(all_stocks[all_stocks['code'].str.contains('sh.6')])), random_state=42)
        sample_stocks.append(sh_stocks)
        
        # 深圳主板 (sz.000) 
        sz_main_stocks = all_stocks[all_stocks['code'].str.contains('sz.000')].sample(n=min(20, len(all_stocks[all_stocks['code'].str.contains('sz.000')])), random_state=42)
        sample_stocks.append(sz_main_stocks)
        
        # 中小板 (sz.002)
        sme_stocks = all_stocks[all_stocks['code'].str.contains('sz.002')].sample(n=min(20, len(all_stocks[all_stocks['code'].str.contains('sz.002')])), random_state=42)
        sample_stocks.append(sme_stocks)
        
        # 创业板 (sz.30)
        growth_stocks = all_stocks[all_stocks['code'].str.contains('sz.30')].sample(n=min(20, len(all_stocks[all_stocks['code'].str.contains('sz.30')])), random_state=42)
        sample_stocks.append(growth_stocks)
        
        # 合并样本
        sample_df = pd.concat(sample_stocks, ignore_index=True)
        print(f'\\n📋 分析样本: {len(sample_df)}只 (均衡覆盖各板块)')
        
        # 获取K线数据
        print('\\n📈 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        stock_data = {}
        for _, stock in tqdm(sample_df.iterrows(), total=len(sample_df), desc='获取数据'):
            code = stock['code']
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
                        'name': stock['code_name']
                    }
                    
            except Exception:
                continue
        
        print(f'✅ 获取到 {len(stock_data)} 只股票数据')
        
        # 执行分析
        print('\\n🧠 执行技术分析...')
        selected_stocks = []
        
        for symbol, data in tqdm(stock_data.items(), desc='技术分析'):
            df = safe_data_conversion(data['df'])
            df = add_technical_indicators(df)
            
            result = analyze_stock_comprehensive(symbol, df)
            if result:
                result['stock_name'] = data['name']
                selected_stocks.append(result)
        
        # 按评分和市场分类
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\\n🎯 === 全市场选股结果 ===')
        print(f'符合条件股票: {len(selected_stocks)}只')
        
        # 按市场分类展示
        markets = ['上海主板', '深圳主板', '中小板', '创业板']
        
        for market in markets:
            market_stocks = [s for s in selected_stocks if s['market'] == market]
            if market_stocks:
                print(f'\\n🏆 {market} 推荐股票:')
                for i, stock in enumerate(market_stocks[:3], 1):
                    print(f'  {i}. {stock["symbol"]} ({stock["stock_name"]})')
                    print(f'     💰 价格: {stock["current_price"]:.2f}元 | 评分: {stock["total_score"]}')
                    print(f'     📈 技术: {stock["ma_status"]} | RSI: {stock["rsi"]} | 量比: {stock["volume_ratio"]}x')
                    print(f'     ⚡ 动量: 5日{stock["momentum_5d"]}% | 10日{stock["momentum_10d"]}%')
                    print(f'     🎯 建议: 入场{stock["entry_price"]:.2f} 止损{stock["stop_loss"]:.2f} 目标{stock["target_price"]:.2f}')
                    print()
        
        # 保存结果
        output_file = '/Users/yang/multi_market_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'💾 详细结果已保存至: {output_file}')
        
        # 统计各市场分布
        market_stats = {}
        for stock in selected_stocks:
            market = stock['market']
            market_stats[market] = market_stats.get(market, 0) + 1
        
        print(f'\\n📊 入选股票市场分布:')
        for market, count in market_stats.items():
            print(f'  {market}: {count}只')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print('\\n🔚 分析完成')

if __name__ == '__main__':
    results = multi_market_analysis()