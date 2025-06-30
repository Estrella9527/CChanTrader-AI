#!/bin/bash
# CChanTrader-AI 启动脚本

echo "🚀 启动 CChanTrader-AI..."
echo "📍 项目根目录: $(pwd)"

# 检查Python版本
if command -v python3 &> /dev/null; then
    echo "✅ 使用 python3"
    python3 backend/app.py
elif command -v python &> /dev/null; then
    echo "✅ 使用 python"
    python backend/app.py
else
    echo "❌ 未找到Python，请安装Python 3.7+"
    exit 1
fi