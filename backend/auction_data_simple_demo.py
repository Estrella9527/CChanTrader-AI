#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股集合竞价数据获取简化演示程序
展示AKShare和BaoStock的核心功能
"""

import akshare as ak
import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def test_akshare_auction_data():
    """测试AKShare集合竞价数据获取"""
    print("🔥 测试AKShare集合竞价数据获取")
    print("=" * 50)
    
    test_stocks = ["000001", "600000", "300015"]
    
    for symbol in test_stocks:
        print(f"\n📊 获取 {symbol} 的集合竞价数据:")
        
        try:
            # 获取盘前分钟数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00",
                end_time="09:30:00"
            )
            
            if not pre_market_df.empty:
                # 筛选集合竞价时间段 (9:15-9:25)
                auction_df = pre_market_df[
                    pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]', na=False)
                ]
                
                if not auction_df.empty:
                    # 分析竞价数据
                    opening_price = auction_df['收盘'].iloc[-1]
                    first_price = auction_df['收盘'].iloc[0]
                    total_volume = auction_df['成交量'].sum()
                    price_high = auction_df['最高'].max()
                    price_low = auction_df['最低'].min()
                    trend_pct = (opening_price - first_price) / first_price * 100
                    
                    print(f"  ✅ 成功获取竞价数据 ({len(auction_df)}条记录)")
                    print(f"  📈 开盘价: {opening_price:.2f}")
                    print(f"  📊 竞价趋势: {trend_pct:+.2f}%")
                    print(f"  🔄 成交量: {total_volume:,} 手")
                    print(f"  📏 价格区间: {price_low:.2f} - {price_high:.2f}")
                    
                    # 显示竞价过程
                    print(f"  ⏰ 竞价时间序列:")
                    for _, row in auction_df.head(3).iterrows():
                        time_str = row['时间'].split()[1]
                        print(f"    {time_str}: {row['收盘']:.2f}")
                    if len(auction_df) > 3:
                        print(f"    ... (共{len(auction_df)}个时间点)")
                else:
                    print(f"  ⚠️ 当前无集合竞价数据")
            else:
                print(f"  ❌ 无盘前数据")
                
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")

def test_baostock_opening_data():
    """测试BaoStock开盘价数据获取"""
    print("\n\n🔥 测试BaoStock开盘价数据获取")
    print("=" * 50)
    
    # 登录BaoStock
    lg = bs.login()
    print(f"BaoStock登录: {lg.error_msg}")
    
    if lg.error_code == '0':
        test_stocks = ["sz.000001", "sh.600000", "sz.300015"]
        
        for symbol in test_stocks:
            print(f"\n📈 获取 {symbol} 的开盘价数据:")
            
            try:
                # 获取最近几天的K线数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                
                rs = bs.query_history_k_data_plus(
                    symbol,
                    "date,code,open,high,low,close,preclose,volume,amount,pctChg",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="3"
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    
                    # 数据类型转换
                    numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'pctChg']
                    for col in numeric_cols:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df = df.dropna().tail(5)
                    
                    if not df.empty:
                        print(f"  ✅ 成功获取数据 ({len(df)}条记录)")
                        
                        # 显示最近几天的开盘价
                        print(f"  📅 最近开盘价数据:")
                        for _, row in df.tail(3).iterrows():
                            gap_pct = 0
                            if _ > 0:
                                prev_close = df.iloc[_-1]['close']
                                gap_pct = (row['open'] - prev_close) / prev_close * 100
                            
                            print(f"    {row['date']}: 开盘{row['open']:.2f}, "
                                  f"收盘{row['close']:.2f}, "
                                  f"缺口{gap_pct:+.2f}%")
                    else:
                        print(f"  ❌ 数据为空")
                else:
                    print(f"  ❌ 未获取到数据")
                    
            except Exception as e:
                print(f"  ❌ 获取失败: {e}")
        
        # 登出
        bs.logout()
        print("\nBaoStock已登出")

def analyze_auction_signals():
    """分析集合竞价信号示例"""
    print("\n\n🔥 集合竞价信号分析示例")
    print("=" * 50)
    
    symbol = "000001"
    print(f"\n🎯 分析 {symbol} 的集合竞价信号:")
    
    try:
        # 获取集合竞价数据
        pre_market_df = ak.stock_zh_a_hist_pre_min_em(
            symbol=symbol,
            start_time="09:00:00",
            end_time="09:30:00"
        )
        
        if not pre_market_df.empty:
            auction_df = pre_market_df[
                pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]', na=False)
            ]
            
            if not auction_df.empty:
                # 计算关键指标
                opening_price = auction_df['收盘'].iloc[-1]
                first_price = auction_df['收盘'].iloc[0]
                total_volume = auction_df['成交量'].sum()
                price_high = auction_df['最高'].max()
                price_low = auction_df['最低'].min()
                trend_pct = (opening_price - first_price) / first_price * 100
                volatility_pct = (price_high - price_low) / opening_price * 100
                
                print(f"📊 竞价数据分析:")
                print(f"  开盘价: {opening_price:.2f}")
                print(f"  价格趋势: {trend_pct:+.2f}%")
                print(f"  价格波动: {volatility_pct:.2f}%")
                print(f"  成交量: {total_volume:,} 手")
                print(f"  价格区间: {price_low:.2f} - {price_high:.2f}")
                
                # 生成交易信号
                print(f"\n🚦 交易信号分析:")
                
                # 趋势信号
                if trend_pct > 1:
                    trend_signal = "强烈看涨"
                elif trend_pct > 0.2:
                    trend_signal = "看涨"
                elif trend_pct < -1:
                    trend_signal = "强烈看跌"
                elif trend_pct < -0.2:
                    trend_signal = "看跌"
                else:
                    trend_signal = "中性"
                
                # 成交量信号
                if total_volume > 10000:
                    volume_signal = "高成交量"
                elif total_volume > 5000:
                    volume_signal = "中等成交量"
                else:
                    volume_signal = "低成交量"
                
                # 波动率信号
                if volatility_pct > 2:
                    volatility_signal = "高波动"
                elif volatility_pct > 1:
                    volatility_signal = "中等波动"
                else:
                    volatility_signal = "低波动"
                
                print(f"  趋势信号: {trend_signal}")
                print(f"  成交量信号: {volume_signal}")
                print(f"  波动率信号: {volatility_signal}")
                
                # 综合建议
                bullish_count = sum([
                    trend_pct > 0.5,
                    total_volume > 5000,
                    volatility_pct < 3  # 适度波动
                ])
                
                if bullish_count >= 2:
                    recommendation = "建议关注 (偏多)"
                elif trend_pct < -0.5:
                    recommendation = "谨慎观望 (偏空)"
                else:
                    recommendation = "中性持有"
                
                print(f"  💡 交易建议: {recommendation}")
                
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    """主函数"""
    print("🚀 A股集合竞价数据获取与分析完整演示")
    print("=" * 60)
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试AKShare集合竞价数据
    test_akshare_auction_data()
    
    # 2. 测试BaoStock开盘价数据
    test_baostock_opening_data()
    
    # 3. 分析集合竞价信号
    analyze_auction_signals()
    
    print("\n" + "=" * 60)
    print("🎉 演示程序执行完成！")
    print("\n📝 总结:")
    print("✅ AKShare: 提供详细的集合竞价过程数据，包含分钟级价格变化")
    print("✅ BaoStock: 提供稳定的日级开盘价和历史数据，适合缺口分析")
    print("✅ 双数据源策略: 互相验证，提高数据可靠性")
    print("✅ 信号分析: 基于竞价数据生成交易信号和投资建议")
    
    print("\n🔧 实际应用建议:")
    print("1. 在交易日9:15-9:25期间实时监控集合竞价数据")
    print("2. 结合成交量和价格趋势判断市场情绪")
    print("3. 利用开盘缺口制定日内交易策略")
    print("4. 将竞价信号集成到量化交易系统中")

if __name__ == "__main__":
    main()