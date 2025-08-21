#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络配置助手 - 帮助用户配置网络部署
"""

import socket
import subprocess
import platform
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os


class NetworkHelper:
    """网络配置助手"""
    
    def __init__(self):
        self.system = platform.system()
        self.local_ip = None
        self.public_ip = None
        self.network_info = {}
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 方法1：连接外部地址获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
                # 方法2：获取主机名对应的IP
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except:
                return "127.0.0.1"
    
    def get_public_ip(self):
        """获取公网IP地址"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            try:
                response = requests.get('https://httpbin.org/ip', timeout=5)
                return response.json()['origin']
            except:
                return "无法获取"
    
    def get_network_interfaces(self):
        """获取网络接口信息"""
        interfaces = []
        try:
            if self.system == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
                # 解析Windows ipconfig输出
                lines = result.stdout.split('\n')
                current_adapter = None
                for line in lines:
                    line = line.strip()
                    if '适配器' in line or 'adapter' in line.lower():
                        current_adapter = line
                    elif 'IPv4' in line and ':' in line:
                        ip = line.split(':')[-1].strip()
                        if ip and ip != '127.0.0.1':
                            interfaces.append({
                                'name': current_adapter or 'Unknown',
                                'ip': ip
                            })
            else:
                # Linux/Mac
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                # 简单解析ifconfig输出
                pass
        except:
            pass
        
        return interfaces
    
    def test_port(self, host, port):
        """测试端口是否可访问"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_network_devices(self, network_base="192.168.1"):
        """扫描局域网设备"""
        devices = []
        try:
            for i in range(1, 255):
                ip = f"{network_base}.{i}"
                # 简单的ping测试
                if self.system == "Windows":
                    cmd = ['ping', '-n', '1', '-w', '1000', ip]
                else:
                    cmd = ['ping', '-c', '1', '-W', '1', ip]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=2)
                    if result.returncode == 0:
                        devices.append(ip)
                except:
                    pass
        except:
            pass
        
        return devices
    
    def generate_qr_url(self, host, port=8080, qr_id="example"):
        """生成二维码URL"""
        return f"http://{host}:{port}/qr/{qr_id}"
    
    def save_network_config(self, config):
        """保存网络配置"""
        with open('network_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_network_config(self):
        """加载网络配置"""
        try:
            with open('network_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}


class NetworkHelperGUI:
    """网络配置助手GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 网络配置助手")
        self.root.geometry("800x700")
        
        self.helper = NetworkHelper()
        self.setup_ui()
        
        # 自动检测网络信息
        self.detect_network()
    
    def setup_ui(self):
        """设置用户界面"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 网络检测页面
        self.setup_detection_tab(notebook)
        
        # 部署方案页面
        self.setup_deployment_tab(notebook)
        
        # 配置生成页面
        self.setup_config_tab(notebook)
        
        # 测试页面
        self.setup_test_tab(notebook)
    
    def setup_detection_tab(self, notebook):
        """网络检测页面"""
        detection_frame = ttk.Frame(notebook)
        notebook.add(detection_frame, text="🔍 网络检测")
        
        # 标题
        title = ttk.Label(detection_frame, text="网络环境检测", font=("Arial", 14, "bold"))
        title.pack(pady=(10, 20))
        
        # 检测结果区域
        result_frame = ttk.LabelFrame(detection_frame, text="检测结果", padding="15")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 本机IP
        self.local_ip_frame = ttk.Frame(result_frame)
        self.local_ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.local_ip_frame, text="🏠 本机IP地址:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.local_ip_label = ttk.Label(self.local_ip_frame, text="检测中...", foreground="blue")
        self.local_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(self.local_ip_frame, text="复制", 
                  command=lambda: self.copy_to_clipboard(self.local_ip_label.cget("text"))).pack(side=tk.RIGHT)
        
        # 公网IP
        self.public_ip_frame = ttk.Frame(result_frame)
        self.public_ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.public_ip_frame, text="🌐 公网IP地址:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.public_ip_label = ttk.Label(self.public_ip_frame, text="检测中...", foreground="blue")
        self.public_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(self.public_ip_frame, text="复制", 
                  command=lambda: self.copy_to_clipboard(self.public_ip_label.cget("text"))).pack(side=tk.RIGHT)
        
        # 网络接口
        interface_frame = ttk.LabelFrame(result_frame, text="网络接口", padding="10")
        interface_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.interface_text = scrolledtext.ScrolledText(interface_frame, height=8, width=70)
        self.interface_text.pack(fill=tk.BOTH, expand=True)
        
        # 操作按钮
        button_frame = ttk.Frame(detection_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="🔄 重新检测", 
                  command=self.detect_network).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📋 生成配置", 
                  command=self.generate_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🧪 测试连接", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
    
    def setup_deployment_tab(self, notebook):
        """部署方案页面"""
        deploy_frame = ttk.Frame(notebook)
        notebook.add(deploy_frame, text="🚀 部署方案")
        
        # 方案选择
        scheme_frame = ttk.LabelFrame(deploy_frame, text="选择部署方案", padding="15")
        scheme_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.deploy_var = tk.StringVar(value="local")
        
        schemes = [
            ("local", "🏠 局域网部署", "免费，适合办公室/家庭使用"),
            ("cloud", "☁️ 云服务器", "付费，适合正式使用"),
            ("tunnel", "🔗 内网穿透", "免费/低费用，适合测试"),
            ("free", "🆓 免费托管", "免费，适合小规模使用")
        ]
        
        for value, title, desc in schemes:
            frame = ttk.Frame(scheme_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Radiobutton(frame, text=title, variable=self.deploy_var, 
                           value=value).pack(side=tk.LEFT)
            ttk.Label(frame, text=f" - {desc}", foreground="gray").pack(side=tk.LEFT)
        
        # 配置详情
        detail_frame = ttk.LabelFrame(deploy_frame, text="配置详情", padding="15")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.deploy_text = scrolledtext.ScrolledText(detail_frame, height=15)
        self.deploy_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        ttk.Button(deploy_frame, text="📖 查看详细说明", 
                  command=self.show_deployment_details).pack(pady=10)
    
    def setup_config_tab(self, notebook):
        """配置生成页面"""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ 配置生成")
        
        # 服务器配置
        server_frame = ttk.LabelFrame(config_frame, text="服务器配置", padding="15")
        server_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(server_frame, text="服务器地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_host_var = tk.StringVar()
        self.server_host_entry = ttk.Entry(server_frame, textvariable=self.server_host_var, width=30)
        self.server_host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(server_frame, text="端口:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.server_port_var = tk.StringVar(value="8080")
        ttk.Entry(server_frame, textvariable=self.server_port_var, width=30).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        server_frame.columnconfigure(1, weight=1)
        
        # 生成的配置
        generated_frame = ttk.LabelFrame(config_frame, text="生成的启动命令", padding="15")
        generated_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(generated_frame, height=12)
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="🔄 使用本机IP", 
                  command=self.use_local_ip).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📋 生成命令", 
                  command=self.generate_commands).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="💾 保存配置", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
    
    def setup_test_tab(self, notebook):
        """测试页面"""
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="🧪 连接测试")
        
        # 测试配置
        test_config_frame = ttk.LabelFrame(test_frame, text="测试配置", padding="15")
        test_config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(test_config_frame, text="测试地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.test_url_var = tk.StringVar()
        ttk.Entry(test_config_frame, textvariable=self.test_url_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        test_config_frame.columnconfigure(1, weight=1)
        
        # 测试按钮
        button_frame = ttk.Frame(test_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="🔌 测试连接", 
                  command=self.test_url_connection).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📱 生成测试二维码", 
                  command=self.generate_test_qr).pack(side=tk.LEFT, padx=5)
        
        # 测试结果
        result_frame = ttk.LabelFrame(test_frame, text="测试结果", padding="15")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.test_result_text = scrolledtext.ScrolledText(result_frame, height=15)
        self.test_result_text.pack(fill=tk.BOTH, expand=True)
    
    def detect_network(self):
        """检测网络信息"""
        def detect():
            # 检测本机IP
            local_ip = self.helper.get_local_ip()
            self.root.after(0, lambda: self.local_ip_label.config(text=local_ip))
            
            # 检测公网IP
            public_ip = self.helper.get_public_ip()
            self.root.after(0, lambda: self.public_ip_label.config(text=public_ip))
            
            # 获取网络接口
            interfaces = self.helper.get_network_interfaces()
            interface_info = "网络接口信息:\n\n"
            
            if interfaces:
                for i, interface in enumerate(interfaces, 1):
                    interface_info += f"{i}. {interface['name']}\n"
                    interface_info += f"   IP地址: {interface['ip']}\n\n"
            else:
                interface_info += "无法获取详细网络接口信息\n\n"
            
            interface_info += f"推荐配置:\n"
            interface_info += f"- 局域网访问: http://{local_ip}:8080\n"
            interface_info += f"- 服务器启动: python real_dynamic_qr.py --host 0.0.0.0 --port 8080\n"
            
            self.root.after(0, lambda: self.update_interface_text(interface_info))
            
            # 更新服务器地址
            self.root.after(0, lambda: self.server_host_var.set(local_ip))
            self.root.after(0, lambda: self.test_url_var.set(f"http://{local_ip}:8080"))
        
        # 在后台线程中执行检测
        threading.Thread(target=detect, daemon=True).start()
    
    def update_interface_text(self, text):
        """更新接口信息文本"""
        self.interface_text.delete(1.0, tk.END)
        self.interface_text.insert(1.0, text)
    
    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        if text and text != "检测中..." and text != "无法获取":
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("成功", f"已复制到剪贴板: {text}")
        else:
            messagebox.showwarning("提示", "没有可复制的内容")
    
    def generate_config(self):
        """生成配置"""
        local_ip = self.local_ip_label.cget("text")
        if local_ip and local_ip != "检测中...":
            config = {
                'local_ip': local_ip,
                'public_ip': self.public_ip_label.cget("text"),
                'recommended_host': local_ip,
                'recommended_port': 8080,
                'server_url': f"http://{local_ip}:8080"
            }
            
            self.helper.save_network_config(config)
            messagebox.showinfo("成功", "配置已保存到 network_config.json")
        else:
            messagebox.showwarning("提示", "请先完成网络检测")
    
    def test_connection(self):
        """测试连接"""
        local_ip = self.local_ip_label.cget("text")
        if local_ip and local_ip != "检测中...":
            port = int(self.server_port_var.get())
            
            def test():
                result = self.helper.test_port(local_ip, port)
                status = "✅ 连接成功" if result else "❌ 连接失败"
                message = f"测试地址: {local_ip}:{port}\n状态: {status}\n"
                
                if not result:
                    message += "\n可能的原因:\n"
                    message += "- 服务器未启动\n"
                    message += "- 端口被防火墙阻止\n"
                    message += "- 端口被其他程序占用\n"
                
                self.root.after(0, lambda: messagebox.showinfo("测试结果", message))
            
            threading.Thread(target=test, daemon=True).start()
        else:
            messagebox.showwarning("提示", "请先完成网络检测")
    
    def show_deployment_details(self):
        """显示部署详情"""
        scheme = self.deploy_var.get()
        details = {
            "local": """🏠 局域网部署详细说明:

