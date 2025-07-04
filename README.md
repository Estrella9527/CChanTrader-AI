# CChanTrader-AI 智能交易管理平台

## 🚀 快速启动

### 方法1：使用Python3 (推荐)
```bash
python3 backend/app.py
```

### 方法2：使用启动脚本
```bash
python3 run.py
# 或者
./run.sh
```

### 方法3：从backend目录启动
```bash
cd backend
python3 app.py
```

## 📂 项目结构

```
.
├── backend/           # 后端代码
│   ├── app.py         # Flask主应用
│   ├── routes/        # API路由
│   └── services/      # 邮件等服务
├── analysis/          # 分析引擎
├── frontend/          # 前端资源
│   ├── templates/     # HTML模板
│   └── static/        # CSS/JS/图片
├── data/             # 数据文件
├── config/           # 配置文件
└── docs/             # 文档
```

## 🌐 访问地址

启动成功后访问：
- http://localhost:8080
- http://127.0.0.1:8080

## ⚠️ 常见问题

1. **提示 "python command not found"**
   - 使用 `python3 backend/app.py` 替代

2. **模块导入错误**
   - 确保在项目根目录运行
   - 检查Python路径配置

3. **端口占用**
   - 修改 backend/app.py 中的端口号
   - 或先停止占用端口的进程

## 🛑 停止服务

按 `Ctrl+C` 停止服务