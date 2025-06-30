#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 竞价数据增强版
在原有算法基础上集成集合竞价分析，提高选股精确度
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
import akshare as ak
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

class AuctionDataAnalyzer:
    """集合竞价数据分析器"""
    
    def get_auction_data(self, symbol: str) -> pd.DataFrame:
        """获取集合竞价数据"""
        try:
            # 使用AKShare获取竞价数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00", 
                end_time="09:30:00"
            )
            
            if pre_market_df.empty:
                return pd.DataFrame()
            
            # 筛选集合竞价时间段
            auction_df = pre_market_df[
                pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]')
            ].copy()
            
            return auction_df
            
        except Exception:
            return pd.DataFrame()
    
    def calculate_auction_signals(self, symbol: str, prev_close: float) -> dict:
        """计算集合竞价信号"""
        auction_df = self.get_auction_data(symbol)
        
        if auction_df.empty:
            return self._get_default_signals()
        
        try:
            # 获取最终竞价价格
            final_price = float(auction_df.iloc[-1]['开盘'])
            auction_volume = auction_df['成交量'].sum()
            
            # 1. 竞价比率
            auction_ratio = (final_price - prev_close) / prev_close * 100
            
            # 2. 竞价强度
            high_price = auction_df['最高'].max()
            low_price = auction_df['最低'].min()
            price_range = (high_price - low_price) / prev_close * 100
            
            # 3. 资金流向 (后期交易占比)
            early_vol = auction_df[auction_df['时间'].str.contains('09:1[5-9]')]['成交量'].sum()
            late_vol = auction_df[auction_df['时间'].str.contains('09:2[0-5]')]['成交量'].sum()
            capital_bias = late_vol / (early_vol + late_vol + 1e-10)
            
            # 4. 价格趋势
            prices = auction_df['开盘'].values
            if len(prices) >= 3:
                trend_slope = np.polyfit(range(len(prices)), prices, 1)[0]
                price_trend = trend_slope / prices[0] * 100
            else:
                price_trend = 0
            
            # 5. 缺口类型
            gap_type = self._classify_gap(auction_ratio)
            
            # 6. 综合信号强度
            signal_strength = self._calculate_signal_strength(
                auction_ratio, capital_bias, price_range, auction_volume
            )
            
            return {
                'auction_ratio': round(auction_ratio, 2),
                'price_range': round(price_range, 2),
                'capital_bias': round(capital_bias, 3),
                'price_trend': round(price_trend, 2),
                'gap_type': gap_type,
                'auction_volume': auction_volume,
                'signal_strength': round(signal_strength, 3),
                'final_price': final_price
            }
            
        except Exception:
            return self._get_default_signals()
    
    def _classify_gap(self, auction_ratio: float) -> str:
        """分类缺口类型"""
        if auction_ratio > 3:
            return "high_gap_up"
        elif auction_ratio > 1:
            return "gap_up"
        elif auction_ratio > -1:
            return "flat"
        elif auction_ratio > -3:
            return "gap_down"
        else:
            return "low_gap_down"
    
    def _calculate_signal_strength(self, auction_ratio: float, capital_bias: float,
                                 price_range: float, volume: float) -> float:
        """计算信号强度"""
        strength = 0.5
        
        # 温和高开加分
        if 0.5 <= auction_ratio <= 3:
            strength += 0.2 * (auction_ratio / 3)
        
        # 资金后期坚决性
        strength += 0.2 * capital_bias
        
        # 价格稳定性
        if price_range < 5:
            strength += 0.1
        
        # 成交量活跃度
        if volume > 0:
            strength += 0.1
        
        return max(0, min(1, strength))
    
    def _get_default_signals(self) -> dict:
        """默认信号值"""
        return {
            'auction_ratio': 0,
            'price_range': 0,
            'capital_bias': 0,
            'price_trend': 0,
            'gap_type': 'no_data',
            'auction_volume': 0,
            'signal_strength': 0.3,
            'final_price': 0
        }