1. 启动服务器:
   python real_dynamic_qr.py --host 0.0.0.0 --port 8080 --gui

2. 获取本机IP地址 (已自动检测):
   """ + self.local_ip_label.cget("text") + """

3. 二维码URL格式:
   http://""" + self.local_ip_label.cget("text") + """:8080/qr/xxx

4. 适用场景:
   - 办公室内部使用
   - 家庭网络环境
   - 同一WiFi下的设备

5. 注意事项:
   - 电脑需要保持开机
   - 确保防火墙允许8080端口
   - 只有同网络用户能访问""",

            "cloud": """☁️ 云服务器部署详细说明:

1. 推荐服务商:
   - 阿里云ECS: 约￥100/年
   - 腾讯云CVM: 约￥95/年
   - 华为云ECS: 约￥99/年

2. 服务器配置:
   - 1核2G内存即可
   - Ubuntu 20.04系统
   - 开放8080端口

3. 部署步骤:
   # 连接服务器
   ssh root@你的服务器IP
   
   # 安装依赖
   apt update && apt install python3 python3-pip -y
   pip3 install qrcode[pil] pillow
   
   # 上传代码并启动
   python3 real_dynamic_qr.py --host 0.0.0.0 --port 8080

4. 优点:
   - 全球访问
   - 24小时运行
   - 稳定可靠""",

            "tunnel": """🔗 内网穿透详细说明:

