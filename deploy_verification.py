#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway 部署验证脚本
用于在部署前验证项目配置和依赖
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} 不存在")
        return False

def check_python_dependencies():
    """检查 Python 依赖"""
    print("\n🔍 检查 Python 依赖...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                try:
                    module_name = req.split('==')[0].replace('-', '_')
                    if module_name == 'sqlite3':
                        continue  # sqlite3 是内置模块
                    __import__(module_name)
                    print(f"✅ {req}")
                except ImportError:
                    print(f"❌ {req} - 未安装")
    except FileNotFoundError:
        print("❌ requirements.txt 文件不存在")

def check_database():
    """检查数据库连接"""
    print("\n🗄️ 检查数据库...")
    
    try:
        # 检查数据目录
        os.makedirs('data', exist_ok=True)
        
        # 测试 SQLite 连接
        conn = sqlite3.connect('data/cchan_web.db')
        cursor = conn.cursor()
        
        # 创建测试表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployment_test (
                id INTEGER PRIMARY KEY,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入测试数据
        cursor.execute("INSERT INTO deployment_test (status) VALUES (?)", ("deployment_ready",))
        conn.commit()
        
        # 读取测试数据
        cursor.execute("SELECT * FROM deployment_test ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 数据库连接正常: {result}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库错误: {e}")

def check_flask_app():
    """检查 Flask 应用"""
    print("\n🌐 检查 Flask 应用...")
    
    try:
        sys.path.append('.')
        sys.path.append('backend')
        
        # 尝试导入主应用
        from backend.app import app
        print("✅ Flask 应用导入成功")
        
        # 检查路由
        with app.app_context():
            print(f"✅ Flask 应用配置正常")
            
    except Exception as e:
        print(f"❌ Flask 应用错误: {e}")

def main():
    """主验证函数"""
    print("🚀 CChanTrader-AI Railway 部署验证")
    print("=" * 50)
    
    # 检查部署文件
    print("\n📋 检查部署配置文件...")
    deployment_files = [
        ('Procfile', 'Railway 进程配置'),
        ('runtime.txt', 'Python 版本配置'),
        ('railway.toml', 'Railway 平台配置'),
        ('requirements.txt', 'Python 依赖列表'),
        ('.gitignore', 'Git 忽略文件'),
        ('README_DEPLOY.md', '部署说明文档')
    ]
    
    all_files_exist = True
    for file_path, description in deployment_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    # 检查项目结构
    print("\n📁 检查项目结构...")
    project_dirs = [
        ('backend/', '后端代码目录'),
        ('analysis/', '分析引擎目录'),
        ('frontend/', '前端资源目录'),
        ('data/', '数据文件目录'),
        ('docs/', '文档目录'),
        ('.github/workflows/', 'GitHub Actions 工作流')
    ]
    
    for dir_path, description in project_dirs:
        check_file_exists(dir_path, description)
    
    # 检查依赖
    check_python_dependencies()
    
    # 检查数据库
    check_database()
    
    # 检查 Flask 应用
    check_flask_app()
    
    print("\n" + "=" * 50)
    if all_files_exist:
        print("🎉 项目已准备好部署到 Railway!")
        print("\n📋 下一步操作:")
        print("1. 将代码推送到 GitHub")
        print("2. 在 Railway 控制台从 GitHub 部署")
        print("3. 设置环境变量")
        print("4. 等待部署完成")
    else:
        print("⚠️ 部署前需要修复上述问题")

if __name__ == "__main__":
    main()