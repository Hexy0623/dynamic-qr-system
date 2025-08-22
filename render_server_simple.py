#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Render服务器 - 确保兼容性
"""

import os
import sys
import json
import uuid
import http.server
import socketserver
import urllib.parse
from datetime import datetime

# 简化的二维码配置管理
class SimpleQRConfig:
    def __init__(self):
        self.config_file = "qr_config.json"
        self.data = self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {"qr_codes": {}}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get_qr_data(self, qr_id):
        """获取二维码数据"""
        return self.data.get("qr_codes", {}).get(qr_id)
    
    def add_qr(self, qr_id, email, subject="", body="", cc=""):
        """添加二维码"""
        if "qr_codes" not in self.data:
            self.data["qr_codes"] = {}
        
        self.data["qr_codes"][qr_id] = {
            "email": email,
            "subject": subject,
            "body": body,
            "cc": cc,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        self.save_config()

# HTTP请求处理器
class SimpleQRHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, config_manager=None, **kwargs):
        self.config_manager = config_manager or SimpleQRConfig()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                self.send_status_page()
            elif self.path.startswith('/qr/'):
                qr_id = self.path.split('/')[-1]
                self.handle_qr_request(qr_id)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"请求处理错误: {e}")
            self.send_error(500)
    
    def send_status_page(self):
        """发送状态页面"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        qr_count = len(self.config_manager.data.get("qr_codes", {}))
        
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>动态二维码系统</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                h1 {{ color: #2c3e50; text-align: center; }}
                .status {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 动态二维码系统</h1>
                <div class="status">
                    <strong>✅ 系统运行正常</strong>
                </div>
                <div class="info">
                    <p><strong>📊 统计信息</strong></p>
                    <p>• 管理二维码数量: {qr_count}</p>
                    <p>• 服务器状态: 在线</p>
                    <p>• 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))
    
    def handle_qr_request(self, qr_id):
        """处理二维码请求"""
        qr_data = self.config_manager.get_qr_data(qr_id)
        
        if not qr_data:
            self.send_error(404, "二维码不存在")
            return
        
        if qr_data.get("status") != "active":
            self.send_stopped_page()
            return
        
        # 构建邮件链接
        email = qr_data.get("email", "")
        subject = qr_data.get("subject", "")
        body = qr_data.get("body", "")
        cc = qr_data.get("cc", "")
        
        mailto_url = f"mailto:{email}"
        params = []
        
        if subject:
            params.append(f"subject={urllib.parse.quote(subject)}")
        if body:
            params.append(f"body={urllib.parse.quote(body)}")
        if cc:
            params.append(f"cc={urllib.parse.quote(cc)}")
        
        if params:
            mailto_url += "?" + "&".join(params)
        
        # 重定向到邮件客户端
        self.send_response(302)
        self.send_header('Location', mailto_url)
        self.end_headers()
    
    def send_stopped_page(self):
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
                body { font-family: sans-serif; text-align: center; margin: 50px; }
                .message { background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="message">
                <h2>⚠️ 二维码已失效</h2>
                <p>此二维码已被停用，无法使用。</p>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))

def main():
    """主函数"""
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 10000))
    
    print(f"🌐 简化版动态二维码服务器")
    print(f"📡 监听地址: {host}:{port}")
    
    # 创建配置管理器
    config_manager = SimpleQRConfig()
    
    # 创建测试二维码（如果不存在）
    if not config_manager.data.get("qr_codes"):
        test_id = str(uuid.uuid4())
        config_manager.add_qr(
            test_id,
            "test@example.com",
            "测试邮件",
            "这是一个测试二维码"
        )
        print(f"✅ 创建测试二维码: {test_id}")
    
    # 创建HTTP处理器
    def handler(*args, **kwargs):
        SimpleQRHandler(*args, config_manager=config_manager, **kwargs)
    
    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"✅ 服务器启动成功")
            print(f"🔗 访问地址: http://{host}:{port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())