1. ngrok (国外):
   - 注册: https://ngrok.com
   - 下载客户端
   - 启动: ngrok http 8080
   - 获得: https://xxx.ngrok.io

2. 花生壳 (国内):
   - 注册: https://hsk.oray.com
   - 下载客户端
   - 配置穿透规则

3. frp (免费开源):
   - 需要有公网IP的服务器
   - 配置frps和frpc
   - 完全免费但需要技术基础

4. 优点:
   - 快速测试
   - 无需购买服务器
   - 即时获得公网访问""",

            "free": """🆓 免费托管详细说明:

1. Railway (推荐):
   - 网站: https://railway.app
   - 每月500小时免费
   - 支持GitHub自动部署

2. Render:
   - 网站: https://render.com
   - 每月750小时免费
   - 简单易用

3. Heroku:
   - 需要信用卡验证
   - 功能强大
   - 社区支持好

4. 部署步骤:
   - 将代码上传到GitHub
   - 连接到托管平台
   - 自动构建和部署

5. 限制:
   - 有使用时间限制
   - 性能相对较低
   - 可能有地域限制"""
        }
        
        self.deploy_text.delete(1.0, tk.END)
        self.deploy_text.insert(1.0, details.get(scheme, "请选择部署方案"))
    
    def use_local_ip(self):
        """使用本机IP"""
        local_ip = self.local_ip_label.cget("text")
        if local_ip and local_ip != "检测中...":
            self.server_host_var.set(local_ip)
            self.test_url_var.set(f"http://{local_ip}:{self.server_port_var.get()}")
        else:
            messagebox.showwarning("提示", "请先完成网络检测")
    
    def generate_commands(self):
        """生成启动命令"""
        host = self.server_host_var.get()
        port = self.server_port_var.get()
        
        if not host:
            messagebox.showwarning("提示", "请输入服务器地址")
            return
        
        commands = f"""🚀 服务器启动命令:

