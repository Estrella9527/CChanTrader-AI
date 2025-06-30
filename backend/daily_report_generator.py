#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 交易日报生成器
在每个交易日9:25-9:29自动分析并生成日报
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import baostock as bs
import akshare as ak
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from backend.services.email_config import EmailSender

class DailyReportGenerator:
    """交易日报生成器"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.analysis_results = {}
        self.report_data = {}
        
    def is_trading_day(self, date=None) -> bool:
        """判断是否为交易日"""
        if date is None:
            date = datetime.now()
        
        # 简化版：排除周末
        weekday = date.weekday()
        if weekday >= 5:  # 周六日
            return False
        
        # TODO: 可以集成节假日API进行更精确判断
        return True
    
    def get_stock_data_quick(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """快速获取股票数据"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            rs = bs.query_history_k_data_plus(symbol,
                'date,code,open,high,low,close,volume',
                start_date=start_date, 
                end_date=end_date,
                frequency='d')
            df = rs.get_data()
            
            if df.empty:
                return pd.DataFrame()
            
            # 数据转换
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.split().str[0]
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.dropna()
            
        except Exception:
            return pd.DataFrame()
    
    def get_auction_data_quick(self, symbol: str) -> dict:
        """快速获取竞价数据"""
        try:
            # 使用AKShare获取竞价数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00", 
                end_time="09:30:00"
            )
            
            if pre_market_df.empty:
                return self._get_default_auction()
            
            # 筛选竞价时间
            auction_df = pre_market_df[
                pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]')
            ]
            
            if auction_df.empty:
                return self._get_default_auction()
            
            final_price = float(auction_df.iloc[-1]['开盘'])
            total_volume = auction_df['成交量'].sum()
            
            return {
                'final_price': final_price,
                'total_volume': total_volume,
                'data_points': len(auction_df),
                'status': 'success'
            }
            
        except Exception:
            return self._get_default_auction()
    
    def _get_default_auction(self) -> dict:
        """默认竞价数据"""
        return {
            'final_price': 0,
            'total_volume': 0,
            'data_points': 0,
            'status': 'no_data'
        }
    
    def analyze_single_stock(self, symbol: str, stock_name: str) -> dict:
        """分析单只股票"""
        try:
            # 获取历史数据
            df = self.get_stock_data_quick(symbol, 30)
            if len(df) < 20:
                return None
            
            current_price = float(df['close'].iloc[-1])
            prev_close = float(df['close'].iloc[-2])
            
            # 基础过滤
            if not (2 <= current_price <= 300):
                return None
            
            # 技术指标计算
            tech_score = self._calculate_tech_indicators(df)
            
            # 竞价数据分析
            auction_data = self.get_auction_data_quick(symbol)
            auction_score = self._analyze_auction_signals(auction_data, prev_close)
            
            # 综合评分
            total_score = tech_score * 0.65 + auction_score['strength'] * 0.35
            
            # 竞价加分
            if auction_score['ratio'] > 0.5 and auction_score['strength'] > 0.6:
                total_score += 0.1
            
            # 筛选条件
            if total_score < 0.65:
                return None
            
            return {
                'symbol': symbol,
                'stock_name': stock_name,
                'market': self._get_market_type(symbol),
                'current_price': current_price,
                'total_score': round(total_score, 3),
                'tech_score': round(tech_score, 3),
                'auction_score': round(auction_score['strength'], 3),
                'auction_ratio': auction_score['ratio'],
                'gap_type': auction_score['gap_type'],
                'capital_bias': auction_score.get('capital_bias', 0),
                'rsi': self._calculate_rsi(df),
                'volume_ratio': self._calculate_volume_ratio(df),
                'entry_price': current_price,
                'stop_loss': round(current_price * 0.92, 2),
                'target_price': round(current_price * 1.15, 2),
                'confidence': self._determine_confidence(total_score, auction_score),
                'strategy': self._generate_strategy(auction_score)
            }
            
        except Exception:
            return None
    
    def _calculate_tech_indicators(self, df: pd.DataFrame) -> float:
        """计算技术指标评分"""
        score = 0.5
        
        try:
            # 均线
            if len(df) >= 20:
                ma5 = df['close'].rolling(5).mean().iloc[-1]
                ma10 = df['close'].rolling(10).mean().iloc[-1] 
                ma20 = df['close'].rolling(20).mean().iloc[-1]
                current = df['close'].iloc[-1]
                
                if current > ma5 > ma10 > ma20:
                    score += 0.25
                elif current > ma5 > ma10:
                    score += 0.15
            
            # RSI
            rsi = self._calculate_rsi(df)
            if 30 <= rsi <= 70:
                score += 0.15
            
            # 成交量
            vol_ratio = self._calculate_volume_ratio(df)
            if vol_ratio > 0.8:
                score += 0.1
            
        except Exception:
            pass
        
        return min(1.0, score)
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """计算RSI"""
        try:
            if len(df) < period + 1:
                return 50.0
            
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = -delta.where(delta < 0, 0).rolling(period).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception:
            return 50.0
    
    def _calculate_volume_ratio(self, df: pd.DataFrame) -> float:
        """计算量比"""
        try:
            if len(df) < 10:
                return 1.0
            
            vol_ma = df['volume'].rolling(10).mean().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            return float(current_vol / (vol_ma + 1e-10))
        except Exception:
            return 1.0
    
    def _analyze_auction_signals(self, auction_data: dict, prev_close: float) -> dict:
        """分析竞价信号"""
        if auction_data['status'] != 'success' or auction_data['final_price'] == 0:
            return {
                'strength': 0.3,
                'ratio': 0,
                'gap_type': 'no_data',
                'capital_bias': 0
            }
        
        final_price = auction_data['final_price']
        ratio = (final_price - prev_close) / prev_close * 100
        
        # 缺口类型
        if ratio > 3:
            gap_type = 'high_gap_up'
        elif ratio > 1:
            gap_type = 'gap_up'
        elif ratio > -1:
            gap_type = 'flat'
        elif ratio > -3:
            gap_type = 'gap_down'
        else:
            gap_type = 'low_gap_down'
        
        # 信号强度
        strength = 0.5
        if 0.5 <= ratio <= 3:
            strength += 0.3
        elif ratio > 3:
            strength -= 0.1
        
        if auction_data['total_volume'] > 0:
            strength += 0.1
        
        if auction_data['data_points'] >= 8:  # 有足够数据点
            strength += 0.1
        
        return {
            'strength': max(0, min(1, strength)),
            'ratio': round(ratio, 2),
            'gap_type': gap_type,
            'capital_bias': min(auction_data['data_points'] / 10, 1.0)
        }
    
    def _get_market_type(self, symbol: str) -> str:
        """获取市场类型"""
        if symbol.startswith('sh.6'):
            return '上海主板'
        elif symbol.startswith('sz.000'):
            return '深圳主板'
        elif symbol.startswith('sz.002'):
            return '中小板'
        elif symbol.startswith('sz.30'):
            return '创业板'
        return '其他'
    
    def _determine_confidence(self, total_score: float, auction_score: dict) -> str:
        """确定置信度"""
        if total_score > 0.85 and auction_score['strength'] > 0.7:
            return 'very_high'
        elif total_score > 0.75:
            return 'high'
        elif total_score > 0.65:
            return 'medium'
        return 'low'
    
    def _generate_strategy(self, auction_score: dict) -> str:
        """生成策略建议"""
        gap_type = auction_score['gap_type']
        ratio = auction_score['ratio']
        
        if gap_type == 'high_gap_up':
            return "高开过度，建议等待回踩"
        elif gap_type == 'gap_up' and auction_score['strength'] > 0.6:
            return "温和高开，开盘可买"
        elif gap_type == 'flat' and auction_score['strength'] > 0.6:
            return "平开强势，关注买入"
        elif gap_type == 'gap_down' and ratio > -2:
            return "小幅低开，可逢低买入"
        else:
            return "竞价信号一般，建议观望"
    
    def generate_daily_report(self) -> dict:
        """生成每日报告"""
        print("🔄 开始生成交易日报...")
        
        if not self.is_trading_day():
            print("📅 今日非交易日，跳过报告生成")
            return {}
        
        # 连接数据源
        lg = bs.login()
        print(f"📊 BaoStock连接: {lg.error_code}")
        
        try:
            # 获取股票列表
            print("🔍 获取股票列表...")
            stock_rs = bs.query_all_stock(day=datetime.now().strftime('%Y-%m-%d'))
            all_stocks = stock_rs.get_data()
            
            if all_stocks.empty:
                print("❌ 无法获取股票列表")
                return {}
            
            # 快速采样分析 (限制数量以提高速度)
            markets = {
                '上海主板': all_stocks[all_stocks['code'].str.startswith('sh.6')],
                '深圳主板': all_stocks[all_stocks['code'].str.startswith('sz.000')],
                '中小板': all_stocks[all_stocks['code'].str.startswith('sz.002')],
                '创业板': all_stocks[all_stocks['code'].str.startswith('sz.30')]
            }
            
            sample_stocks = []
            for market_name, market_stocks in markets.items():
                if len(market_stocks) > 0:
                    sample_size = min(15, len(market_stocks))  # 限制每个市场15只
                    sampled = market_stocks.sample(n=sample_size, random_state=42)
                    sample_stocks.append(sampled)
            
            final_sample = pd.concat(sample_stocks, ignore_index=True)
            print(f"📋 快速分析样本: {len(final_sample)}只股票")
            
            # 执行分析
            print("🧠 执行股票分析...")
            recommendations = []
            auction_stats = {
                'gap_up_count': 0,
                'flat_count': 0,
                'gap_down_count': 0,
                'total_auction_ratio': 0,
                'analyzed_count': 0
            }
            
            for _, stock in tqdm(final_sample.iterrows(), total=len(final_sample), desc="分析进度"):
                result = self.analyze_single_stock(stock['code'], stock['code_name'])
                if result:
                    recommendations.append(result)
                    
                    # 统计竞价数据
                    auction_stats['analyzed_count'] += 1
                    auction_stats['total_auction_ratio'] += result['auction_ratio']
                    
                    gap_type = result['gap_type']
                    if 'gap_up' in gap_type:
                        auction_stats['gap_up_count'] += 1
                    elif gap_type == 'flat':
                        auction_stats['flat_count'] += 1
                    elif 'gap_down' in gap_type:
                        auction_stats['gap_down_count'] += 1
            
            # 排序推荐结果
            recommendations.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 计算汇总统计
            avg_auction_ratio = (auction_stats['total_auction_ratio'] / 
                               max(auction_stats['analyzed_count'], 1))
            
            avg_score = (sum(r['total_score'] for r in recommendations) / 
                        max(len(recommendations), 1))
            
            # 生成报告数据
            report_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_time': datetime.now().strftime('%H:%M:%S'),
                'recommendations': recommendations[:15],  # 限制推荐数量
                'market_summary': {
                    'total_analyzed': len(final_sample),
                    'total_recommended': len(recommendations),
                    'avg_score': round(avg_score, 3)
                },
                'auction_analysis': {
                    'avg_auction_ratio': round(avg_auction_ratio, 2),
                    'gap_up_count': auction_stats['gap_up_count'],
                    'flat_count': auction_stats['flat_count'],
                    'gap_down_count': auction_stats['gap_down_count']
                }
            }
            
            # 保存详细结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = fos.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'daily_report_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            report_data['json_file'] = json_file
            
            print(f"✅ 日报生成完成:")
            print(f"   📊 分析股票: {len(final_sample)}只")
            print(f"   🎯 推荐股票: {len(recommendations)}只")
            print(f"   📈 平均评分: {avg_score:.3f}")
            print(f"   💾 详细数据: {json_file}")
            
            return report_data
            
        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            return {}
        
        finally:
            bs.logout()
    
    def send_daily_report(self) -> bool:
        """发送每日报告"""
        try:
            # 生成报告
            report_data = self.generate_daily_report()
            
            if not report_data:
                print("📭 无报告数据，跳过邮件发送")
                return False
            
            # 发送邮件
            print("📧 发送日报邮件...")
            success = self.email_sender.send_daily_report(report_data)
            
            if success:
                print("✅ 日报邮件发送成功!")
                return True
            else:
                print("❌ 日报邮件发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送日报过程出错: {e}")
            return False

