#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CChanTrader-AI 启动脚本
便捷启动方式
"""

import subprocess
import sys
import os

def main():
    print("🚀 启动 CChanTrader-AI...")
    print("📍 项目根目录:", os.getcwd())
    
    try:
        # 从项目根目录启动Flask应用
        subprocess.run([sys.executable, "backend/app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 已停止服务")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()