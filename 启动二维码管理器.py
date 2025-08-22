#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二维码管理器启动脚本
"""

import subprocess
import sys
import os

def check_dependencies():
    """检查依赖"""
    try:
        import qrcode
        import requests
        import tkinter
        return True
    except ImportError:
        return False

def install_dependencies():
    """安装依赖"""
    print("📦 正在安装依赖库...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_local.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """主函数"""
    print("🚀 启动二维码管理器...")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 检测到缺少依赖库")
        
        if input("是否自动安装依赖？(y/n): ").lower() == 'y':
            if install_dependencies():
                print("✅ 依赖安装成功")
            else:
                print("❌ 依赖安装失败，请手动运行: pip install -r requirements_local.txt")
                return 1
        else:
            print("请手动安装依赖: pip install -r requirements_local.txt")
            return 1
    
    # 启动管理器
    try:
        from qr_manager_local import main as qr_main
        return qr_main()
    except ImportError:
        print("❌ 找不到二维码管理器模块")
        return 1

if __name__ == "__main__":
    exit(main())
