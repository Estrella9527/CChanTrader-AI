# A股集合竞价数据获取研究报告

## 📊 研究概述

本研究深入分析了A股集合竞价数据的获取方法，重点对比了BaoStock和AKShare两大数据源的能力，并提供了完整的实现方案。

## 🎯 核心发现

### 1. BaoStock 集合竞价数据支持情况
- **❌ 缺乏专门的集合竞价API**：BaoStock主要提供日K、周K、月K线数据
- **✅ 支持分钟级数据**：可获取5分钟、15分钟、30分钟、60分钟K线
- **⚠️ 间接获取**：开盘价可通过日K线的open字段获取，但无法获取竞价过程数据
- **数据字段**：date, code, open, high, low, close, preclose, volume, amount, adjustflag, turn, tradestatus, pctChg

### 2. AKShare 集合竞价数据支持情况
- **✅ 专门的盘前数据API**：`stock_zh_a_hist_pre_min_em`
- **✅ 分钟级竞价数据**：支持盘前分钟级数据获取
- **✅ 实时性强**：基于东方财富数据源，更新及时
- **数据源**：东方财富-股票行情-盘前数据

## 📋 数据字段结构分析

### AKShare 集合竞价数据字段
| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| 时间 | object | 时间戳（精确到分钟）|
| 开盘 | float64 | 开盘价 |
| 收盘 | float64 | 收盘价（分钟收盘）|
| 最高 | float64 | 最高价 |
| 最低 | float64 | 最低价 |
| 成交量 | float64 | 成交量（单位：手）|
| 成交额 | float64 | 成交额 |
| 最新价 | float64 | 最新价 |

### 集合竞价关键信息解读
1. **开盘价**：集合竞价最终确定的开盘价格
2. **竞价量**：通过成交量字段体现竞价期间的成交数量
3. **价格区间**：最高价和最低价反映竞价价格波动范围
4. **时间窗口**：9:15-9:25为集合竞价时间，9:25-9:30为静默期

## ⏰ 数据获取时间窗口

### A股集合竞价时间安排
- **9:15-9:20**：接受委托买单和卖单，可以撤销
- **9:20-9:25**：接受委托买单和卖单，不可撤销
- **9:25-9:30**：不接受委托，为开盘前的静默期
- **14:57-15:00**：收盘集合竞价

### 数据可用性分析
- **BaoStock**：当日收盘后可获取开盘价数据
- **AKShare**：可获取盘前分钟级数据，包含竞价过程
- **更新频率**：AKShare提供近实时数据，BaoStock为日级更新

## 🔧 完整代码实现

### 1. AKShare集合竞价数据获取器
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare集合竞价数据获取器
获取A股集合竞价相关数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time

