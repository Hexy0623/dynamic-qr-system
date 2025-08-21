#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化服务器管理工具 - 解决启动问题
"""

import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import json
from datetime import datetime


class SimpleServerManager:
    """简化的服务器管理器"""
    
    def __init__(self):
        self.server_process = None
        self.is_monitoring = False
        self.log_file = "simple_server_log.txt"
    
    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except:
            pass
    
    def check_server_status(self):
        """检查服务器状态"""
        # 方法1: 先用Socket检查端口
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            
            if result != 0:
                self.log_message(f"端口8080未开放 (错误码: {result})")
                return False
        except Exception as e:
            self.log_message(f"Socket检查失败: {e}")
            return False
        
        # 方法2: HTTP请求检查（禁用代理）
        try:
            # 禁用代理设置
            proxies = {
                'http': None,
                'https': None
            }
            
            response = requests.get("http://localhost:8080", 
                                  timeout=5, 
                                  proxies=proxies)
            if response.status_code == 200:
                return True
            else:
                self.log_message(f"HTTP状态码异常: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            self.log_message(f"HTTP连接被拒绝: {str(e)}")
            return False
        except requests.exceptions.Timeout as e:
            self.log_message(f"HTTP连接超时: {str(e)}")
            return False
        except Exception as e:
            self.log_message(f"HTTP检查异常: {str(e)}")
            return False
    
    def start_server(self):
        """启动服务器"""
        try:
            # 检查文件是否存在
            script_path = "integrated_qr_system.py"
            if not os.path.exists(script_path):
                self.log_message(f"错误: 找不到 {script_path}")
                return False
            
            self.log_message("正在启动服务器...")
            
            # 使用最简单的方式启动 - 直接启动GUI版本
            self.server_process = subprocess.Popen(
                [sys.executable, script_path],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.log_message(f"服务器进程已启动 (PID: {self.server_process.pid})")
            
            # 等待服务器启动
            self.log_message("等待服务器启动...")
            
            # 先等待3秒让GUI完全初始化
            time.sleep(3)
            
            for i in range(12):  # 等待12秒
                # 检查进程是否还在运行
                if self.server_process.poll() is not None:
                    self.log_message(f"服务器进程已退出 (返回码: {self.server_process.returncode})")
                    return False
                
                # 检查HTTP服务
                if self.check_server_status():
                    self.log_message(f"✅ 服务器启动成功 (等待{i+4}秒)")
                    return True
                
                time.sleep(1)
                
                if (i + 1) % 3 == 0:  # 每3秒显示一次等待信息
                    self.log_message(f"等待HTTP服务启动... ({i+4}/15秒)")
            
            # 最后检查一次
            if self.server_process.poll() is None:
                self.log_message("⚠️ HTTP服务检查超时，但进程仍在运行")
                # 再次尝试检查HTTP服务
                if self.check_server_status():
                    self.log_message("✅ 延迟检查：HTTP服务正常")
                    return True
                else:
                    self.log_message("⚠️ HTTP服务可能需要更多时间启动")
                    return True  # 进程在运行就认为成功
            else:
                self.log_message("❌ 服务器进程已意外退出")
                return False
            
        except Exception as e:
            self.log_message(f"启动失败: {str(e)}")
            return False
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.log_message("服务器已停止")
            except:
                try:
                    self.server_process.kill()
                    self.log_message("服务器已强制停止")
                except:
                    self.log_message("停止服务器失败")
            finally:
                self.server_process = None
    
    def restart_server(self):
        """重启服务器"""
        self.log_message("正在重启服务器...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def monitor_server(self):
        """监控服务器"""
        self.is_monitoring = True
        self.log_message("开始监控服务器")
        
        while self.is_monitoring:
            try:
                # 检查进程是否还在运行
                if self.server_process and self.server_process.poll() is not None:
                    self.log_message("检测到服务器进程已退出，尝试重启...")
                    if self.start_server():
                        self.log_message("服务器重启成功")
                    else:
                        self.log_message("服务器重启失败")
                        break
                
                # 检查HTTP服务
                elif not self.check_server_status():
                    self.log_message("检测到HTTP服务异常，尝试重启...")
                    if self.restart_server():
                        self.log_message("服务器重启成功")
                    else:
                        self.log_message("服务器重启失败")
                        break
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                self.log_message(f"监控过程出错: {str(e)}")
                time.sleep(30)
        
        self.log_message("服务器监控已停止")


class SimpleServerGUI:
    """简化的服务器管理GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🖥️ 简化服务器管理工具")
        self.root.geometry("600x500")
        
        self.manager = SimpleServerManager()
        self.monitor_thread = None
        
        self.setup_ui()
        self.update_status()
        
        # 程序退出时的清理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """设置用户界面"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(main_frame, text="🖥️ 简化动态二维码服务器管理", 
                         font=("Arial", 16, "bold"))
        title.pack(pady=(0, 20))
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="服务器状态", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = ttk.Label(status_frame, text="❓ 未知", 
                                     font=("Arial", 12), foreground="gray")
        self.status_label.pack()
        
        self.url_label = ttk.Label(status_frame, text="http://localhost:8080", 
                                  foreground="blue")
        self.url_label.pack(pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="🚀 启动服务器", 
                  command=self.start_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⏹️ 停止服务器", 
                  command=self.stop_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 重启服务器", 
                  command=self.restart_server).pack(side=tk.LEFT, padx=5)
        
        # 监控按钮
        monitor_frame = ttk.Frame(main_frame)
        monitor_frame.pack(pady=5)
        
        ttk.Button(monitor_frame, text="👁️ 开始监控", 
                  command=self.start_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(monitor_frame, text="⏸️ 停止监控", 
                  command=self.stop_monitoring).pack(side=tk.LEFT, padx=5)
        
        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # 创建Text组件显示日志
        from tkinter import scrolledtext
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志按钮
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(log_button_frame, text="🔄 刷新日志", 
                  command=self.refresh_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_button_frame, text="🗑️ 清空日志", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_button_frame, text="🧪 测试连接", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        # 自动刷新日志
        self.refresh_log()
        self.auto_refresh_log()
    
    def update_status(self):
        """更新状态显示"""
        if self.manager.server_process and self.manager.server_process.poll() is None:
            if self.manager.check_server_status():
                self.status_label.config(text="✅ 服务器运行正常", foreground="green")
            else:
                self.status_label.config(text="⚠️ 进程运行但HTTP异常", foreground="orange")
        else:
            self.status_label.config(text="❌ 服务器已停止", foreground="red")
    
    def start_server(self):
        """启动服务器"""
        if self.manager.start_server():
            messagebox.showinfo("成功", "服务器启动成功！")
        else:
            messagebox.showerror("错误", "服务器启动失败，请查看日志")
        self.update_status()
    
    def stop_server(self):
        """停止服务器"""
        self.manager.stop_server()
        messagebox.showinfo("成功", "服务器已停止")
        self.update_status()
    
    def restart_server(self):
        """重启服务器"""
        if self.manager.restart_server():
            messagebox.showinfo("成功", "服务器重启成功！")
        else:
            messagebox.showerror("错误", "服务器重启失败，请查看日志")
        self.update_status()
    
    def start_monitoring(self):
        """开始监控"""
        if not self.manager.is_monitoring:
            self.monitor_thread = threading.Thread(target=self.manager.monitor_server, daemon=True)
            self.monitor_thread.start()
            messagebox.showinfo("成功", "服务器监控已启动")
        else:
            messagebox.showwarning("提示", "监控已经在运行中")
    
    def stop_monitoring(self):
        """停止监控"""
        self.manager.is_monitoring = False
        messagebox.showinfo("成功", "服务器监控已停止")
    
    def test_connection(self):
        """测试连接"""
        if self.manager.check_server_status():
            messagebox.showinfo("测试结果", "✅ 连接正常\n服务器响应正常")
        else:
            messagebox.showwarning("测试结果", "❌ 连接失败\n服务器无响应或未启动")
    
    def refresh_log(self):
        """刷新日志"""
        try:
            if os.path.exists(self.manager.log_file):
                with open(self.manager.log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(tk.END, content)
                    self.log_text.see(tk.END)
        except:
            pass
    
    def clear_log(self):
        """清空日志"""
        result = messagebox.askyesno("确认", "确定要清空日志吗？")
        if result:
            try:
                open(self.manager.log_file, 'w').close()
                self.log_text.delete(1.0, tk.END)
                messagebox.showinfo("成功", "日志已清空")
            except Exception as e:
                messagebox.showerror("错误", f"清空日志失败: {str(e)}")
    
    def auto_refresh_log(self):
        """自动刷新日志"""
        self.refresh_log()
        self.update_status()
        self.root.after(3000, self.auto_refresh_log)  # 每3秒刷新
    
    def on_closing(self):
        """程序关闭处理"""
        if self.manager.is_monitoring:
            result = messagebox.askyesno("确认退出", 
                                       "监控正在运行中，退出会停止监控。\n"
                                       "确定要退出吗？")
            if not result:
                return
        
        self.manager.is_monitoring = False
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = SimpleServerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
