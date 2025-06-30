# CChanTrader-AI 策略解释功能使用说明

## 🎯 功能概述

新增的策略解释功能为每只推荐股票提供详细的自然语言说明，包括：
- 📊 推荐理由和技术分析
- 💰 买入卖出策略建议
- ⚖️ 风险收益比分析
- 🎯 目标价格和止损位

## 🚀 使用方法

### 1. Web界面使用
1. 访问推荐页面：`http://localhost:8080/recommendations`
2. 查看新增的"策略解释"列
3. 点击"查看详情"按钮弹出详细解释模态框

### 2. API调用
```bash
# 获取带解释的推荐列表
curl http://localhost:8080/api/picks

# 带参数调用
curl "http://localhost:8080/api/picks?limit=5&confidence=very_high"
```

### 3. 程序化调用
```python
from optimized_stock_analyzer import OptimizedStockAnalyzer
from explain_generator import generate_explain

# 生成推荐（已自动包含解释）
analyzer = OptimizedStockAnalyzer()
result = analyzer.generate_optimized_recommendations()

# 手动生成解释（如需自定义）
recommendations = result['recommendations']
explanations = generate_explain(recommendations)
```

## 📊 解释内容结构

每只股票的解释包含：

### 基本信息
- 股票代码和名称
- 当前价格和信心等级
- 综合评分

### 推荐理由
- 技术面分析
- 竞价表现
- 信号类型说明

### 买卖策略
- 买入时机和价位
- 卖出策略和止损
- 目标价格区间

### 风险收益
- 预期收益率
- 风险收益比
- 持仓建议

## 🔧 技术实现

### 新增文件
- `explain_generator.py` - 解释生成核心逻辑
- `test_explain_integration.py` - 集成测试脚本

### 修改文件
- `optimized_stock_analyzer.py` - 集成解释生成
- `web_app.py` - 新增API端点
- `templates/recommendations.html` - 前端界面增强
- `cchan_web.db` - 数据库表结构扩展

### 数据库变更
- `stock_analysis`表新增`explanation`字段
- 自动保存解释到数据库

## 🎨 界面特性

### 表格视图
- 策略解释列显示简要说明
- 点击"查看详情"展开完整解释

### 模态框设计
- 分模块展示：基本信息、推荐理由、买卖策略、风险收益
- 使用颜色区分不同类型信息
- 响应式设计，支持移动端

## ⚙️ 配置选项

解释生成器支持的自定义配置：
- 目标价格倍数（基于信心等级）
- 风险收益比计算方式
- 解释模板和措辞风格

## 🔍 示例输出

```
推荐理由：顺利办(深圳主板)：技术形态良好，竞价高开4.4%显示资金关注，
综合评分优秀，技术面强势表现。建议16.15元附近买入，止损14.7元，
目标17.77-19.06元。

买入建议：等待价格突破中枢上沿时买入，开盘高开可跟进，可积极建仓，
参考价位16.15元。

卖出策略：价格达到19.06元附近时分批止盈；出现技术破位或二卖信号时止损；
跌破14.7元坚决止损；可适当放宽止盈目标。

风险收益：预期收益10-18%，潜在风险9%，风险收益比1:2.91。
风险收益比良好，值得关注。
```

## 🛡️ 风险提示

- 所有解释仅供参考，不构成投资建议
- 请结合个人风险偏好谨慎操作
- 市场有风险，投资需谨慎

---

**CChanTrader-AI** - 让AI为您的投资决策提供更智能的解释！