class AuctionDataProvider:
    """集合竞价数据提供器"""
    
    def __init__(self):
        self.name = "AKShare集合竞价数据提供器"
        print(f"初始化 {self.name}")
    
    def get_auction_data(self, symbol, trading_date=None):
        """
        获取指定股票的集合竞价数据
        
        Args:
            symbol (str): 股票代码，如 "000001"
            trading_date (str): 交易日期，格式YYYY-MM-DD，默认为最新交易日
        
        Returns:
            dict: 包含竞价数据的字典
        """
        try:
            # 获取盘前分钟数据
            pre_market_df = ak.stock_zh_a_hist_pre_min_em(
                symbol=symbol,
                start_time="09:00:00",
                end_time="09:30:00"
            )
            
            if pre_market_df.empty:
                return None
            
            # 筛选集合竞价时间段数据 (9:15-9:25)
            auction_data = pre_market_df[
                (pre_market_df['时间'].str.contains('09:1[5-9]|09:2[0-5]'))
            ].copy()
            
            if auction_data.empty:
                return None
            
            # 获取开盘价（9:25的收盘价即为开盘价）
            opening_data = auction_data[auction_data['时间'].str.contains('09:25')]
            opening_price = opening_data['收盘'].iloc[-1] if not opening_data.empty else None
            
            # 计算竞价统计数据
            total_volume = auction_data['成交量'].sum()
            total_amount = auction_data['成交额'].sum()
            price_high = auction_data['最高'].max()
            price_low = auction_data['最低'].min()
            
            result = {
                'symbol': symbol,
                'trading_date': auction_data['时间'].iloc[-1][:10] if len(auction_data) > 0 else None,
                'opening_price': float(opening_price) if opening_price else None,
                'auction_high': float(price_high),
                'auction_low': float(price_low),
                'total_auction_volume': int(total_volume),
                'total_auction_amount': float(total_amount),
                'auction_detail': auction_data.to_dict('records'),
                'data_source': 'AKShare-EastMoney'
            }
            
            return result
            
        except Exception as e:
            print(f"获取{symbol}集合竞价数据失败: {e}")
            return None
    
    def get_multiple_stocks_auction(self, stock_list):
        """
        批量获取多只股票的集合竞价数据
        
        Args:
            stock_list (list): 股票代码列表
        
        Returns:
            dict: 包含所有股票竞价数据的字典
        """
        results = {}
        
        for symbol in stock_list:
            print(f"正在获取 {symbol} 的集合竞价数据...")
            
            data = self.get_auction_data(symbol)
            if data:
                results[symbol] = data
                
            # 避免请求过于频繁
            time.sleep(0.5)
        
        return results
    
    def analyze_auction_signals(self, auction_data):
        """
        分析集合竞价信号
        
        Args:
            auction_data (dict): 竞价数据
        
        Returns:
            dict: 分析结果
        """
        if not auction_data or not auction_data.get('auction_detail'):
            return None
        
        detail = auction_data['auction_detail']
        opening_price = auction_data['opening_price']
        
        # 竞价趋势分析
        if len(detail) >= 2:
            first_price = detail[0]['收盘']
            last_price = detail[-1]['收盘']
            trend = 'up' if last_price > first_price else 'down' if last_price < first_price else 'flat'
        else:
            trend = 'insufficient_data'
        
        # 成交量集中度分析
        total_volume = sum(item['成交量'] for item in detail)
        last_minute_volume = detail[-1]['成交量'] if detail else 0
        volume_concentration = (last_minute_volume / total_volume * 100) if total_volume > 0 else 0
        
        # 价格波动分析
        price_volatility = (auction_data['auction_high'] - auction_data['auction_low']) / opening_price * 100 if opening_price else 0
        
        analysis = {
            'trend': trend,
            'volume_concentration_pct': round(volume_concentration, 2),
            'price_volatility_pct': round(price_volatility, 2),
            'signal_strength': 'strong' if volume_concentration > 50 and price_volatility > 1 else 'weak',
            'recommendation': self._generate_recommendation(trend, volume_concentration, price_volatility)
        }
        
        return analysis
    
    def _generate_recommendation(self, trend, vol_concentration, volatility):
        """生成交易建议"""
        if trend == 'up' and vol_concentration > 50 and volatility > 1:
            return 'strong_buy_signal'
        elif trend == 'up' and vol_concentration > 30:
            return 'buy_signal'
        elif trend == 'down' and vol_concentration > 50:
            return 'strong_sell_signal'
        elif trend == 'down' and vol_concentration > 30:
            return 'sell_signal'
        else:
            return 'wait_and_see'

# 使用示例
if __name__ == "__main__":
    provider = AuctionDataProvider()
    
    # 测试股票列表
    test_stocks = ["000001", "000002", "600000", "600036"]
    
    print("=== 批量获取集合竞价数据 ===")
    auction_results = provider.get_multiple_stocks_auction(test_stocks)
    
    for symbol, data in auction_results.items():
        print(f"\n股票: {symbol}")
        print(f"开盘价: {data['opening_price']}")
        print(f"竞价成交量: {data['total_auction_volume']} 手")
        print(f"竞价成交额: {data['total_auction_amount']:.2f} 元")
        
        # 分析竞价信号
        analysis = provider.analyze_auction_signals(data)
        if analysis:
            print(f"趋势: {analysis['trend']}")
            print(f"成交量集中度: {analysis['volume_concentration_pct']}%")
            print(f"价格波动率: {analysis['price_volatility_pct']}%")
            print(f"交易建议: {analysis['recommendation']}")
