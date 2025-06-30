#!/bin/bash
echo "🚀 启动 Flask 服务..."

# 设置 Python 路径（确保模块引用无误）
export PYTHONPATH=/app

# 设置环境为生产模式
export FLASK_ENV=production

# 启动 Flask 应用
python3 backend/app.py

