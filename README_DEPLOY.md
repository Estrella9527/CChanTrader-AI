# 🚀 CChanTrader-AI Railway 部署指南

## 📋 部署概述

本项目已配置为支持 Railway 免费层一键部署，包含完整的股票分析系统、Web界面和自动化分析功能。

## 🔧 部署文件说明

### 核心配置文件
- `Procfile` - Railway 进程定义
- `runtime.txt` - Python 版本指定 (3.9.19)
- `railway.toml` - Railway 平台配置
- `requirements.txt` - Python 依赖包列表

### 自动化配置
- `.github/workflows/trading-analysis.yml` - GitHub Actions 自动化分析

## 🚀 一键部署步骤

### 1. 准备 Railway 账户
```bash
# 访问 Railway 官网注册账户
https://railway.app

# 连接您的 GitHub 账户
```

### 2. 部署项目
```bash
# 方法1: 直接从 GitHub 部署
1. 在 Railway 控制台点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择本项目仓库
4. Railway 会自动识别配置文件并开始部署

# 方法2: 使用 Railway CLI
npm install -g @railway/cli
railway login
railway link
railway up
```

### 3. 配置环境变量
在 Railway 控制台设置以下环境变量：
```bash
PORT=8080
FLASK_ENV=production
PYTHONPATH=/app
```

### 4. 配置数据库持久化
Railway 会自动配置卷存储：
```toml
[volumes]
data = "/app/data"  # SQLite 数据库存储
```

## 📊 自动化分析配置

### GitHub Actions 工作流
项目配置了自动化股票分析：
- **触发时间**: 每个交易日 16:30 (中国时间)
- **分析范围**: 全市场股票筛选
- **输出结果**: 自动更新到数据库

### 设置 GitHub Secrets
在 GitHub 仓库设置中添加：
```bash
RAILWAY_TOKEN=your_railway_token_here
```

## 🌐 访问部署的应用

部署成功后：
```bash
# Railway 会提供一个公共URL，例如：
https://your-app-name.railway.app

# 主要页面：
- 股票推荐: https://your-app.railway.app/
- 策略配置: https://your-app.railway.app/strategy
- 分析历史: https://your-app.railway.app/history
```

## 💾 数据持久化

### SQLite 数据库
```bash
# 位置: /app/data/cchan_web.db
# 包含内容:
- 股票分析结果
- 推荐历史记录
- 策略配置参数
- 用户系统设置
```

### 备份策略
```bash
# Railway 会自动为卷存储创建备份
# 建议定期导出重要数据
```

## 🔍 监控与日志

### Railway 控制台监控
- CPU/内存使用情况
- 请求响应时间
- 错误日志查看

### 应用日志
```bash
# 在 Railway 控制台查看实时日志
# 包含股票分析进度和系统状态
```

## ⚠️ 免费层限制

### Railway 免费层配置
- **内存**: 512MB RAM
- **CPU**: 共享 vCPU
- **存储**: 1GB 持久化存储
- **带宽**: 100GB/月
- **运行时间**: 500小时/月

### 优化建议
```bash
# 1. 优化股票池大小
MAX_STOCKS = 50  # 减少分析股票数量

# 2. 调整分析频率
ANALYSIS_INTERVAL = 1800  # 30分钟间隔

# 3. 清理历史数据
AUTO_CLEANUP_DAYS = 30  # 自动清理30天前数据
```

## 🛠️ 故障排除

### 常见问题

#### 1. 部署失败
```bash
# 检查 requirements.txt 是否包含所有依赖
# 确认 Python 版本兼容性
# 查看 Railway 部署日志
```

#### 2. 数据库连接错误
```bash
# 检查 data/ 目录权限
# 确认 SQLite 文件路径正确
# 查看应用日志中的错误信息
```

#### 3. 分析功能异常
```bash
# 检查网络连接（BaoStock API）
# 确认股票代码格式正确
# 查看风险过滤配置
```

### 调试命令
```bash
# 本地测试部署配置
python3 backend/app.py

# 检查依赖安装
pip install -r requirements.txt

# 测试数据库连接
python3 -c "import sqlite3; print('SQLite OK')"
```

## 📈 性能优化

### 建议配置
```python
# backend/app.py 优化配置
STOCK_POOL_SIZE = 50        # 限制股票池大小
ANALYSIS_TIMEOUT = 300      # 5分钟超时
CACHE_RESULTS = True        # 启用结果缓存
MAX_RECOMMENDATIONS = 10    # 限制推荐数量
```

## 🔄 更新部署

### 自动更新
```bash
# GitHub 推送会自动触发 Railway 重新部署
git push origin main
```

### 手动更新
```bash
# 使用 Railway CLI
railway up
```

## 📞 技术支持

### 获取帮助
- Railway 官方文档: https://docs.railway.app
- GitHub Issues: 项目仓库问题跟踪
- 部署日志: Railway 控制台查看

### 监控建议
- 设置 Railway 告警通知
- 监控应用健康状态
- 定期检查数据库大小

---

## 🎯 部署成功确认

部署完成后，请验证以下功能：
- ✅ Web 界面正常访问
- ✅ 股票数据获取正常
- ✅ 分析结果显示正确
- ✅ 数据库读写正常
- ✅ 定时任务执行正常

**恭喜！您的 CChanTrader-AI 已成功部署到 Railway！** 🎉