#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 实时竞价监控模块
实时获取和分析集合竞价数据，支持开盘前决策
"""

import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

class RealTimeAuctionMonitor:
    """实时竞价监控器"""
    
    def __init__(self, watch_list: list = None):
        self.watch_list = watch_list or []
        self.auction_history = {}
        self.signals = {}
        self.is_auction_time = False
        
    def add_stock(self, symbol: str):
        """添加监控股票"""
        if symbol not in self.watch_list:
            self.watch_list.append(symbol)
            print(f"✅ 已添加 {symbol} 到监控列表")
    
    def remove_stock(self, symbol: str):
        """移除监控股票"""
        if symbol in self.watch_list:
            self.watch_list.remove(symbol)
            print(f"❌ 已移除 {symbol} 从监控列表")
    
    def check_auction_time(self) -> bool:
        """检查是否为竞价时间"""
        now = datetime.now()
        current_time = now.time()
        
        # 9:15-9:25为集合竞价时间
        auction_start = datetime.strptime("09:15", "%H:%M").time()
        auction_end = datetime.strptime("09:25", "%H:%M").time()
        
        # 检查是否为交易日（简化版，实际应该检查节假日）
        weekday = now.weekday()
        is_trading_day = weekday < 5  # 周一到周五
        
        self.is_auction_time = (is_trading_day and 
                               auction_start <= current_time <= auction_end)
        
        return self.is_auction_time
    
    def get_realtime_auction_data(self, symbol: str) -> dict:
        """获取实时竞价数据"""
        try:
            if not self.check_auction_time():
                return {'status': 'not_auction_time', 'data': None}
            
            # 获取竞价数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00", 
                end_time="09:30:00"
            )
            
            if pre_market_df.empty:
                return {'status': 'no_data', 'data': None}
            
            # 筛选当前时间之前的竞价数据
            current_time = datetime.now().strftime("%H:%M")
            auction_df = pre_market_df[
                pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]')
            ]
            
            # 只要在9:15之后有数据的
            auction_df = auction_df[auction_df['时间'] <= current_time]
            
            if auction_df.empty:
                return {'status': 'no_current_data', 'data': None}
            
            return {
                'status': 'success',
                'data': auction_df,
                'latest_time': auction_df.iloc[-1]['时间'],
                'latest_price': float(auction_df.iloc[-1]['开盘']),
                'total_volume': auction_df['成交量'].sum()
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'data': None}
    
    def analyze_auction_signals(self, symbol: str, auction_data: dict, prev_close: float) -> dict:
        """分析竞价信号"""
        if auction_data['status'] != 'success':
            return self._get_default_auction_analysis()
        
        try:
            df = auction_data['data']
            latest_price = auction_data['latest_price']
            
            # 1. 竞价趋势
            prices = df['开盘'].astype(float).values
            if len(prices) >= 3:
                trend_slope = np.polyfit(range(len(prices)), prices, 1)[0]
                price_trend = "上升" if trend_slope > 0 else "下降" if trend_slope < 0 else "平稳"
            else:
                price_trend = "数据不足"
            
            # 2. 竞价比率
            auction_ratio = (latest_price - prev_close) / prev_close * 100
            
            # 3. 成交量分析
            total_volume = auction_data['total_volume']
            early_volume = df[df['时间'].str.contains('09:1[5-9]')]['成交量'].sum()
            late_volume = df[df['时间'].str.contains('09:2[0-5]')]['成交量'].sum()
            
            # 4. 资金坚决性 (后期成交占比)
            capital_determination = late_volume / (total_volume + 1e-10)
            
            # 5. 价格波动
            high_price = df['最高'].astype(float).max()
            low_price = df['最低'].astype(float).min()
            price_volatility = (high_price - low_price) / prev_close * 100
            
            # 6. 信号强度评估
            signal_strength = self._evaluate_signal_strength(
                auction_ratio, capital_determination, price_volatility, total_volume
            )
            
            # 7. 交易建议
            recommendation = self._generate_recommendation(
                auction_ratio, signal_strength, price_trend, capital_determination
            )
            
            return {
                'symbol': symbol,
                'latest_price': latest_price,
                'prev_close': prev_close,
                'auction_ratio': round(auction_ratio, 2),
                'price_trend': price_trend,
                'total_volume': total_volume,
                'capital_determination': round(capital_determination, 3),
                'price_volatility': round(price_volatility, 2),
                'signal_strength': round(signal_strength, 3),
                'recommendation': recommendation,
                'update_time': auction_data['latest_time'],
                'analysis_time': datetime.now().strftime("%H:%M:%S")
            }
            
        except Exception as e:
            return self._get_default_auction_analysis()
    
    def _evaluate_signal_strength(self, auction_ratio: float, capital_determination: float,
                                price_volatility: float, volume: float) -> float:
        """评估信号强度"""
        strength = 0.5
        
        # 温和高开加分
        if 0.5 <= auction_ratio <= 3:
            strength += 0.25
        elif auction_ratio > 3:
            strength -= 0.1  # 过度高开扣分
        
        # 资金坚决性
        if capital_determination > 0.6:
            strength += 0.2
        
        # 价格稳定性
        if price_volatility < 3:
            strength += 0.15
        elif price_volatility > 8:
            strength -= 0.1
        
        # 成交量活跃度
        if volume > 0:
            strength += 0.1
        
        return max(0, min(1, strength))
    
    def _generate_recommendation(self, auction_ratio: float, signal_strength: float,
                               price_trend: str, capital_determination: float) -> str:
        """生成交易建议"""
        if auction_ratio > 5:
            return "⚠️ 高开过度，建议等待回踩"
        elif auction_ratio > 2 and signal_strength > 0.7 and price_trend == "上升":
            return "🚀 温和高开+强信号，建议开盘买入"
        elif -1 <= auction_ratio <= 2 and signal_strength > 0.6:
            return "✅ 竞价信号良好，可考虑买入"
        elif auction_ratio < -3:
            return "📉 低开较多，建议等待企稳"
        elif capital_determination > 0.7:
            return "💪 资金坚决，可关注买入时机"
        else:
            return "👀 竞价信号一般，建议观望"
    
    def _get_default_auction_analysis(self) -> dict:
        """默认分析结果"""
        return {
            'symbol': '',
            'latest_price': 0,
            'prev_close': 0,
            'auction_ratio': 0,
            'price_trend': '无数据',
            'total_volume': 0,
            'capital_determination': 0,
            'price_volatility': 0,
            'signal_strength': 0,
            'recommendation': '数据获取失败',
            'update_time': '无',
            'analysis_time': datetime.now().strftime("%H:%M:%S")
        }
    
    def monitor_watch_list(self, prev_close_prices: dict) -> dict:
        """监控观察列表"""
        results = {}
        
        print(f"\n🔍 开始监控 {len(self.watch_list)} 只股票...")
        print(f"⏰ 当前时间: {datetime.now().strftime('%H:%M:%S')}")
        
        if not self.check_auction_time():
            print("⏰ 当前不是竞价时间 (9:15-9:25)")
            return results
        
        print("🎯 正在竞价时间，开始实时分析...")
        
        for symbol in self.watch_list:
            prev_close = prev_close_prices.get(symbol, 0)
            if prev_close == 0:
                print(f"❌ {symbol}: 缺少前收盘价数据")
                continue
            
            # 获取竞价数据
            auction_data = self.get_realtime_auction_data(symbol)
            
            # 分析信号
            analysis = self.analyze_auction_signals(symbol, auction_data, prev_close)
            results[symbol] = analysis
            
            # 显示结果
            self._display_analysis(analysis)
        
        return results
    
    def _display_analysis(self, analysis: dict):
        """显示分析结果"""
        symbol = analysis['symbol']
        print(f"\n📊 {symbol} 竞价分析:")
        print(f"   💰 当前价格: {analysis['latest_price']:.2f}元")
        print(f"   📈 竞价比率: {analysis['auction_ratio']:+.2f}%")
        print(f"   📊 价格趋势: {analysis['price_trend']}")
        print(f"   💎 资金坚决度: {analysis['capital_determination']:.3f}")
        print(f"   ⚡ 信号强度: {analysis['signal_strength']:.3f}")
        print(f"   🎯 建议: {analysis['recommendation']}")
        print(f"   ⏰ 更新时间: {analysis['update_time']}")
    
    def save_analysis_history(self, results: dict, filename: str = None):
        """保存分析历史"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/Users/yang/auction_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存: {filename}")
    
    def continuous_monitor(self, prev_close_prices: dict, interval: int = 30):
        """持续监控模式"""
        print("🔄 启动持续监控模式...")
        print(f"📊 监控间隔: {interval}秒")
        print("📝 按 Ctrl+C 停止监控")
        
        try:
            while True:
                if self.check_auction_time():
                    results = self.monitor_watch_list(prev_close_prices)
                    
                    # 保存当前分析
                    timestamp = datetime.now().strftime("%H%M%S")
                    self.save_analysis_history(results, 
                        f"/Users/yang/auction_monitor_{timestamp}.json")
                    
                    time.sleep(interval)
                else:
                    print(f"⏰ 非竞价时间，等待下一个检查周期...")
                    time.sleep(60)  # 非竞价时间延长检查间隔
                    
        except KeyboardInterrupt:
            print("\n🛑 监控已停止")

# 使用示例
if __name__ == "__main__":
    # 创建监控器
    monitor = RealTimeAuctionMonitor()
    
    # 添加监控股票
    watch_stocks = ["000001", "600000", "000002", "300015"]
    for stock in watch_stocks:
        monitor.add_stock(stock)
    
    # 模拟前收盘价 (实际使用时应该从数据库或API获取)
    prev_close_prices = {
        "000001": 12.50,
        "600000": 13.60,
        "000002": 25.80,
        "300015": 12.38
    }
    
    print("=== CChanTrader-AI 实时竞价监控 ===")
    
    # 单次监控
    results = monitor.monitor_watch_list(prev_close_prices)
    
    if results:
        # 汇总显示
        print(f"\n📋 === 监控汇总 ===")
        high_potential = [s for s, r in results.items() if r['signal_strength'] > 0.7]
        if high_potential:
            print(f"🌟 高潜力股票: {', '.join(high_potential)}")
        
        # 保存结果
        monitor.save_analysis_history(results)
    
    # 如果需要持续监控，取消下面注释
    # monitor.continuous_monitor(prev_close_prices, interval=30)