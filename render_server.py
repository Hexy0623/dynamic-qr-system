#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render部署专用服务器 - 适配云环境
"""

import os
import sys
import signal
import time
from integrated_qr_system import IntegratedQRSystem


def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在停止服务器...")
    sys.exit(0)


def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 从环境变量获取配置（Render会自动设置PORT）
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 10000))  # Render默认端口
    
    print(f"🌐 动态二维码服务器 - Render部署版")
    print(f"📡 监听地址: {host}:{port}")
    print(f"🆔 进程ID: {os.getpid()}")
    
    # 创建服务器实例
    qr_system = IntegratedQRSystem(host, port)
    
    try:
        if qr_system.start_server():
            print(f"✅ 服务器已启动")
            print(f"📊 管理 {len(qr_system.get_all_qr_codes())} 个二维码")
            print(f"🔄 服务器运行中...")
            
            # 持续运行
            while True:
                time.sleep(30)  # 每30秒检查一次
                
                # 检查服务器是否还在运行
                if not qr_system.is_server_running():
                    print("⚠️ 检测到服务器异常，尝试重启...")
                    if not qr_system.start_server():
                        print("❌ 服务器重启失败")
                        break
                    else:
                        print("✅ 服务器重启成功")
        else:
            print("❌ 服务器启动失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    except Exception as e:
        print(f"❌ 服务器运行异常: {e}")
        return 1
    finally:
        print("🛑 正在停止服务器...")
        qr_system.stop_server()
        print("✅ 服务器已停止")
    
    return 0


if __name__ == "__main__":
    exit(main())