# 快速测试版本
def quick_test_report():
    """快速测试报告生成"""
    print("🧪 快速测试日报生成...")
    
    generator = DailyReportGenerator()
    
    # 模拟报告数据
    mock_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'analysis_time': datetime.now().strftime('%H:%M:%S'),
        'recommendations': [
            {
                'symbol': 'sh.600000',
                'stock_name': '浦发银行',
                'market': '上海主板',
                'current_price': 13.65,
                'total_score': 0.856,
                'tech_score': 0.750,
                'auction_score': 0.720,
                'auction_ratio': 1.2,
                'gap_type': 'gap_up',
                'capital_bias': 0.68,
                'rsi': 65.2,
                'volume_ratio': 1.3,
                'entry_price': 13.65,
                'stop_loss': 12.56,
                'target_price': 15.70,
                'confidence': 'very_high',
                'strategy': '温和高开，开盘可买'
            },
            {
                'symbol': 'sz.000001',
                'stock_name': '平安银行',
                'market': '深圳主板', 
                'current_price': 12.38,
                'total_score': 0.789,
                'tech_score': 0.680,
                'auction_score': 0.650,
                'auction_ratio': 0.8,
                'gap_type': 'flat',
                'capital_bias': 0.55,
                'rsi': 58.1,
                'volume_ratio': 1.1,
                'entry_price': 12.38,
                'stop_loss': 11.39,
                'target_price': 14.24,
                'confidence': 'high',
                'strategy': '平开强势，关注买入'
            }
        ],
        'market_summary': {
            'total_analyzed': 60,
            'total_recommended': 2,
            'avg_score': 0.823
        },
        'auction_analysis': {
            'avg_auction_ratio': 1.0,
            'gap_up_count': 25,
            'flat_count': 20,
            'gap_down_count': 15
        }
    }
    
    # 测试邮件发送
    success = generator.email_sender.send_daily_report(mock_data)
    
    if success:
        print("✅ 测试邮件发送成功!")
    else:
        print("❌ 测试邮件发送失败，请检查邮件配置")

if __name__ == "__main__":
    # 选择运行模式
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # 测试模式
        quick_test_report()
    else:
        # 正常模式
        generator = DailyReportGenerator()
        generator.send_daily_report()