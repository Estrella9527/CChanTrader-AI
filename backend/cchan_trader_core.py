#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 核心选股引擎
基于缠论技术分析的智能选股系统 - 程序就绪版本
"""

import os, json, pandas as pd, numpy as np
import baostock as bs
from tqdm import tqdm
from datetime import datetime, timedelta
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# ============================================================================
# 0. 全局参数表 (PARAMS) - 可随时调优/网格搜索
# ============================================================================

PARAMS = {
    # 级别与均线
    "periods": ["D", "30m", "5m"],
    "ma_short": 5,
    "ma_mid": 34, 
    "ma_long": 170,          # 用于超长期支撑
    
    # 趋势判定
    "daily_up_cross_ratio": 1.02,  # 日线必须突破前高>=2%
    "ma_align_threshold": 0.98,    # MA排列容忍度
    
    # 成交量
    "v_break_min": 1.8,      # 放量突破需≥过去5根均量1.8倍
    "v_pull_max": 0.5,       # 回踩缩量≤过去5根均量50%
    "vol_ma_period": 5,      # 成交量均线周期
    
    # 行业/热点 (BaoStock版本简化)
    "hot_rank_max": 10,      # 热点板块榜前10
    "rs_threshold": 1.2,     # 相对强弱 > 1.2 判定龙头
    "price_strength_days": 10, # 价格强度计算天数
    
    # 风控
    "max_account_risk": 0.02,    # 单笔亏损不超账户2%
    "stop_buffer_pct": 0.03,     # 止损位再让3% buffer
    "max_position_pct": 0.1,     # 单仓位不超10%
    
    # 技术指标
    "rsi_oversold": 30,      # RSI超卖
    "rsi_overbought": 70,    # RSI超买
    "macd_threshold": 0,     # MACD阈值
}

# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class Segment:
    """缠论线段"""
    start_idx: int
    end_idx: int
    direction: str  # 'up' | 'down'
    high: float
    low: float
    start_price: float
    end_price: float

@dataclass 
class Pivot:
    """缠论中枢"""
    start_idx: int
    end_idx: int
    high: float
    low: float
    center: float
    strength: float  # 中枢强度

@dataclass
class Signal:
    """买卖信号"""
    signal_type: str  # '1_buy', '2_buy', '3_buy', '1_sell', '2_sell'
    k_idx: int
    price: float
    confidence: float

@dataclass
class StructureInfo:
    """结构分析结果"""
    segments: List[Segment]
    pivots: List[Pivot]
    trend: str  # 'up' | 'down' | 'side'
    signals: Dict[str, List[Signal]]
    vol_stats: Dict[str, float]
    tech_indicators: Dict[str, float]

# ============================================================================
# 1. 预处理：K线 → 线段/中枢 (核心缠论算法接口)
# ============================================================================

def parse_structure(df: pd.DataFrame, period: str = "D") -> StructureInfo:
    """
    将K线数据解析为缠论结构
    
    返回:
      StructureInfo{
        'segments': List[Segment],     # 线段列表
        'pivots': List[Pivot],         # 中枢列表  
        'trend': 'up'|'down'|'side',   # 当前趋势
        'signals': {'1_buy':[], '2_buy':[], '3_buy':[], '1_sell':[], '2_sell':[]},
        'vol_stats': {'volume_factor':..., 'pullback_factor':...},
        'tech_indicators': {'rsi':..., 'macd':...}
      }
    """
    
    if df.empty or len(df) < 10:
        return StructureInfo([], [], 'side', {}, {}, {})
    
    # 数据预处理
    df = df.copy()
    
    # 更安全的数据类型转换
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 过滤掉空值和无效数据
    df = df.dropna(subset=['high', 'low', 'close'])
    
    # 确保价格数据为正数
    df = df[(df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
    
    # 修复volume的空值问题
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0)
    
    # ========== 线段识别 (简化版缠论算法) ==========
    segments = _identify_segments(df)
    
    # ========== 中枢识别 ==========
    pivots = _identify_pivots(df, segments)
    
    # ========== 趋势判定 ==========
    trend = _determine_trend(df, segments, pivots)
    
    # ========== 信号识别 ==========
    signals = _identify_signals(df, segments, pivots, period)
    
    # ========== 量价统计 ==========
    vol_stats = _calculate_volume_stats(df)
    
    # ========== 技术指标 ==========
    tech_indicators = _calculate_technical_indicators(df)
    
    return StructureInfo(
        segments=segments,
        pivots=pivots, 
        trend=trend,
        signals=signals,
        vol_stats=vol_stats,
        tech_indicators=tech_indicators
    )

def _identify_segments(df: pd.DataFrame) -> List[Segment]:
    """线段识别 - 简化版本"""
    segments = []
    if len(df) < 5:
        return segments
        
    # 寻找局部极值点
    highs = []
    lows = []
    
    for i in range(2, len(df)-2):
        # 局部高点
        if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
            df['high'].iloc[i] > df['high'].iloc[i+1] and
            df['high'].iloc[i] > df['high'].iloc[i-2] and 
            df['high'].iloc[i] > df['high'].iloc[i+2]):
            highs.append((i, df['high'].iloc[i]))
            
        # 局部低点    
        if (df['low'].iloc[i] < df['low'].iloc[i-1] and
            df['low'].iloc[i] < df['low'].iloc[i+1] and
            df['low'].iloc[i] < df['low'].iloc[i-2] and
            df['low'].iloc[i] < df['low'].iloc[i+2]):
            lows.append((i, df['low'].iloc[i]))
    
    # 合并高低点并排序
    points = [(idx, price, 'high') for idx, price in highs] + \
             [(idx, price, 'low') for idx, price in lows]
    points.sort()
    
    # 构建线段
    for i in range(len(points)-1):
        start_idx, start_price, start_type = points[i]
        end_idx, end_price, end_type = points[i+1]
        
        if start_type != end_type:  # 高低点交替
            direction = 'up' if start_type == 'low' else 'down'
            segment = Segment(
                start_idx=start_idx,
                end_idx=end_idx,
                direction=direction,
                high=max(start_price, end_price),
                low=min(start_price, end_price),
                start_price=start_price,
                end_price=end_price
            )
            segments.append(segment)
    
    return segments

def _identify_pivots(df: pd.DataFrame, segments: List[Segment]) -> List[Pivot]:
    """中枢识别"""
    pivots = []
    
    if len(segments) < 3:
        return pivots
        
    # 寻找三段式中枢: 上-下-上 或 下-上-下
    for i in range(len(segments)-2):
        seg1, seg2, seg3 = segments[i], segments[i+1], segments[i+2]
        
        # 检查是否形成中枢
        if (seg1.direction != seg2.direction and 
            seg2.direction != seg3.direction and
            seg1.direction == seg3.direction):
            
            # 计算中枢范围
            if seg1.direction == 'up':  # 上-下-上
                pivot_high = min(seg1.high, seg3.high)
                pivot_low = seg2.low
            else:  # 下-上-下
                pivot_high = seg2.high  
                pivot_low = max(seg1.low, seg3.low)
                
            if pivot_high > pivot_low:  # 有效中枢
                pivot = Pivot(
                    start_idx=seg1.start_idx,
                    end_idx=seg3.end_idx,
                    high=pivot_high,
                    low=pivot_low,
                    center=(pivot_high + pivot_low) / 2,
                    strength=abs(pivot_high - pivot_low) / pivot_low
                )
                pivots.append(pivot)
    
    return pivots

def _determine_trend(df: pd.DataFrame, segments: List[Segment], pivots: List[Pivot]) -> str:
    """趋势判定"""
    if not segments:
        return 'side'
        
    # 基于最后几个线段的方向
    recent_segments = segments[-3:] if len(segments) >= 3 else segments
    up_count = sum(1 for seg in recent_segments if seg.direction == 'up')
    down_count = sum(1 for seg in recent_segments if seg.direction == 'down')
    
    # 结合MA趋势
    if len(df) >= PARAMS["ma_short"]:
        ma5 = df['close'].rolling(PARAMS["ma_short"]).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if up_count > down_count and current_price > ma5:
            return 'up'
        elif down_count > up_count and current_price < ma5:
            return 'down'
            
    return 'side'

def _identify_signals(df: pd.DataFrame, segments: List[Segment], 
                     pivots: List[Pivot], period: str) -> Dict[str, List[Signal]]:
    """信号识别"""
    signals = {'1_buy': [], '2_buy': [], '3_buy': [], '1_sell': [], '2_sell': []}
    
    if not pivots or len(df) < 10:
        return signals
        
    current_price = df['close'].iloc[-1]
    
    # 二买信号：中枢突破
    for pivot in pivots[-2:]:  # 检查最近的中枢
        if current_price > pivot.high * PARAMS["daily_up_cross_ratio"]:
            signal = Signal(
                signal_type='2_buy',
                k_idx=len(df)-1,
                price=current_price,
                confidence=0.8
            )
            signals['2_buy'].append(signal)
            break
            
    # 三买信号：趋势中的回调买点
    if len(segments) >= 2:
        last_seg = segments[-1]
        if (last_seg.direction == 'up' and 
            current_price > last_seg.start_price * 1.01):  # 突破回调低点
            signal = Signal(
                signal_type='3_buy', 
                k_idx=len(df)-1,
                price=current_price,
                confidence=0.7
            )
            signals['3_buy'].append(signal)
    
    return signals

def _calculate_volume_stats(df: pd.DataFrame) -> Dict[str, float]:
    """量价统计"""
    if len(df) < PARAMS["vol_ma_period"]:
        return {'volume_factor': 1.0, 'pullback_factor': 1.0}
        
    vol_ma = df['volume'].rolling(PARAMS["vol_ma_period"]).mean()
    current_vol = df['volume'].iloc[-1]
    avg_vol = vol_ma.iloc[-PARAMS["vol_ma_period"]:].mean()
    
    volume_factor = current_vol / avg_vol if avg_vol > 0 else 1.0
    
    # 回调量能比率 (简化计算)
    recent_vol = df['volume'].iloc[-3:].mean()
    prev_vol = df['volume'].iloc[-8:-3].mean()
    pullback_factor = recent_vol / prev_vol if prev_vol > 0 else 1.0
    
    return {
        'volume_factor': volume_factor,
        'pullback_factor': pullback_factor,
        'avg_volume': avg_vol
    }

def _calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """技术指标计算"""
    indicators = {}
    
    if len(df) < 14:
        return indicators
        
    # RSI计算
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    indicators['rsi'] = rsi.iloc[-1] if not rsi.isna().iloc[-1] else 50
    
    # MACD (简化版)
    if len(df) >= 26:
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        indicators['macd'] = macd.iloc[-1]
        
    # 移动平均线
    for period in [5, 10, 20, 60]:
        if len(df) >= period:
            ma = df['close'].rolling(period).mean().iloc[-1]
            indicators[f'ma{period}'] = ma
            
    return indicators

# ============================================================================
# 2. 大级别方向过滤（日线Up-Trend）
# ============================================================================

def is_daily_uptrend(daily_info: StructureInfo, df_day: pd.DataFrame) -> bool:
    """
    判断日线是否为上升趋势
    a) 最近一个Pivot(中枢)已被向上有效突破  
    b) 收盘价 > 34MA 并高于 pivot_high * daily_up_cross_ratio
    c) 或者MACD金叉 + 价格站上MA170
    """
    if not daily_info.pivots or len(df_day) < PARAMS["ma_mid"]:
        return False
        
    last_pivot = daily_info.pivots[-1]
    current_price = df_day['close'].iloc[-1]
    
    # 条件1: 突破中枢
    cond1 = current_price > last_pivot.high * PARAMS["daily_up_cross_ratio"]
    
    # 条件2: 均线条件
    ma34 = df_day['close'].rolling(PARAMS["ma_mid"]).mean().iloc[-1]
    cond2 = current_price > ma34
    
    # 条件3: MACD辅助
    cond3 = True
    if 'macd' in daily_info.tech_indicators:
        cond3 = daily_info.tech_indicators['macd'] > PARAMS["macd_threshold"]
    
    # 条件4: 趋势方向
    cond4 = daily_info.trend == 'up'
    
    return (cond1 and cond2) or (cond3 and cond4)

# ============================================================================
# 3. 中观买点触发（30min 二买/三买 + 量价确认）
# ============================================================================

def detect_30m_entry(info_30m: StructureInfo) -> Tuple[bool, Optional[str], Optional[float], Optional[float]]:
    """
    检测30分钟级别的入场信号
    返回 (is_ok, tag, entry_price, stop_loss)
    """
    # 检查信号
    tag = None
    if info_30m.signals.get('2_buy'):
        tag = '2_buy'
    elif info_30m.signals.get('3_buy'):
        tag = '3_buy'
        
    if not tag:
        return (False, None, None, None)
    
    # 量价确认
    vol_stats = info_30m.vol_stats
    vfac = vol_stats.get('volume_factor', 1.0)
    pull = vol_stats.get('pullback_factor', 1.0)
    
    vol_ok = vfac >= PARAMS["v_break_min"]
    pull_ok = pull <= PARAMS["v_pull_max"]
    
    if not (vol_ok and pull_ok):
        return (False, None, None, None)
    
    # 获取信号价格
    last_signal = info_30m.signals[tag][-1]
    entry_price = last_signal.price
    stop_loss = entry_price * (1 - PARAMS["stop_buffer_pct"])
    
    return (True, tag, entry_price, stop_loss)

# ============================================================================
# 4. 细节坐标（5min 缩量回踩企稳）
# ============================================================================

def confirm_5m_pullback(info_5m: StructureInfo, entry_price: float) -> bool:
    """
    5分钟级别确认：缩量回踩企稳
    """
    if not info_5m.segments:
        return True  # 无5分钟数据时直接通过
        
    # 检查最后一段是否为回踩
    last_seg = info_5m.segments[-1]
    if last_seg.direction != 'down':
        return True  # 非回踩，直接通过
        
    # 检查回踩幅度
    if info_5m.pivots:
        last_pivot = info_5m.pivots[-1]
        lowest = min(last_seg.low, last_pivot.low)
        if entry_price < lowest * 1.02:  # 跌破关键位
            return False
            
    # 检查缩量
    vol_factor = info_5m.vol_stats.get('pullback_factor', 1.0)
    return vol_factor <= PARAMS["v_pull_max"]

# ============================================================================
# 5. 行业热点 & 龙头验证 (BaoStock适配版)
# ============================================================================

def is_hot_leader(symbol: str, df_day: pd.DataFrame) -> Tuple[bool, str]:
    """
    判断是否为热点龙头 (基于BaoStock数据的简化版本)
    """
    # 由于BaoStock没有直接的行业热度数据，这里用技术指标替代
    
    # 相对强度计算 (简化版)
    if len(df_day) < PARAMS["price_strength_days"]:
        return False, "数据不足"
        
    # 计算相对强度
    price_change = (df_day['close'].iloc[-1] / df_day['close'].iloc[-PARAMS["price_strength_days"]] - 1) * 100
    
    # 成交量活跃度
    recent_vol = df_day['volume'].iloc[-5:].mean()
    prev_vol = df_day['volume'].iloc[-15:-5].mean()
    vol_activity = recent_vol / prev_vol if prev_vol > 0 else 1.0
    
    # 简化的热点判定
    is_hot = (price_change > 5.0 and vol_activity > 1.5) or price_change > 10.0
    
    # 获取行业信息 (BaoStock可能有限)
    industry_name = "未知行业"  # BaoStock需要额外接口获取
    
    return is_hot, industry_name

# ============================================================================
# 6. 完整选股函数
# ============================================================================

def select_stock(symbol: str, kdict: Dict[str, pd.DataFrame]) -> Optional[Dict]:
    """
    完整的单只股票选股逻辑
    """
    try:
        # 获取各级别数据
        day_df = kdict.get("D")
        m30_df = kdict.get("30m") 
        m5_df = kdict.get("5m")
        
        if day_df is None or day_df.empty:
            return None
            
        # Step 1: 日线趋势过滤
        day_info = parse_structure(day_df, "D")
        if not is_daily_uptrend(day_info, day_df):
            return None
            
        # Step 2: 30分钟买点检测
        if m30_df is not None and not m30_df.empty:
            info_30m = parse_structure(m30_df, "30m")
            ok, tag, entry, stop = detect_30m_entry(info_30m)
            if not ok:
                return None
        else:
            # 无30分钟数据时用日线信号
            if not day_info.signals.get('2_buy') and not day_info.signals.get('3_buy'):
                return None
            tag = '2_buy' if day_info.signals.get('2_buy') else '3_buy'
            entry = day_df['close'].iloc[-1]
            stop = entry * (1 - PARAMS["stop_buffer_pct"])
            
        # Step 3: 5分钟确认 (可选)
        if m5_df is not None and not m5_df.empty:
            info_5m = parse_structure(m5_df, "5m")
            if not confirm_5m_pullback(info_5m, entry):
                return None
                
        # Step 4: 热点验证
        hot_leader, industry = is_hot_leader(symbol, day_df)
        if not hot_leader:
            return None
            
        # Step 5: 技术指标过滤
        tech_ok = True
        if 'rsi' in day_info.tech_indicators:
            rsi = day_info.tech_indicators['rsi']
            tech_ok = PARAMS["rsi_oversold"] <= rsi <= PARAMS["rsi_overbought"]
            
        if not tech_ok:
            return None
            
        # 计算相对强度
        price_strength = 0
        if len(day_df) >= PARAMS["price_strength_days"]:
            price_strength = (day_df['close'].iloc[-1] / day_df['close'].iloc[-PARAMS["price_strength_days"]] - 1) * 100
            
        return {
            'symbol': symbol,
            'industry': industry,
            'entry_price': round(entry, 2),
            'stop_loss': round(stop, 2), 
            'signal': tag,
            'price_strength': round(price_strength, 2),
            'volume_factor': round(day_info.vol_stats.get('volume_factor', 1.0), 2),
            'rsi': round(day_info.tech_indicators.get('rsi', 50), 1),
            'trend': day_info.trend,
            'confidence': round((day_info.signals.get(tag, [Signal('', 0, 0, 0.5)])[-1].confidence), 2)
        }
        
    except Exception as e:
        print(f"处理股票 {symbol} 时出错: {e}")
        return None

# ============================================================================
# 7. 风控计算
# ============================================================================

def calculate_position_size(account_equity: float, entry_price: float, 
                          stop_loss: float) -> int:
    """计算仓位大小"""
    risk_amount = account_equity * PARAMS["max_account_risk"]
    risk_per_share = entry_price - stop_loss
    
    if risk_per_share <= 0:
        return 0
        
    shares = int(risk_amount / risk_per_share)
    max_shares = int(account_equity * PARAMS["max_position_pct"] / entry_price)
    
    return min(shares, max_shares)

# ============================================================================
# 8. 主程序入口
# ============================================================================

def cchan_trader_main(test_mode: bool = True, max_stocks: int = 20):
    """
    CChanTrader主程序
    """
    # 加载环境变量
    load_dotenv()
    
    print('=== CChanTrader-AI 核心选股引擎 ===')
    print(f'参数配置: {json.dumps(PARAMS, indent=2, ensure_ascii=False)}')
    
    # 登录BaoStock
    lg = bs.login()
    print(f'BaoStock状态: {lg.error_code} - {lg.error_msg}')
    
    try:
        # 获取股票列表
        print('\\n获取股票列表...')
        for days_back in range(0, 10):
            query_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            stock_rs = bs.query_all_stock(query_date)
            stock_df = stock_rs.get_data()
            if not stock_df.empty:
                break
                
        if stock_df.empty:
            print('无法获取股票数据')
            return []
            
        # 过滤A股
        a_stocks = stock_df[stock_df['code'].str.contains('sh.6|sz.0|sz.3')]
        if test_mode:
            a_stocks = a_stocks.head(max_stocks)
            
        print(f'待分析股票数量: {len(a_stocks)}')
        
        # 获取K线数据
        print('\\n获取K线数据...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
        
        kline_data = {}
        for _, stock in tqdm(a_stocks.iterrows(), total=len(a_stocks), desc='获取K线'):
            code = stock['code']
            try:
                # 只获取日K线 (BaoStock分钟数据有限制)
                rs_day = bs.query_history_k_data_plus(code,
                    'date,code,open,high,low,close,volume,amount',
                    start_date=start_date, end_date=end_date, frequency='d')
                day_df = rs_day.get_data()
                
                if not day_df.empty and len(day_df) >= 60:
                    kline_data[code] = {'D': day_df}
                    
            except Exception as e:
                continue
                
        print(f'成功获取 {len(kline_data)} 只股票数据')
        
        # 执行选股
        print('\\n执行选股分析...')
        results = []
        for symbol, kdict in tqdm(kline_data.items(), desc='选股分析'):
            result = select_stock(symbol, kdict)
            if result:
                results.append(result)
                
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f'\\n=== 选股结果 ({len(results)}只) ===')
        for i, stock in enumerate(results, 1):
            print(f'{i}. {stock["symbol"]} - {stock["signal"]}')
            print(f'   入场: {stock["entry_price"]}, 止损: {stock["stop_loss"]}')
            print(f'   强度: {stock["price_strength"]}%, 量能: {stock["volume_factor"]}x')
            print(f'   RSI: {stock["rsi"]}, 趋势: {stock["trend"]}')
            print(f'   置信度: {stock["confidence"]}')
            print()
            
        # 保存结果
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cchan_results.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f'结果已保存到 cchan_results.json')
        return results
        
    finally:
        bs.logout()
        print('BaoStock已登出')

if __name__ == '__main__':
    # 运行主程序
    results = cchan_trader_main(test_mode=True, max_stocks=30)