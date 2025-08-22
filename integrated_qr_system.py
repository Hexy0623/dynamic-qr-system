#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成动态二维码系统 - 包含二维码管理和网络配置
"""

import qrcode
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from urllib.parse import quote
import os
import json
import uuid
import threading
from datetime import datetime
from PIL import Image, ImageTk
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import socket
import subprocess
import platform
import requests


class QRConfig:
    """二维码配置管理"""
    
    def __init__(self, config_file="integrated_qr_config.json"):
        self.config_file = config_file
        self.qr_codes = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.qr_codes = json.load(f)
            except:
                self.qr_codes = {}
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.qr_codes, f, ensure_ascii=False, indent=2)
    
    def add_qr(self, qr_id, email, subject, body, cc=None):
        """添加二维码"""
        self.qr_codes[qr_id] = {
            'email': email,
            'subject': subject,
            'body': body,
            'cc': cc,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'scan_count': 0,
            'last_scan': None
        }
        self.save_config()
    
    def get_qr(self, qr_id):
        """获取二维码信息"""
        return self.qr_codes.get(qr_id)
    
    def update_status(self, qr_id, status):
        """更新状态"""
        if qr_id in self.qr_codes:
            self.qr_codes[qr_id]['status'] = status
            self.save_config()
            return True
        return False
    
    def increment_scan(self, qr_id):
        """增加扫描计数"""
        if qr_id in self.qr_codes:
            self.qr_codes[qr_id]['scan_count'] += 1
            self.qr_codes[qr_id]['last_scan'] = datetime.now().isoformat()
            self.save_config()
    
    def get_all(self):
        """获取所有二维码"""
        return self.qr_codes


class DynamicQRHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def __init__(self, *args, config_manager=None, **kwargs):
        self.config_manager = config_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_status_page()
        elif parsed_path.path.startswith('/qr/'):
            qr_id = parsed_path.path.split('/qr/')[1]
            self.handle_qr_request(qr_id)
        else:
            self.send_error(404)
    
    def handle_qr_request(self, qr_id):
        """处理二维码请求"""
        if not self.config_manager:
            self.send_error(500, "配置管理器未初始化")
            return
        
        qr_info = self.config_manager.get_qr(qr_id)
        
        if not qr_info:
            self.send_error(404, "二维码不存在")
            return
        
        # 增加扫描计数
        self.config_manager.increment_scan(qr_id)
        
        if qr_info['status'] == 'active':
            # 激活状态：重定向到mailto
            mailto_url = self.build_mailto_url(qr_info)
            self.send_response(302)
            self.send_header('Location', mailto_url)
            self.end_headers()
        else:
            # 停用状态：显示停用页面
            self.send_stopped_page(qr_info)
    
    def build_mailto_url(self, qr_info):
        """构建mailto链接"""
        mailto_url = f"mailto:{qr_info['email']}"
        params = []
        
        if qr_info['subject']:
            params.append(f"subject={quote(qr_info['subject'])}")
        
        if qr_info['body']:
            params.append(f"body={quote(qr_info['body'])}")
        
        if qr_info['cc']:
            params.append(f"cc={qr_info['cc']}")
        
        if params:
            mailto_url += "?" + "&".join(params)
        
        return mailto_url
    
    def send_stopped_page(self, qr_info):
        """发送停用页面"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>二维码已失效</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex; justify-content: center; align-items: center; min-height: 100vh;
                }
                .container {
                    background: white; padding: 50px 40px; border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; max-width: 400px;
                    animation: fadeIn 0.5s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .icon { 
                    font-size: 80px; margin-bottom: 25px; 
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }
                h1 { 
                    color: #e74c3c; margin-bottom: 20px; font-size: 28px;
                    font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .message {
                    color: #666; font-size: 18px; line-height: 1.6;
                    margin-bottom: 30px;
                }
                .status {
                    background: #f8f9fa; padding: 15px; border-radius: 10px;
                    border-left: 4px solid #e74c3c; margin: 20px 0;
                }
                .footer {
                    color: #999; font-size: 14px; margin-top: 30px;
                    border-top: 1px solid #eee; padding-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🚫</div>
                <h1>二维码已失效</h1>
                <div class="message">
                    此二维码当前不可用，已被管理员停用。
                </div>
                <div class="status">
                    <strong>状态：</strong>已停用 ⏹️
                </div>
                <div class="footer">
                    如有疑问，请联系相关管理员
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))
    
    def send_status_page(self):
        """发送状态页面"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        qr_count = len(self.config_manager.get_all()) if self.config_manager else 0
        
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>集成动态二维码系统</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                .status {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔄 集成动态二维码系统</h1>
                <div class="status">
                    ✅ 服务器运行正常<br>
                    📊 当前管理 {qr_count} 个二维码
                </div>
                <div style="color: #666; line-height: 1.6;">
                    <p><strong>服务说明:</strong></p>
                    <ul>
                        <li>此服务器用于动态二维码重定向</li>
                        <li>激活状态的二维码会重定向到邮箱</li>
                        <li>停用状态的二维码会显示提示页面</li>
                        <li>所有扫描行为都会被记录</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """简化日志输出"""
        pass


class NetworkHelper:
    """网络配置助手"""
    
    def __init__(self):
        self.system = platform.system()
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
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


class IntegratedQRSystem:
    """集成动态二维码系统"""
    
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.config_manager = QRConfig()
        self.network_helper = NetworkHelper()
        self.server = None
        self.server_thread = None
        self.default_subject = "来自二维码的咨询"
        self.default_body = "您好，我通过二维码找到您的联系方式。"
    
    def get_server_url(self, include_qr_path=False, qr_id=None):
        """统一的服务器URL构建方法"""
        cloud_indicators = ['.onrender.com', '.herokuapp.com', '.vercel.app', '.netlify.app']
        is_cloud = any(indicator in self.host.lower() for indicator in cloud_indicators)
        is_https = self.port == 443
        
        if is_cloud or is_https:
            # 云端模式：使用云端地址
            if self.port == 443:
                base_url = f"https://{self.host}"
            else:
                base_url = f"https://{self.host}:{self.port}"
        else:
            # 本地模式：使用本地IP
            local_ip = self.network_helper.get_local_ip()
            base_url = f"http://{local_ip}:{self.port}"
        
        if include_qr_path:
            if qr_id:
                return f"{base_url}/qr/{qr_id}"
            else:
                return f"{base_url}/qr/[ID]"
        else:
            return base_url
    
    def start_server(self):
        """启动HTTP服务器"""
        def handler(*args, **kwargs):
            DynamicQRHandler(*args, config_manager=self.config_manager, **kwargs)
        
        try:
            self.server = HTTPServer((self.host, self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            return True
        except Exception as e:
            print(f"启动服务器失败: {e}")
            return False
    
    def stop_server(self):
        """停止HTTP服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
    
    def is_server_running(self):
        """检查服务器是否运行"""
        # 检测云端配置
        cloud_indicators = ['.onrender.com', '.herokuapp.com', '.vercel.app', '.netlify.app']
        is_cloud = any(indicator in self.host.lower() for indicator in cloud_indicators)
        is_https = self.port == 443
        
        if is_cloud or is_https:
            # 云端模式：检查远程服务器状态
            try:
                import requests
                server_url = self.get_server_url()
                response = requests.get(server_url, timeout=5, proxies={'http': None, 'https': None})
                return response.status_code == 200
            except:
                return False
        else:
            # 本地模式：检查本地服务器进程
            return self.server is not None and self.server_thread and self.server_thread.is_alive()
    
    def create_qr(self, email, subject=None, body=None, cc=None, output_path=None, size=10):
        """创建动态二维码"""
        if not subject:
            subject = self.default_subject
        if not body:
            body = self.default_body
        
        # 生成唯一ID
        qr_id = str(uuid.uuid4())
        
        # 添加到配置
        self.config_manager.add_qr(qr_id, email, subject, body, cc)
        
        # 获取实际服务器地址 - 使用统一方法
        server_url = self.get_server_url(include_qr_path=True, qr_id=qr_id)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        
        qr.add_data(server_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"integrated_qr_{qr_id[:8]}_{timestamp}.png"
        
        img.save(output_path)
        
        return {
            'qr_id': qr_id,
            'qr_path': output_path,
            'server_url': server_url,
            'email': email,
            'subject': subject,
            'body': body,
            'status': 'active'
        }
    
    def activate_qr(self, qr_id):
        """激活二维码"""
        return self.config_manager.update_status(qr_id, 'active')
    
    def stop_qr(self, qr_id):
        """停止二维码"""
        return self.config_manager.update_status(qr_id, 'stopped')
    
    def get_qr_info(self, qr_id):
        """获取二维码信息"""
        return self.config_manager.get_qr(qr_id)
    
    def get_all_qr_codes(self):
        """获取所有二维码"""
        return self.config_manager.get_all()


class IntegratedQRGUI:
    """集成动态二维码系统GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 集成动态二维码系统")
        self.root.geometry("1200x900")
        
        self.qr_system = IntegratedQRSystem()
        self.current_result = None
        self.network_info = {}
        
        self.setup_ui()
        
        # 启动服务器
        self.start_server()
        
        # 自动检测网络信息
        self.detect_network()
        
        # 程序退出时停止服务器
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title = ttk.Label(title_frame, text="🌐 集成动态二维码系统", 
                         font=("Arial", 18, "bold"))
        title.pack(side=tk.LEFT)
        
        # 服务器状态
        self.server_status = ttk.Label(title_frame, text="🔄 正在启动...", 
                                      foreground="orange")
        self.server_status.pack(side=tk.RIGHT)
        
        # 创建Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建各个页面
        self.setup_qr_management_tab()
        self.setup_network_config_tab()
        self.setup_monitoring_tab()
        self.setup_help_tab()
    
    def setup_qr_management_tab(self):
        """二维码管理页面"""
        qr_frame = ttk.Frame(self.notebook)
        self.notebook.add(qr_frame, text="📱 二维码管理")
        
        # 左侧：创建区域
        left_frame = ttk.Frame(qr_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        create_frame = ttk.LabelFrame(left_frame, text="创建动态二维码", padding="15")
        create_frame.pack(fill=tk.BOTH, expand=True)
        create_frame.columnconfigure(1, weight=1)
        
        ttk.Label(create_frame, text="* 邮箱地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(create_frame, textvariable=self.email_var, width=30).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(create_frame, text="邮件主题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.subject_var = tk.StringVar(value="来自二维码的咨询")
        ttk.Entry(create_frame, textvariable=self.subject_var, width=30).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(create_frame, text="邮件正文:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=5)
        self.body_text = tk.Text(create_frame, height=4, width=30)
        self.body_text.insert("1.0", "您好，我通过二维码找到您的联系方式。")
        self.body_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(create_frame, text="抄送邮箱:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cc_var = tk.StringVar()
        ttk.Entry(create_frame, textvariable=self.cc_var, width=30).grid(
            row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(create_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="🚀 创建二维码", 
                  command=self.create_qr).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📁 选择保存位置", 
                  command=self.select_save_path).pack(side=tk.LEFT, padx=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(left_frame, text="二维码预览", padding="15")
        preview_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.preview_label = ttk.Label(preview_frame, text="创建二维码后显示预览")
        self.preview_label.pack(pady=20)
        
        # 右侧：管理区域
        right_frame = ttk.Frame(qr_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        manage_frame = ttk.LabelFrame(right_frame, text="二维码列表", padding="15")
        manage_frame.pack(fill=tk.BOTH, expand=True)
        manage_frame.columnconfigure(0, weight=1)
        manage_frame.rowconfigure(1, weight=1)
        
        # 工具栏
        toolbar = ttk.Frame(manage_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 刷新", command=self.refresh_qr_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="✅ 激活", command=self.activate_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⏹️ 停止", command=self.stop_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ 删除", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        
        # 二维码列表
        list_frame = ttk.Frame(manage_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        columns = ('ID', '邮箱', '主题', '状态', '扫描次数', '创建时间')
        self.qr_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.qr_tree.heading(col, text=col)
        
        self.qr_tree.column('ID', width=80)
        self.qr_tree.column('邮箱', width=120)
        self.qr_tree.column('主题', width=100)
        self.qr_tree.column('状态', width=60)
        self.qr_tree.column('扫描次数', width=80)
        self.qr_tree.column('创建时间', width=120)
        
        self.qr_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.qr_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.qr_tree.configure(yscrollcommand=scrollbar.set)
        
        # 配置列权重
        qr_frame.columnconfigure(0, weight=1)
        qr_frame.columnconfigure(1, weight=1)
        qr_frame.rowconfigure(0, weight=1)
    
    def setup_network_config_tab(self):
        """网络配置页面"""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 网络配置")
        
        # 服务器配置区域
        config_frame = ttk.LabelFrame(network_frame, text="服务器配置", padding="15")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="服务器主机:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_host_var = tk.StringVar(value="0.0.0.0")
        server_host_entry = ttk.Entry(config_frame, textvariable=self.server_host_var, width=20)
        server_host_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Label(config_frame, text="服务器端口:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.server_port_var = tk.StringVar(value="8080")
        server_port_entry = ttk.Entry(config_frame, textvariable=self.server_port_var, width=20)
        server_port_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Button(config_frame, text="🔧 应用配置", 
                  command=self.apply_server_config).grid(row=0, column=2, pady=5, padx=(10, 0))
        
        ttk.Button(config_frame, text="🔄 重置默认", 
                  command=self.reset_server_config).grid(row=1, column=2, pady=5, padx=(10, 0))
        
        # 网络信息区域
        info_frame = ttk.LabelFrame(network_frame, text="网络信息", padding="15")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="本机IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.local_ip_label = ttk.Label(info_frame, text="检测中...", foreground="blue")
        self.local_ip_label.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Button(info_frame, text="复制", 
                  command=lambda: self.copy_text(self.local_ip_label.cget("text"))).grid(
                  row=0, column=2, pady=5, padx=(10, 0))
        
        ttk.Label(info_frame, text="公网IP:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.public_ip_label = ttk.Label(info_frame, text="检测中...", foreground="blue")
        self.public_ip_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Button(info_frame, text="复制", 
                  command=lambda: self.copy_text(self.public_ip_label.cget("text"))).grid(
                  row=1, column=2, pady=5, padx=(10, 0))
        
        ttk.Label(info_frame, text="当前服务器:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.server_url_label = ttk.Label(info_frame, text="启动中...", foreground="green")
        self.server_url_label.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Button(info_frame, text="复制", 
                  command=lambda: self.copy_text(self.server_url_label.cget("text"))).grid(
                  row=2, column=2, pady=5, padx=(10, 0))
        
        ttk.Label(info_frame, text="二维码URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.qr_url_label = ttk.Label(info_frame, text="等待配置...", foreground="purple")
        self.qr_url_label.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Button(info_frame, text="复制", 
                  command=lambda: self.copy_text(self.qr_url_label.cget("text"))).grid(
                  row=3, column=2, pady=5, padx=(10, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(network_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="🔄 重新检测", 
                  command=self.detect_network).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔧 重启服务器", 
                  command=self.restart_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧪 测试连接", 
                  command=self.test_server_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⚡ 快速设置", 
                  command=self.quick_setup).pack(side=tk.LEFT, padx=5)
        
        # 配置说明
        config_frame = ttk.LabelFrame(network_frame, text="部署配置说明", padding="15")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(config_frame, height=20)
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化配置说明
        self.update_config_info()
    
    def setup_monitoring_tab(self):
        """监控页面"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 监控统计")
        
        # 统计信息
        stats_frame = ttk.LabelFrame(monitor_frame, text="系统统计", padding="15")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        stats_frame.columnconfigure(1, weight=1)
        
        self.stats_labels = {}
        stats = [
            ("total_qr", "二维码总数:"),
            ("active_qr", "激活状态:"),
            ("stopped_qr", "停用状态:"),
            ("total_scans", "总扫描次数:"),
            ("server_status", "服务器状态:")
        ]
        
        for i, (key, label) in enumerate(stats):
            ttk.Label(stats_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", foreground="blue")
            self.stats_labels[key].grid(row=i, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 详细日志
        log_frame = ttk.LabelFrame(monitor_frame, text="扫描日志", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(monitor_frame, text="🔄 刷新统计", 
                  command=self.refresh_monitoring).pack(pady=10)
    
    def setup_help_tab(self):
        """帮助页面"""
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="❓ 使用帮助")
        
        help_text = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_content = """🌐 集成动态二维码系统使用说明

📱 二维码管理
═══════════════════════════════════════════════

1. 创建二维码
   • 填写邮箱地址（必填）
   • 设置邮件主题和正文
   • 可选择抄送邮箱
   • 点击"创建二维码"生成

2. 管理二维码
   • ✅ 激活：二维码正常工作，跳转到邮箱
   • ⏹️ 停止：二维码停用，显示提示页面
   • 🗑️ 删除：永久删除二维码记录
   • 🔄 刷新：更新列表显示

3. 二维码预览
   • 创建后自动显示预览
   • 可保存到指定位置

🌐 网络配置
═══════════════════════════════════════════════

1. 网络信息检测
   • 自动检测本机IP和公网IP
   • 显示服务器访问地址
   • 一键复制地址信息

2. 服务器管理
   • 🔄 重新检测：刷新网络信息
   • 🔧 重启服务器：重新启动HTTP服务
   • 🧪 测试连接：检查服务器是否正常

3. 部署方案
   • 局域网部署：同WiFi设备可访问
   • 云服务器：全球访问
   • 内网穿透：临时公网访问
   • 免费托管：长期免费使用

📊 监控统计
═══════════════════════════════════════════════

1. 系统统计
   • 二维码数量统计
   • 扫描次数统计
   • 服务器状态监控

2. 扫描日志
   • 详细的访问记录
   • 时间和IP信息
   • 错误日志记录

🔧 工作原理
═══════════════════════════════════════════════

1. 动态控制流程
   二维码 → HTTP服务器 → 状态检查 → 重定向决策
                                    ↓
                            Active: mailto链接
                            Stopped: 停用页面

2. 网络部署
   • 本地启动HTTP服务器
   • 二维码包含服务器链接
   • 用户扫码访问服务器
   • 服务器根据状态响应

⚠️ 注意事项
═══════════════════════════════════════════════

1. 服务器要求
   • 必须保持HTTP服务器运行
   • 服务器停止，所有二维码失效
   • 建议使用稳定的网络环境

2. 网络访问
   • 局域网部署：只有同网络用户能访问
   • 公网部署：需要公网IP或域名
   • 防火墙：确保端口8080开放

3. 数据安全
   • 配置文件存储在本地
   • 定期备份配置数据
   • 注意邮箱信息保密

🚀 快速开始
═══════════════════════════════════════════════

1. 系统会自动启动服务器和检测网络
2. 在"二维码管理"页面创建第一个二维码
3. 在"网络配置"页面查看访问地址
4. 使用手机扫描测试功能
5. 在"监控统计"页面查看使用情况

💡 技巧提示
═══════════════════════════════════════════════

• 邮件主题和正文支持中文
• 可以批量管理多个二维码
• 停用的二维码仍会显示联系信息
• 定期查看扫描统计了解使用情况
• 服务器地址变化时需要重新生成二维码"""

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
    
    def start_server(self):
        """启动服务器"""
        # 检测是否为云端配置
        cloud_indicators = ['.onrender.com', '.herokuapp.com', '.vercel.app', '.netlify.app']
        is_cloud = any(indicator in self.qr_system.host.lower() for indicator in cloud_indicators)
        is_https = self.qr_system.port == 443
        
        if is_cloud or is_https:
            # 云端模式：不启动本地服务器，直接更新URL显示
            server_url = self.qr_system.get_server_url()
            
            self.server_url_label.config(text=server_url)
            self.refresh_qr_list()
            
            # 异步检查云端服务器状态
            def check_cloud_status():
                if self.qr_system.is_server_running():
                    self.root.after(0, lambda: self.server_status.config(
                        text=f"✅ 云端服务器在线: {server_url}", 
                        foreground="green"
                    ))
                else:
                    self.root.after(0, lambda: self.server_status.config(
                        text=f"❌ 云端服务器离线: {server_url}", 
                        foreground="red"
                    ))
            
            import threading
            threading.Thread(target=check_cloud_status, daemon=True).start()
        else:
            # 本地模式：正常启动本地服务器
            if self.qr_system.start_server():
                server_url = self.qr_system.get_server_url()
                
                self.server_status.config(
                    text=f"✅ 服务器运行中: {server_url}", 
                    foreground="green"
                )
                
                self.server_url_label.config(text=server_url)
                self.refresh_qr_list()
            else:
                self.server_status.config(text="❌ 服务器启动失败", foreground="red")
                messagebox.showerror("错误", "服务器启动失败，请检查端口是否被占用")
    
    def restart_server(self):
        """重启服务器"""
        self.server_status.config(text="🔄 重启中...", foreground="orange")
        self.qr_system.stop_server()
        threading.Timer(1.0, self.start_server).start()
    
    def apply_server_config(self):
        """应用服务器配置"""
        try:
            new_host = self.server_host_var.get().strip()
            new_port = int(self.server_port_var.get().strip())
            
            if new_port < 1 or new_port > 65535:
                messagebox.showerror("错误", "端口号必须在1-65535之间！")
                return
            
            # 检查配置是否有变化
            if new_host == self.qr_system.host and new_port == self.qr_system.port:
                messagebox.showinfo("提示", "配置没有变化")
                return
            
            # 确认重启
            result = messagebox.askyesno("确认配置", 
                                       f"将要应用新的服务器配置:\n\n"
                                       f"主机: {new_host}\n"
                                       f"端口: {new_port}\n\n"
                                       f"这将重启服务器，确定继续吗？")
            
            if result:
                # 停止当前服务器
                self.server_status.config(text="🔄 应用新配置...", foreground="orange")
                self.qr_system.stop_server()
                
                # 更新配置
                self.qr_system.host = new_host
                self.qr_system.port = new_port
                
                # 延迟启动新服务器
                threading.Timer(1.0, self.start_server_with_new_config).start()
                
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字！")
        except Exception as e:
            messagebox.showerror("错误", f"配置应用失败: {str(e)}")
    
    def start_server_with_new_config(self):
        """使用新配置启动服务器 - 支持云端配置"""
        
        # 检测是否为云端配置
        cloud_indicators = ['.onrender.com', '.herokuapp.com', '.vercel.app', '.netlify.app']
        is_cloud = any(indicator in self.qr_system.host.lower() for indicator in cloud_indicators)
        is_https = self.qr_system.port == 443
        
        if is_cloud or is_https:
            # 云端模式：不启动本地服务器，直接更新URL显示
            server_url = self.qr_system.get_server_url()
            qr_url = self.qr_system.get_server_url(include_qr_path=True)
            
            self.server_url_label.config(text=server_url)
            self.qr_url_label.config(text=qr_url)
            
            # 异步检查云端服务器状态
            def check_cloud_status():
                if self.qr_system.is_server_running():
                    self.root.after(0, lambda: self.server_status.config(
                        text=f"✅ 云端服务器在线: {server_url}", 
                        foreground="green"
                    ))
                    self.root.after(0, lambda: messagebox.showinfo("成功", 
                                      f"云端服务器配置已更新！\n\n"
                                      f"云端地址: {server_url}\n\n"
                                      f"✅ 服务器在线，可以正常使用"))
                else:
                    self.root.after(0, lambda: self.server_status.config(
                        text=f"❌ 云端服务器离线: {server_url}", 
                        foreground="red"
                    ))
                    self.root.after(0, lambda: messagebox.showwarning("警告", 
                                      f"云端服务器配置已更新！\n\n"
                                      f"云端地址: {server_url}\n\n"
                                      f"⚠️ 服务器可能正在启动或离线"))
            
            import threading
            threading.Thread(target=check_cloud_status, daemon=True).start()
            
            # 更新网络信息
            self.detect_network()
            
        else:
            # 本地模式：正常启动本地服务器
            if self.qr_system.start_server():
                server_url = self.qr_system.get_server_url()
                qr_url = self.qr_system.get_server_url(include_qr_path=True)
                
                self.server_status.config(
                    text=f"✅ 服务器已重启: {server_url}", 
                    foreground="green"
                )
                
                self.server_url_label.config(text=server_url)
                self.qr_url_label.config(text=qr_url)
                
                messagebox.showinfo("成功", 
                                  f"服务器配置已更新！\n\n"
                                  f"新地址: {server_url}\n\n"
                                  f"注意：之前创建的二维码可能需要重新生成")
                
                # 更新网络信息
                self.detect_network()
            else:
                self.server_status.config(text="❌ 新配置启动失败", foreground="red")
                messagebox.showerror("错误", 
                                   f"新配置启动失败，可能原因:\n"
                                   f"• 端口 {self.qr_system.port} 被占用\n"
                                   f"• 主机地址 {self.qr_system.host} 无效\n"
                                   f"• 防火墙阻止了连接")
    
    def reset_server_config(self):
        """重置服务器配置"""
        result = messagebox.askyesno("确认重置", 
                                   "确定要重置为默认配置吗？\n\n"
                                   "默认配置:\n"
                                   "主机: 0.0.0.0\n"
                                   "端口: 8080")
        
        if result:
            self.server_host_var.set("0.0.0.0")
            self.server_port_var.set("8080")
            messagebox.showinfo("成功", "配置已重置，点击'应用配置'生效")
    
    def quick_setup(self):
        """快速设置对话框"""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("⚡ 快速网络设置")
        setup_window.geometry("500x400")
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # 居中显示
        setup_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(main_frame, text="⚡ 快速网络设置", 
                         font=("Arial", 14, "bold"))
        title.pack(pady=(0, 20))
        
        # 当前配置
        current_frame = ttk.LabelFrame(main_frame, text="当前配置", padding="15")
        current_frame.pack(fill=tk.X, pady=(0, 15))
        
        current_info = f"""主机: {self.qr_system.host}
端口: {self.qr_system.port}
状态: {'✅ 运行中' if self.qr_system.is_server_running() else '❌ 停止'}
地址: {self.server_url_label.cget('text')}"""
        
        ttk.Label(current_frame, text=current_info, font=("Consolas", 10)).pack()
        
        # 快速选项
        options_frame = ttk.LabelFrame(main_frame, text="快速设置选项", padding="15")
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        setup_var = tk.StringVar(value="local")
        
        # 局域网设置
        local_frame = ttk.Frame(options_frame)
        local_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(local_frame, text="🏠 局域网设置 (推荐)", 
                       variable=setup_var, value="local").pack(side=tk.LEFT)
        ttk.Label(local_frame, text=" - 主机:0.0.0.0, 端口:8080", 
                 foreground="gray").pack(side=tk.LEFT)
        
        # 自定义端口
        custom_frame = ttk.Frame(options_frame)
        custom_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(custom_frame, text="🔧 自定义端口", 
                       variable=setup_var, value="custom").pack(side=tk.LEFT)
        
        port_frame = ttk.Frame(custom_frame)
        port_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(port_frame, text="端口:").pack(side=tk.LEFT)
        custom_port_var = tk.StringVar(value="8080")
        ttk.Entry(port_frame, textvariable=custom_port_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        # 外网访问
        public_frame = ttk.Frame(options_frame)
        public_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(public_frame, text="🌐 外网访问设置", 
                       variable=setup_var, value="public").pack(side=tk.LEFT)
        ttk.Label(public_frame, text=" - 主机:0.0.0.0, 端口:80", 
                 foreground="gray").pack(side=tk.LEFT)
        
        # 测试端口
        test_frame = ttk.Frame(options_frame)
        test_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(test_frame, text="🧪 测试端口", 
                       variable=setup_var, value="test").pack(side=tk.LEFT)
        ttk.Label(test_frame, text=" - 主机:localhost, 端口:8888", 
                 foreground="gray").pack(side=tk.LEFT)
        
        # 说明文本
        info_text = scrolledtext.ScrolledText(options_frame, height=6, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        info_content = """🏠 局域网设置: 适合办公室、家庭WiFi环境，同网络设备可访问
🔧 自定义端口: 如果8080端口被占用，可以更换其他端口
🌐 外网访问设置: 适合云服务器部署，使用80端口（需要管理员权限）
🧪 测试端口: 使用不同端口进行测试，避免冲突"""
        
        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        def apply_quick_setup():
            choice = setup_var.get()
            
            if choice == "local":
                host, port = "0.0.0.0", 8080
            elif choice == "custom":
                host, port = "0.0.0.0", int(custom_port_var.get())
            elif choice == "public":
                host, port = "0.0.0.0", 80
            elif choice == "test":
                host, port = "localhost", 8888
            
            # 更新配置
            self.server_host_var.set(host)
            self.server_port_var.set(str(port))
            
            setup_window.destroy()
            
            # 询问是否立即应用
            result = messagebox.askyesno("确认应用", 
                                       f"快速设置完成！\n\n"
                                       f"新配置:\n"
                                       f"主机: {host}\n"
                                       f"端口: {port}\n\n"
                                       f"是否立即应用配置？")
            
            if result:
                self.apply_server_config()
        
        ttk.Button(button_frame, text="✅ 应用设置", 
                  command=apply_quick_setup).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="❌ 取消", 
                  command=setup_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def detect_network(self):
        """检测网络信息"""
        def detect():
            local_ip = self.qr_system.network_helper.get_local_ip()
            public_ip = self.qr_system.network_helper.get_public_ip()
            
            self.root.after(0, lambda: self.local_ip_label.config(text=local_ip))
            self.root.after(0, lambda: self.public_ip_label.config(text=public_ip))
            
            # 使用统一的URL构建方法
            server_url = self.qr_system.get_server_url()
            qr_url = self.qr_system.get_server_url(include_qr_path=True)
            
            self.root.after(0, lambda: self.server_url_label.config(text=server_url))
            self.root.after(0, lambda: self.qr_url_label.config(text=qr_url))
            
            self.network_info = {
                'local_ip': local_ip,
                'public_ip': public_ip,
                'server_url': server_url,
                'qr_url': qr_url
            }
            
            self.root.after(0, self.update_config_info)
        
        threading.Thread(target=detect, daemon=True).start()
    
    def update_config_info(self):
        """更新配置信息"""
        local_ip = self.network_info.get('local_ip', 'unknown')
        public_ip = self.network_info.get('public_ip', 'unknown')
        server_url = self.network_info.get('server_url', 'unknown')
        
        config_info = f"""🌐 当前网络配置信息

📋 基本信息
═══════════════════════════════════════════════
• 本机IP地址: {local_ip}
• 公网IP地址: {public_ip}
• 服务器地址: {server_url}
• 服务器端口: {self.qr_system.port}
• 服务器状态: {'✅ 运行中' if self.qr_system.is_server_running() else '❌ 未运行'}

🏠 局域网部署（推荐新手）
═══════════════════════════════════════════════
适用场景：办公室、家庭WiFi环境

1. 当前配置已就绪
   服务器地址: {server_url}

2. 二维码URL格式
   {server_url}/qr/[二维码ID]

3. 使用说明
   • 确保设备连接同一WiFi
   • 电脑需要保持开机运行
   • 防火墙允许端口{self.qr_system.port}

4. 测试方法
   • 用手机浏览器访问: {server_url}
   • 应该看到系统状态页面

☁️ 云服务器部署（正式使用）
═══════════════════════════════════════════════
适用场景：全球访问，24小时服务

推荐服务商：
• 阿里云ECS: 1核2G约￥100/年
• 腾讯云CVM: 1核2G约￥95/年
• 华为云ECS: 1核2G约￥99/年

部署步骤：
1. 购买云服务器（Ubuntu 20.04）
2. 连接服务器: ssh root@服务器IP
3. 安装依赖: apt install python3 python3-pip -y
4. 安装包: pip3 install qrcode[pil] pillow requests
5. 上传代码并运行

🔗 内网穿透（临时测试）
═══════════════════════════════════════════════
适用场景：快速测试，无需购买服务器

方案一：ngrok（国外）
1. 注册账号: https://ngrok.com
2. 下载客户端
3. 运行: ngrok http {self.qr_system.port}
4. 获得公网地址: https://xxx.ngrok.io

方案二：花生壳（国内）
1. 注册账号: https://hsk.oray.com
2. 下载客户端
3. 配置内网穿透
4. 获得域名访问

🆓 免费托管（长期免费）
═══════════════════════════════════════════════
适用场景：小规模使用，长期运行

推荐平台：
• Railway: https://railway.app (500小时/月)
• Render: https://render.com (750小时/月)

部署方法：
1. 将代码上传到GitHub
2. 连接到托管平台
3. 自动构建和部署

⚠️ 故障排除
═══════════════════════════════════════════════
1. 服务器无法启动
   • 检查端口{self.qr_system.port}是否被占用
   • 尝试更换端口号
   • 检查防火墙设置

2. 二维码扫描无响应
   • 确认服务器正在运行
   • 检查网络连接
   • 验证二维码URL格式

3. 局域网无法访问
   • 确认设备在同一网络
   • 检查路由器设置
   • 尝试关闭防火墙测试

📞 技术支持
═══════════════════════════════════════════════
• 系统会自动检测网络配置
• 使用"测试连接"功能验证
• 查看"监控统计"了解使用情况
• 遇到问题请检查服务器日志"""

        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, config_info)
    
    def copy_text(self, text):
        """复制文本到剪贴板"""
        if text and text not in ["检测中...", "启动中...", "无法获取", "unknown"]:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("成功", f"已复制: {text}")
        else:
            messagebox.showwarning("提示", "没有可复制的内容")
    
    def test_server_connection(self):
        """测试服务器连接"""
        local_ip = self.network_info.get('local_ip')
        if not local_ip:
            messagebox.showwarning("提示", "请先检测网络信息")
            return
        
        def test():
            result = self.qr_system.network_helper.test_port(local_ip, self.qr_system.port)
            status = "✅ 连接成功" if result else "❌ 连接失败"
            
            message = f"测试结果: {status}\n"
            message += f"服务器地址: {local_ip}:{self.qr_system.port}\n\n"
            
            if result:
                message += "✅ 服务器运行正常\n"
                message += "✅ 端口连接成功\n"
                message += "✅ 可以创建和使用二维码\n"
            else:
                message += "❌ 无法连接到服务器\n"
                message += "\n可能的原因:\n"
                message += "• 服务器未正确启动\n"
                message += "• 端口被防火墙阻止\n"
                message += "• 端口被其他程序占用\n"
                message += "\n建议解决方案:\n"
                message += "• 点击'重启服务器'按钮\n"
                message += "• 检查防火墙设置\n"
                message += "• 尝试更换端口号\n"
            
            self.root.after(0, lambda: messagebox.showinfo("连接测试", message))
        
        threading.Thread(target=test, daemon=True).start()
    
    def select_save_path(self):
        """选择保存路径"""
        filename = filedialog.asksaveasfilename(
            title="选择二维码保存位置",
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
        )
        if filename:
            self.save_path = filename
            messagebox.showinfo("成功", f"保存路径已设置: {filename}")
    
    def create_qr(self):
        """创建二维码"""
        email = self.email_var.get().strip()
        if not email or "@" not in email:
            messagebox.showerror("错误", "请输入有效的邮箱地址！")
            return
        
        if not self.qr_system.is_server_running():
            messagebox.showerror("错误", "服务器未运行，请先重启服务器！")
            return
        
        try:
            subject = self.subject_var.get().strip()
            body = self.body_text.get("1.0", tk.END).strip()
            cc = self.cc_var.get().strip() if self.cc_var.get().strip() else None
            
            output_path = getattr(self, 'save_path', None)
            
            result = self.qr_system.create_qr(email, subject, body, cc, output_path)
            self.current_result = result
            
            # 显示预览
            self.show_qr_preview(result['qr_path'])
            
            # 刷新列表
            self.refresh_qr_list()
            
            # 更新监控
            self.refresh_monitoring()
            
            messagebox.showinfo("成功", 
                              f"动态二维码创建成功！\n\n"
                              f"ID: {result['qr_id'][:8]}...\n"
                              f"文件: {result['qr_path']}\n"
                              f"服务器链接: {result['server_url']}\n\n"
                              f"二维码已激活，可以立即使用！")
            
            # 清空保存路径
            if hasattr(self, 'save_path'):
                delattr(self, 'save_path')
            
        except Exception as e:
            messagebox.showerror("错误", f"创建失败: {str(e)}")
    
    def show_qr_preview(self, image_path):
        """显示二维码预览"""
        try:
            image = Image.open(image_path)
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        except Exception as e:
            self.preview_label.config(text=f"预览失败: {str(e)}")
    
    def refresh_qr_list(self):
        """刷新二维码列表"""
        for item in self.qr_tree.get_children():
            self.qr_tree.delete(item)
        
        qr_codes = self.qr_system.get_all_qr_codes()
        
        for qr_id, qr_info in qr_codes.items():
            status_text = "✅ 激活" if qr_info['status'] == 'active' else "⏹️ 停止"
            created_time = qr_info['created_at'][:16] if qr_info['created_at'] else ""
            
            self.qr_tree.insert('', 'end', values=(
                qr_id[:8] + '...',
                qr_info['email'],
                qr_info['subject'][:12] + '...' if len(qr_info['subject']) > 12 else qr_info['subject'],
                status_text,
                qr_info['scan_count'],
                created_time
            ), tags=(qr_id,))
    
    def activate_selected(self):
        """激活选中的二维码"""
        selected = self.qr_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要激活的二维码")
            return
        
        count = 0
        for item in selected:
            qr_id = self.qr_tree.item(item)['tags'][0]
            if self.qr_system.activate_qr(qr_id):
                count += 1
        
        self.refresh_qr_list()
        self.refresh_monitoring()
        messagebox.showinfo("成功", f"已激活 {count} 个二维码")
    
    def stop_selected(self):
        """停止选中的二维码"""
        selected = self.qr_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要停止的二维码")
            return
        
        result = messagebox.askyesno("确认", f"确定要停止 {len(selected)} 个二维码吗？")
        if result:
            count = 0
            for item in selected:
                qr_id = self.qr_tree.item(item)['tags'][0]
                if self.qr_system.stop_qr(qr_id):
                    count += 1
            
            self.refresh_qr_list()
            self.refresh_monitoring()
            messagebox.showinfo("成功", f"已停止 {count} 个二维码")
    
    def delete_selected(self):
        """删除选中的二维码"""
        selected = self.qr_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的二维码")
            return
        
        result = messagebox.askyesno("确认删除", 
                                   f"确定要删除 {len(selected)} 个二维码吗？\n\n"
                                   "注意：删除后无法恢复，已分发的二维码将无法使用！")
        if result:
            count = 0
            for item in selected:
                qr_id = self.qr_tree.item(item)['tags'][0]
                if qr_id in self.qr_system.config_manager.qr_codes:
                    del self.qr_system.config_manager.qr_codes[qr_id]
                    count += 1
            
            self.qr_system.config_manager.save_config()
            self.refresh_qr_list()
            self.refresh_monitoring()
            messagebox.showinfo("成功", f"已删除 {count} 个二维码")
    
    def refresh_monitoring(self):
        """刷新监控统计"""
        qr_codes = self.qr_system.get_all_qr_codes()
        
        total_qr = len(qr_codes)
        active_qr = sum(1 for qr in qr_codes.values() if qr['status'] == 'active')
        stopped_qr = total_qr - active_qr
        total_scans = sum(qr['scan_count'] for qr in qr_codes.values())
        server_status = "✅ 运行中" if self.qr_system.is_server_running() else "❌ 停止"
        
        self.stats_labels['total_qr'].config(text=str(total_qr))
        self.stats_labels['active_qr'].config(text=str(active_qr))
        self.stats_labels['stopped_qr'].config(text=str(stopped_qr))
        self.stats_labels['total_scans'].config(text=str(total_scans))
        self.stats_labels['server_status'].config(text=server_status)
        
        # 更新日志
        log_content = "📊 二维码使用统计\n"
        log_content += "=" * 50 + "\n\n"
        
        if qr_codes:
            for qr_id, qr_info in qr_codes.items():
                log_content += f"🏷️ ID: {qr_id[:8]}...\n"
                log_content += f"📧 邮箱: {qr_info['email']}\n"
                log_content += f"📝 主题: {qr_info['subject']}\n"
                log_content += f"📊 状态: {'✅ 激活' if qr_info['status'] == 'active' else '⏹️ 停止'}\n"
                log_content += f"📈 扫描: {qr_info['scan_count']} 次\n"
                log_content += f"🕒 创建: {qr_info['created_at'][:19]}\n"
                if qr_info['last_scan']:
                    log_content += f"🕒 最后扫描: {qr_info['last_scan'][:19]}\n"
                log_content += "-" * 30 + "\n\n"
        else:
            log_content += "暂无二维码记录\n"
        
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(1.0, log_content)
    
    def on_closing(self):
        """程序关闭处理"""
        self.qr_system.stop_server()
        self.root.destroy()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="集成动态二维码系统")
    parser.add_argument("--no-gui", action="store_true", help="仅启动服务器，不显示GUI")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口")
    
    args = parser.parse_args()
    
    if args.no_gui:
        # 纯服务器模式
        print("🌐 集成动态二维码系统 - 服务器模式")
        print("=" * 50)
        
        qr_system = IntegratedQRSystem(args.host, args.port)
        
        if qr_system.start_server():
            # 使用统一的URL构建方法
            server_url = qr_system.get_server_url()
            
            print(f"✅ 服务器已启动: {server_url}")
            print(f"📊 管理 {len(qr_system.get_all_qr_codes())} 个二维码")
            print("🔄 服务器正在运行...")
            print("按 Ctrl+C 停止服务器")
            
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 正在停止服务器...")
                qr_system.stop_server()
                print("✅ 服务器已停止")
        else:
            print("❌ 服务器启动失败")
            return 1
    else:
        # GUI模式
        try:
            root = tk.Tk()
            app = IntegratedQRGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"❌ GUI启动失败: {e}")
            print("💡 尝试使用 --no-gui 参数运行纯服务器模式")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