class EnhancedCChanTrader:
    """增强版CChanTrader（集成竞价数据）"""
    
    def __init__(self):
        self.auction_analyzer = AuctionDataAnalyzer()
    
    def safe_data_conversion(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据安全转换"""
        df = df.copy()
        
        basic_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in basic_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.split().str[0]
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['high', 'low', 'close'])
        df = df[(df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
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
        
        # 成交量指标
        if len(df) >= 20:
            df['vol_ma'] = df['volume'].rolling(20).mean()
            df['vol_ratio'] = df['volume'] / (df['vol_ma'] + 1e-10)
        
        # 动量
        if len(df) >= 10:
            df['momentum_5'] = df['close'].pct_change(5)
            df['momentum_10'] = df['close'].pct_change(10)
        
        return df
    
    def analyze_stock_with_auction(self, symbol: str, df: pd.DataFrame, stock_name: str) -> dict:
        """结合竞价数据的股票分析"""
        try:
            if len(df) < 30:
                return None
            
            current_price = float(df['close'].iloc[-1])
            prev_close = float(df['close'].iloc[-2])
            
            # 基础价格过滤
            if not (2 <= current_price <= 300):
                return None
            
            # 技术分析
            latest = df.iloc[-1]
            tech_score = self._calculate_tech_score(df, latest)
            
            # 竞价分析
            auction_signals = self.auction_analyzer.calculate_auction_signals(symbol, prev_close)
            auction_score = auction_signals['signal_strength']
            
            # 综合评分：技术分析65% + 竞价分析35%
            base_score = tech_score * 0.65 + auction_score * 0.35
            
            # 竞价增强调整
            auction_bonus = self._calculate_auction_bonus(auction_signals)
            total_score = base_score + auction_bonus
            
            # 筛选条件
            if total_score < 0.65:
                return None
            
            # 获取市场信息
            market_info = self._get_market_info(symbol)
            
            return {
                'symbol': symbol,
                'stock_name': stock_name,
                'market': market_info['market'],
                'current_price': current_price,
                'total_score': round(total_score, 3),
                'tech_score': round(tech_score, 3),
                'auction_score': round(auction_score, 3),
                
                # 技术指标
                'rsi': round(latest.get('rsi', 50), 1),
                'volume_ratio': round(latest.get('vol_ratio', 1.0), 2),
                'momentum_5d': round(latest.get('momentum_5', 0) * 100, 2),
                
                # 竞价数据
                'auction_ratio': auction_signals['auction_ratio'],
                'gap_type': auction_signals['gap_type'],
                'capital_bias': auction_signals['capital_bias'],
                'price_trend': auction_signals['price_trend'],
                'auction_volume': auction_signals['auction_volume'],
                
                # 交易建议
                'entry_price': current_price,
                'stop_loss': round(current_price * 0.92, 2),
                'target_price': round(current_price * 1.15, 2),
                'confidence': self._determine_confidence(total_score, auction_signals),
                'strategy': self._generate_strategy(auction_signals)
            }
            
        except Exception as e:
            return None
    
    def _calculate_tech_score(self, df: pd.DataFrame, latest: pd.Series) -> float:
        """计算技术分析得分"""
        score = 0.5
        
        try:
            # 均线排列
            if all(f'ma{p}' in latest.index for p in [5, 10, 20]):
                ma_bullish = 0
                if latest['close'] > latest['ma5']:
                    ma_bullish += 1
                if latest['ma5'] > latest['ma10']:
                    ma_bullish += 1
                if latest['ma10'] > latest['ma20']:
                    ma_bullish += 1
                score += ma_bullish * 0.1
            
            # RSI合理区间
            rsi = latest.get('rsi', 50)
            if 30 <= rsi <= 70:
                score += 0.15
            
            # 成交量
            vol_ratio = latest.get('vol_ratio', 1.0)
            if vol_ratio > 0.8:
                score += 0.1
            
            # 动量
            momentum = latest.get('momentum_5', 0)
            if momentum > 0:
                score += 0.05
            
        except Exception:
            pass
        
        return min(1.0, score)
    
    def _calculate_auction_bonus(self, auction_signals: dict) -> float:
        """计算竞价加分项"""
        bonus = 0
        
        # 温和高开且资金坚决
        if (auction_signals['gap_type'] == 'gap_up' and 
            auction_signals['capital_bias'] > 0.6):
            bonus += 0.1
        
        # 平开但竞价强势
        if (auction_signals['gap_type'] == 'flat' and 
            auction_signals['signal_strength'] > 0.7):
            bonus += 0.08
        
        # 价格趋势向上
        if auction_signals['price_trend'] > 0.5:
            bonus += 0.05
        
        # 有成交量支撑
        if auction_signals['auction_volume'] > 0:
            bonus += 0.03
        
        return bonus
    
    def _get_market_info(self, symbol: str) -> dict:
        """获取市场信息"""
        if symbol.startswith('sh.6'):
            return {'market': '上海主板'}
        elif symbol.startswith('sz.000'):
            return {'market': '深圳主板'}
        elif symbol.startswith('sz.002'):
            return {'market': '中小板'}
        elif symbol.startswith('sz.30'):
            return {'market': '创业板'}
        else:
            return {'market': '其他'}
    
    def _determine_confidence(self, total_score: float, auction_signals: dict) -> str:
        """确定信心等级"""
        if total_score > 0.85 and auction_signals['signal_strength'] > 0.7:
            return 'very_high'
        elif total_score > 0.75:
            return 'high'
        elif total_score > 0.65:
            return 'medium'
        else:
            return 'low'
    
    def _generate_strategy(self, auction_signals: dict) -> str:
        """生成交易策略"""
        gap_type = auction_signals['gap_type']
        
        if gap_type == 'high_gap_up':
            return "高开过度，建议等待回踩"
        elif gap_type == 'gap_up' and auction_signals['capital_bias'] > 0.6:
            return "温和高开+资金坚决，开盘可买"
        elif gap_type == 'flat' and auction_signals['signal_strength'] > 0.6:
            return "平开强势，竞价后买入"
        elif gap_type == 'gap_down' and auction_signals['auction_ratio'] > -2:
            return "小幅低开，可逢低吸纳"
        else:
            return "竞价信号一般，建议观望"

def enhanced_stock_selection():
    """增强版选股主程序"""
    load_dotenv()
    
    print('=== CChanTrader-AI 竞价数据增强版 ===')
    print('🎯 整合集合竞价分析，提升选股精确度')
    
    # 初始化分析器
    analyzer = EnhancedCChanTrader()
    
    # 连接BaoStock获取基础数据
    lg = bs.login()
    print(f'📊 BaoStock连接: {lg.error_code}')
    
    try:
        # 获取股票列表
        print('\n🔍 获取股票列表...')
        stock_rs = bs.query_all_stock(day='2025-06-26')
        all_stocks = stock_rs.get_data()
        
        # 多市场采样
        markets = {
            '上海主板': all_stocks[all_stocks['code'].str.startswith('sh.6')],
            '深圳主板': all_stocks[all_stocks['code'].str.startswith('sz.000')],
            '中小板': all_stocks[all_stocks['code'].str.startswith('sz.002')],
            '创业板': all_stocks[all_stocks['code'].str.startswith('sz.30')]
        }
        
        sample_stocks = []
        for market_name, market_stocks in markets.items():
            if len(market_stocks) > 0:
                sample_size = min(20, len(market_stocks))
                sampled = market_stocks.sample(n=sample_size, random_state=42)
                sample_stocks.append(sampled)
        
        final_sample = pd.concat(sample_stocks, ignore_index=True)
        print(f'📋 分析样本: {len(final_sample)}只股票')
        
        # 获取K线数据
        print('\n📈 获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        stock_data = {}
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
                    stock_data[code] = {'df': day_df, 'name': name}
                    
            except Exception:
                continue
        
        print(f'✅ 获取到 {len(stock_data)} 只股票数据')
        
        # 执行增强分析
        print('\n🧠 执行竞价增强分析...')
        selected_stocks = []
        
        for symbol, data in tqdm(stock_data.items(), desc='分析'):
            df = analyzer.safe_data_conversion(data['df'])
            df = analyzer.add_technical_indicators(df)
            
            result = analyzer.analyze_stock_with_auction(symbol, df, data['name'])
            if result:
                selected_stocks.append(result)
        
        # 排序和展示
        selected_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f'\n🎯 === 竞价增强选股结果 ===')
        print(f'符合条件: {len(selected_stocks)}只')
        
        # 分市场展示
        for market in ['上海主板', '深圳主板', '中小板', '创业板']:
            market_stocks = [s for s in selected_stocks if s['market'] == market]
            if market_stocks:
                print(f'\n🏆 {market}:')
                for i, stock in enumerate(market_stocks[:3], 1):
                    print(f'  {i}. {stock["symbol"]} - {stock["stock_name"]}')
                    print(f'     💰 价格: {stock["current_price"]:.2f}元 | 综合评分: {stock["total_score"]}')
                    print(f'     📊 技术: {stock["tech_score"]} | 竞价: {stock["auction_score"]}')
                    print(f'     📈 竞价比率: {stock["auction_ratio"]}% | 缺口: {stock["gap_type"]}')
                    print(f'     💎 资金偏向: {stock["capital_bias"]} | 成交量: {stock["auction_volume"]}手')
                    print(f'     🎯 策略: {stock["strategy"]}')
                    print(f'     💡 信心: {stock["confidence"]} | 目标: {stock["target_price"]:.2f}元')
        
        # 保存结果
        output_file = '/Users/yang/enhanced_auction_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\n💾 详细结果保存: {output_file}')
        print(f'\n✅ 竞价数据成功整合！算法精确度已提升')
        
        return selected_stocks
        
    finally:
        bs.logout()
        print('\n🔚 分析完成')

if __name__ == '__main__':
    results = enhanced_stock_selection()