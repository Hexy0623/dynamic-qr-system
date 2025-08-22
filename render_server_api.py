#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带API功能的Render服务器 - 支持本地管理器
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

# HTTP请求处理器（带API）
class QRAPIHandler(http.server.BaseHTTPRequestHandler):
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
            elif self.path == '/api/qr':
                self.send_qr_list()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"GET请求处理错误: {e}")
            self.send_error(500)
    
    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path == '/api/qr':
                self.handle_create_qr()
            elif self.path.startswith('/api/qr/') and '/status' in self.path:
                qr_id = self.path.split('/')[-2]  # /api/qr/{id}/status
                self.handle_update_status(qr_id)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"POST请求处理错误: {e}")
            self.send_error(500)
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
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
                .api {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
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
                <div class="api">
                    <p><strong>🔌 API接口</strong></p>
                    <p>• GET /api/qr - 获取二维码列表</p>
                    <p>• POST /api/qr - 创建新二维码</p>
                    <p>• POST /api/qr/{{id}}/status - 更新状态</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))
    
    def send_qr_list(self):
        """发送二维码列表API"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {
            "status": "success",
            "data": self.config_manager.data.get("qr_codes", {})
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def handle_create_qr(self):
        """处理创建二维码API"""
        try:
            # 读取POST数据
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 提取参数
            qr_id = data.get('qr_id')
            email = data.get('email')
            subject = data.get('subject', '')
            body = data.get('body', '')
            cc = data.get('cc', '')
            
            if not qr_id or not email:
                self.send_error(400, "缺少必要参数")
                return
            
            # 添加二维码
            self.config_manager.add_qr(qr_id, email, subject, body, cc)
            
            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                "status": "success",
                "message": "二维码创建成功",
                "qr_id": qr_id
            }
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            print(f"✅ 创建二维码: {qr_id[:8]}... -> {email}")
            
        except Exception as e:
            print(f"创建二维码错误: {e}")
            self.send_error(500, f"创建失败: {str(e)}")
    
    def handle_update_status(self, qr_id):
        """处理更新状态API"""
        try:
            # 读取POST数据
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            status = data.get('status')
            if not status:
                self.send_error(400, "缺少状态参数")
                return
            
            # 更新状态
            qr_codes = self.config_manager.data.get("qr_codes", {})
            if qr_id in qr_codes:
                qr_codes[qr_id]["status"] = status
                self.config_manager.save_config()
                
                # 返回成功响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response_data = {
                    "status": "success",
                    "message": f"状态更新为: {status}"
                }
                
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                print(f"📝 更新状态: {qr_id[:8]}... -> {status}")
            else:
                self.send_error(404, "二维码不存在")
                
        except Exception as e:
            print(f"更新状态错误: {e}")
            self.send_error(500, f"更新失败: {str(e)}")
    
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
        
        # 记录访问
        print(f"📱 二维码访问: {qr_id[:8]}... -> {email}")
        
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
    
    print(f"🌐 动态二维码服务器 (带API)")
    print(f"📡 监听地址: {host}:{port}")
    
    # 创建配置管理器
    config_manager = SimpleQRConfig()
    
    # 创建HTTP处理器
    def handler(*args, **kwargs):
        QRAPIHandler(*args, config_manager=config_manager, **kwargs)
    
    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"✅ 服务器启动成功")
            print(f"🔗 访问地址: http://{host}:{port}")
            print(f"🔌 API地址: http://{host}:{port}/api/qr")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
