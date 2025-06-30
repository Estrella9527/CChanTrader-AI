#!/bin/bash

# CChanTrader-AI 快速部署脚本
echo "🚀 CChanTrader-AI 快速部署到 Railway"
echo "=================================="

# 检查是否已经初始化 Git
if [ ! -d ".git" ]; then
    echo "❌ Git 仓库未初始化"
    exit 1
fi

# 检查是否有远程仓库
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️ 请先设置 GitHub 远程仓库："
    echo "git remote add origin https://github.com/YOUR_USERNAME/CChanTrader-AI.git"
    echo ""
    echo "创建 GitHub 仓库步骤："
    echo "1. 访问 https://github.com/new"
    echo "2. 仓库名: CChanTrader-AI"
    echo "3. 设为公开仓库"
    echo "4. 复制仓库 URL 并运行上述命令"
    exit 1
fi

# 提交最新更改
echo "📝 提交最新更改..."
git add .
git commit -m "Ready for Railway deployment - $(date '+%Y-%m-%d %H:%M:%S')"

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ 代码已成功推送到 GitHub"
    echo ""
    echo "🌐 现在请前往 Railway 控制台部署："
    echo "1. 访问: https://railway.app/dashboard"
    echo "2. 点击 'New Project'"
    echo "3. 选择 'Deploy from GitHub repo'"
    echo "4. 选择 CChanTrader-AI 仓库"
    echo "5. Railway 会自动检测配置文件并开始部署"
    echo ""
    echo "⚙️ 环境变量设置："
    echo "- PORT=8080"
    echo "- FLASK_ENV=production" 
    echo "- PYTHONPATH=/app"
    echo ""
    echo "📋 部署完成后您将获得一个公网 URL，例如："
    echo "https://cchantrader-ai-production.railway.app"
else
    echo "❌ 推送失败，请检查 GitHub 仓库设置"
fi