1. 启动GUI管理界面 (推荐):
   python real_dynamic_qr.py --host 0.0.0.0 --port {port} --gui

2. 仅启动服务器:
   python real_dynamic_qr.py --host 0.0.0.0 --port {port}

3. 服务器访问地址:
   http://{host}:{port}

4. 二维码URL格式:
   http://{host}:{port}/qr/[二维码ID]

5. Windows防火墙设置 (如需要):
   netsh advfirewall firewall add rule name="QR Server" dir=in action=allow protocol=TCP localport={port}

6. 测试连接:
   在浏览器中访问: http://{host}:{port}
   
📋 配置信息:
- 服务器地址: {host}
- 端口: {port}
- 协议: HTTP
- 状态: {"✅ 已配置" if host else "❌ 未配置"}

🔧 故障排除:
- 确保端口{port}未被占用
- 检查防火墙设置
- 确认网络连接正常
- 验证Python环境和依赖包"""

        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, commands)
    
    def save_config(self):
        """保存配置"""
        host = self.server_host_var.get()
        port = self.server_port_var.get()
        
        if not host:
            messagebox.showwarning("提示", "请输入服务器地址")
            return
        
        config = {
            'server_host': host,
            'server_port': int(port),
            'server_url': f"http://{host}:{port}",
            'generated_at': self.helper.get_local_ip(),
            'deployment_type': self.deploy_var.get()
        }
        
        self.helper.save_network_config(config)
        messagebox.showinfo("成功", "配置已保存到 network_config.json")
    
    def test_url_connection(self):
        """测试URL连接"""
        url = self.test_url_var.get()
        if not url:
            messagebox.showwarning("提示", "请输入测试地址")
            return
        
        def test():
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(url)
                host = parsed.hostname
                port = parsed.port or 80
                
                # 测试TCP连接
                tcp_result = self.helper.test_port(host, port)
                
                result_text = f"🧪 连接测试结果:\n\n"
                result_text += f"测试地址: {url}\n"
                result_text += f"主机: {host}\n"
                result_text += f"端口: {port}\n"
                result_text += f"TCP连接: {'✅ 成功' if tcp_result else '❌ 失败'}\n\n"
                
                if tcp_result:
                    # 尝试HTTP请求
                    try:
                        import requests
                        response = requests.get(url, timeout=5)
                        result_text += f"HTTP状态: ✅ {response.status_code}\n"
                        result_text += f"响应时间: {response.elapsed.total_seconds():.2f}秒\n"
                        result_text += f"服务器: {response.headers.get('Server', 'Unknown')}\n"
                    except Exception as e:
                        result_text += f"HTTP请求: ❌ {str(e)}\n"
                else:
                    result_text += "❌ 无法建立TCP连接\n\n"
                    result_text += "可能的问题:\n"
                    result_text += "- 服务器未启动\n"
                    result_text += "- 端口被防火墙阻止\n"
                    result_text += "- 网络连接问题\n"
                    result_text += "- IP地址不正确\n"
                
                self.root.after(0, lambda: self.update_test_result(result_text))
                
            except Exception as e:
                error_text = f"测试出错: {str(e)}"
                self.root.after(0, lambda: self.update_test_result(error_text))
        
        threading.Thread(target=test, daemon=True).start()
    
    def update_test_result(self, text):
        """更新测试结果"""
        self.test_result_text.delete(1.0, tk.END)
        self.test_result_text.insert(1.0, text)
    
    def generate_test_qr(self):
        """生成测试二维码"""
        url = self.test_url_var.get()
        if not url:
            messagebox.showwarning("提示", "请输入测试地址")
            return
        
        try:
            import qrcode
            from PIL import ImageTk
            
            # 生成测试二维码
            qr = qrcode.QRCode(version=1, box_size=8, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save("test_qr.png")
            
            # 显示预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title("测试二维码")
            preview_window.geometry("400x450")
            
            # 显示二维码
            img_resized = img.resize((300, 300))
            photo = ImageTk.PhotoImage(img_resized)
            
            ttk.Label(preview_window, image=photo).pack(pady=10)
            ttk.Label(preview_window, text=f"测试地址: {url}", 
                     wraplength=350).pack(pady=5)
            ttk.Label(preview_window, text="请用手机扫描测试连接", 
                     font=("Arial", 10, "bold")).pack(pady=5)
            
            # 保持图片引用
            preview_window.image = photo
            
            messagebox.showinfo("成功", "测试二维码已生成: test_qr.png")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成二维码失败: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = NetworkHelperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