```

### 2. BaoStock开盘价数据获取器（补充方案）
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaoStock开盘价数据获取器
虽然无法获取竞价过程，但可获取开盘价用于分析
"""

import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

class BaoStockOpeningProvider:
    """BaoStock开盘价数据提供器"""
    
    def __init__(self):
        self.name = "BaoStock开盘价数据提供器"
        self.login_result = bs.login()
        print(f"BaoStock登录: {self.login_result.error_msg}")
    
    def get_opening_data(self, symbol, days=5):
        """
        获取最近几天的开盘价数据
        
        Args:
            symbol (str): 股票代码，如 "sh.600000"
            days (int): 获取天数
        
        Returns:
            pd.DataFrame: 包含开盘价等数据的DataFrame
        """
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            # 获取K线数据
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,preclose,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"  # 不复权
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'pctChg']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 过滤掉无效数据
            df = df.dropna().tail(days)
            
            return df
            
        except Exception as e:
            print(f"获取{symbol}开盘价数据失败: {e}")
            return pd.DataFrame()
    
    def analyze_opening_gaps(self, df):
        """
        分析开盘缺口
        
        Args:
            df (pd.DataFrame): 股票数据
        
        Returns:
            dict: 缺口分析结果
        """
        if df.empty or len(df) < 2:
            return None
        
        gaps = []
        for i in range(1, len(df)):
            prev_close = df.iloc[i-1]['close']
            current_open = df.iloc[i]['open']
            
            gap_pct = (current_open - prev_close) / prev_close * 100
            gap_type = 'up' if gap_pct > 0.5 else 'down' if gap_pct < -0.5 else 'normal'
            
            gaps.append({
                'date': df.iloc[i]['date'],
                'gap_pct': round(gap_pct, 2),
                'gap_type': gap_type,
                'prev_close': prev_close,
                'open_price': current_open
            })
        
        return gaps
    
    def __del__(self):
        """析构函数，登出BaoStock"""
        try:
            bs.logout()
        except:
            pass

# 使用示例
if __name__ == "__main__":
    provider = BaoStockOpeningProvider()
    
    # 测试股票
    test_symbol = "sh.600000"
    
    print(f"=== 获取{test_symbol}开盘价数据 ===")
    data = provider.get_opening_data(test_symbol, days=5)
    
    if not data.empty:
        print(data[['date', 'open', 'close', 'pctChg']])
        
        # 分析开盘缺口
        gaps = provider.analyze_opening_gaps(data)
        if gaps:
            print("\n=== 开盘缺口分析 ===")
            for gap in gaps:
                print(f"{gap['date']}: {gap['gap_type']} gap {gap['gap_pct']}%")
```

## 📊 数据准确性对比

### AKShare优势
1. **✅ 实时性**：基于东方财富，数据更新及时
2. **✅ 完整性**：提供完整的竞价过程数据
3. **✅ 细粒度**：分钟级数据，可看到竞价动态
4. **✅ 字段丰富**：包含成交量、成交额等关键信息

### BaoStock优势
1. **✅ 稳定性**：接口稳定，较少出现中断
2. **✅ 历史数据**：提供长期历史数据
3. **✅ 免费使用**：完全免费，无使用限制
4. **✅ 数据质量**：基础数据准确可靠

## 🎯 推荐方案

### 最佳实践：双数据源策略
1. **主要数据源**：使用AKShare获取集合竞价详细数据
2. **备用数据源**：使用BaoStock获取开盘价和基础K线数据
3. **数据验证**：交叉验证两个数据源的开盘价数据
4. **容错机制**：当一个数据源失效时自动切换

### 实际应用建议
1. **实时监控**：使用AKShare监控盘前竞价情况
2. **历史分析**：结合BaoStock的历史数据进行回测
3. **信号生成**：基于竞价成交量和价格变化生成交易信号
4. **风险控制**：通过竞价数据判断市场情绪和流动性

## 📈 实际应用场景

### 1. 集合竞价交易策略
- 监控竞价成交量异常放大的股票
- 分析竞价价格趋势判断开盘方向
- 识别大单参与的集合竞价信号

### 2. 开盘缺口分析
- 计算开盘价与前收盘价的缺口
- 分析缺口类型（上跳、下跳、平开）
- 制定缺口填补交易策略

### 3. 市场情绪判断
- 通过整体竞价成交量判断市场活跃度
- 分析竞价价格分布判断多空力量
- 识别市场恐慌或贪婪情绪

## 🔧 技术实现要点

### 数据获取频率控制
```python
import time

def rate_limited_request(func, delay=0.5):
    """限制请求频率的装饰器"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        time.sleep(delay)
        return result
    return wrapper
```

### 错误处理机制
```python
def safe_data_request(func, max_retries=3):
    """安全数据请求，带重试机制"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)
```

### 数据缓存策略
```python
import pickle
from datetime import datetime

def cache_data(data, filename):
    """缓存数据到本地文件"""
    with open(f"/tmp/{filename}_{datetime.now().strftime('%Y%m%d')}.pkl", 'wb') as f:
        pickle.dump(data, f)
```

## 📋 总结与建议

### 核心结论
1. **AKShare是获取集合竞价数据的最佳选择**，提供完整的盘前分钟级数据
2. **BaoStock适合作为补充数据源**，提供稳定的开盘价和历史数据
3. **双数据源策略能够最大化数据可靠性和完整性**

### 实施建议
1. **立即行动**：集成AKShare的`stock_zh_a_hist_pre_min_em`接口
2. **分步实施**：先实现基础功能，再扩展高级分析
3. **持续优化**：根据实际使用情况调整数据获取策略

### 后续扩展
1. **实时数据流**：考虑集成实时数据推送
2. **机器学习**：基于竞价数据训练预测模型
3. **可视化分析**：开发竞价数据可视化工具
4. **量化策略**：将竞价分析集成到现有交易策略中

---

**注意**：本研究仅用于学术和技术研究目的，投资决策请基于专业分析和风险评估。