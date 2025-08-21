#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成动态二维码系统 - 快速启动脚本
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """检查依赖包"""
    required_packages = ['qrcode', 'PIL', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """安装依赖包"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except:
        return False

def main():
    """主函数"""
    print("🌐 集成动态二维码系统")
    print("=" * 40)
    
    # 检查依赖
    missing = check_dependencies()
    if missing:
        print(f"❌ 缺少依赖包: {', '.join(missing)}")
        print("🔄 正在自动安装...")
        
        if install_dependencies():
            print("✅ 依赖包安装成功")
        else:
            print("❌ 依赖包安装失败")
            print("请手动运行: pip install -r requirements.txt")
            input("按回车键退出...")
            return
    else:
        print("✅ 依赖包检查通过")
    
    # 启动系统
    print("🚀 正在启动集成系统...")
    
    try:
        from integrated_qr_system import main as start_system
        start_system()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        
        # 显示错误对话框
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动失败", 
                           f"系统启动失败:\n{str(e)}\n\n"
                           "请检查:\n"
                           "1. Python环境是否正确\n"
                           "2. 依赖包是否完整\n"
                           "3. 端口8080是否被占用")
        root.destroy()

if __name__ == "__main__":
    main()
