#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复项目中的硬编码路径问题
适配 Railway 部署环境
"""

import os
import re
import glob

def fix_hardcoded_paths():
    """修复所有 Python 文件中的硬编码路径"""
    
    # 查找所有 Python 文件
    python_files = []
    for root, dirs, files in os.walk('.'):
        # 跳过隐藏目录和 __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"🔍 找到 {len(python_files)} 个 Python 文件")
    
    # 定义需要替换的模式
    replacements = [
        # sys.path.append 修复
        (r"sys\.path\.append\(['\"]\/Users\/yang['\"]?\)", 
         "sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"),
        
        # 日志文件路径修复
        (r"['\"]\/Users\/yang\/[^'\"]*\.log['\"]", 
         "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', os.path.basename(match.group().strip('\\'\"')))"),
        
        # JSON 文件路径修复  
        (r"['\"]\/Users\/yang\/[^'\"]*\.json['\"]",
         "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', os.path.basename(match.group().strip('\\'\"')))"),
        
        # HTML 文件路径修复
        (r"['\"]\/Users\/yang\/[^'\"]*\.html['\"]",
         "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.path.basename(match.group().strip('\\'\"')))"),
        
        # 环境文件路径修复
        (r"['\"]\/Users\/yang\/\.env['\"]",
         "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')"),
    ]
    
    fixed_files = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 检查是否包含硬编码路径
            if '/Users/yang' in content:
                print(f"📝 修复文件: {file_path}")
                
                # 确保文件开头有必要的导入
                if 'import os' not in content and '/Users/yang' in content:
                    # 在适当位置添加 import os
                    import_pos = content.find('import ')
                    if import_pos != -1:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') and 'import os' not in content:
                                lines.insert(i, 'import os')
                                content = '\n'.join(lines)
                                break
                
                # 应用简单的替换
                content = content.replace("sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))", 
                                        "sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))")
                
                # 替换具体的文件路径
                content = re.sub(r"'/Users/yang/([^']*\.log)'", 
                               r"os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', '\1')", 
                               content)
                
                content = re.sub(r"'/Users/yang/([^']*\.json)'", 
                               r"os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', '\1')", 
                               content)
                
                content = re.sub(r"'/Users/yang/([^']*\.html)'", 
                               r"os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '\1')", 
                               content)
                
                content = content.replace("os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')", 
                                        "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')")
                
                # 只有内容发生变化时才写入
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(file_path)
                    print(f"   ✅ 已修复")
                
        except Exception as e:
            print(f"   ❌ 修复失败: {e}")
    
    print(f"\n🎉 完成! 共修复 {len(fixed_files)} 个文件")
    if fixed_files:
        print("修复的文件:")
        for file in fixed_files:
            print(f"  - {file}")

if __name__ == "__main__":
    print("🔧 开始修复硬编码路径...")
    fix_hardcoded_paths()
    print("✅ 路径修复完成!")