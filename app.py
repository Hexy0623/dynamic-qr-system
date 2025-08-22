#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态二维码系统 - Render云端服务器
支持API管理和二维码重定向
"""

import os
import sys
import json
import uuid
import http.server
import socketserver
import urllib.parse
from datetime import datetime

class QRConfigManager:
    """二维码配置管理器"""
    
    def __init__(self):
        self.config_file = "qr_data.json"
        self.data = self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"配置加载失败: {e}")
        return {"qr_codes": {}, "stats": {"total_scans": 0, "total_qrs": 0}}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置保存失败: {e}")
    
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
            "scan_count": 0,
            "created_at": datetime.now().isoformat(),
            "last_scan": None
        }
        
        # 更新统计
        self.data.setdefault("stats", {})["total_qrs"] = len(self.data["qr_codes"])
        self.save_config()
        print(f"✅ 添加二维码: {qr_id[:8]}... -> {email}")
    
    def update_status(self, qr_id, status):
        """更新二维码状态"""
        if qr_id in self.data.get("qr_codes", {}):
            self.data["qr_codes"][qr_id]["status"] = status
            self.save_config()
            print(f"📝 状态更新: {qr_id[:8]}... -> {status}")
            return True
        return False
    
    def record_scan(self, qr_id):
        """记录扫描"""
        if qr_id in self.data.get("qr_codes", {}):
            self.data["qr_codes"][qr_id]["scan_count"] += 1
            self.data["qr_codes"][qr_id]["last_scan"] = datetime.now().isoformat()
            self.data.setdefault("stats", {})["total_scans"] = self.data["stats"].get("total_scans", 0) + 1
            self.save_config()

class QRHandler(http.server.BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def __init__(self, *args, config_manager=None, **kwargs):
        self.config_manager = config_manager or QRConfigManager()
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                self.send_dashboard()
            elif self.path == '/health':
                self.send_health_check()
            elif self.path.startswith('/qr/'):
                qr_id = self.path.split('/')[-1]
                self.handle_qr_scan(qr_id)
            elif self.path == '/api/qr':
                self.send_qr_list()
            elif self.path == '/api/stats':
                self.send_stats()
            else:
                self.send_error(404, "页面不存在")
        except Exception as e:
            print(f"GET请求错误: {e}")
            self.send_error(500, f"服务器错误: {str(e)}")
    
    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path == '/api/qr':
                self.handle_create_qr()
            elif self.path.startswith('/api/qr/') and self.path.endswith('/status'):
                qr_id = self.path.split('/')[-2]
                self.handle_update_status(qr_id)
            else:
                self.send_error(404, "API接口不存在")
        except Exception as e:
            print(f"POST请求错误: {e}")
            self.send_error(500, f"服务器错误: {str(e)}")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_dashboard(self):
        """发送控制台页面"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        stats = self.config_manager.data.get("stats", {})
        qr_count = len(self.config_manager.data.get("qr_codes", {}))
        total_scans = stats.get("total_scans", 0)
        
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>动态二维码系统控制台</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .stat-number {{ font-size: 2.5em; font-weight: bold; color: #2d3748; }}
                .stat-label {{ color: #718096; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
                .api-docs {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .endpoint {{ background: #f7fafc; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4299e1; }}
                .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
                .get {{ background: #48bb78; color: white; }}
                .post {{ background: #ed8936; color: white; }}
                code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; font-family: 'Monaco', monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌐 动态二维码系统</h1>
                    <p>云端服务器控制台 | 运行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{qr_count}</div>
                        <div class="stat-label">总二维码数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_scans}</div>
                        <div class="stat-label">总扫描次数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">✅</div>
                        <div class="stat-label">服务状态</div>
                    </div>
                </div>
                
                <div class="api-docs">
                    <h2>🔌 API 接口文档</h2>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <code>/qr/{{id}}</code> - 二维码重定向 (用户扫描)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <code>/api/qr</code> - 获取所有二维码列表
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <code>/api/qr</code> - 创建新二维码<br>
                        参数: qr_id, email, subject, body, cc
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <code>/api/qr/{{id}}/status</code> - 更新二维码状态<br>
                        参数: status (active/stopped)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <code>/api/stats</code> - 获取统计信息
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <code>/health</code> - 健康检查
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode('utf-8'))
    
    def send_health_check(self):
        """健康检查"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0",
            "qr_count": len(self.config_manager.data.get("qr_codes", {}))
        }
        
        self.wfile.write(json.dumps(health_data).encode('utf-8'))
    
    def handle_qr_scan(self, qr_id):
        """处理二维码扫描"""
        qr_data = self.config_manager.get_qr_data(qr_id)
        
        if not qr_data:
            self.send_error(404, "二维码不存在")
            return
        
        if qr_data.get("status") != "active":
            self.send_stopped_page()
            return
        
        # 记录扫描
        self.config_manager.record_scan(qr_id)
        
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
        
        print(f"📱 二维码扫描: {qr_id[:8]}... -> {email}")
        
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
                body { font-family: sans-serif; text-align: center; margin: 50px; background: #f5f5f5; }
                .message { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                .icon { font-size: 3em; margin-bottom: 20px; }
                h2 { color: #e53e3e; margin-bottom: 15px; }
                p { color: #718096; }
            </style>
        </head>
        <body>
            <div class="message">
                <div class="icon">⚠️</div>
                <h2>二维码已失效</h2>
                <p>此二维码已被停用，无法继续使用。</p>
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
            "data": self.config_manager.data.get("qr_codes", {}),
            "count": len(self.config_manager.data.get("qr_codes", {}))
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def send_stats(self):
        """发送统计信息API"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        stats = self.config_manager.data.get("stats", {})
        response_data = {
            "status": "success",
            "stats": stats,
            "qr_count": len(self.config_manager.data.get("qr_codes", {})),
            "timestamp": datetime.now().isoformat()
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
                self.send_error(400, "缺少必要参数: qr_id, email")
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
                "qr_id": qr_id,
                "qr_url": f"/qr/{qr_id}"
            }
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except json.JSONDecodeError:
            self.send_error(400, "JSON格式错误")
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
            if not status or status not in ['active', 'stopped']:
                self.send_error(400, "状态必须是 active 或 stopped")
                return
            
            # 更新状态
            if self.config_manager.update_status(qr_id, status):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response_data = {
                    "status": "success",
                    "message": f"状态已更新为: {status}",
                    "qr_id": qr_id
                }
                
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(404, "二维码不存在")
                
        except json.JSONDecodeError:
            self.send_error(400, "JSON格式错误")
        except Exception as e:
            print(f"更新状态错误: {e}")
            self.send_error(500, f"更新失败: {str(e)}")

def main():
    """主函数"""
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 10000))
    
    print("🌐 动态二维码系统服务器 v2.0")
    print("=" * 50)
    print(f"📡 监听地址: {host}:{port}")
    print(f"🕒 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建配置管理器
    config_manager = QRConfigManager()
    
    # 创建HTTP处理器
    def handler(*args, **kwargs):
        QRHandler(*args, config_manager=config_manager, **kwargs)
    
    try:
        # 启动服务器
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"✅ 服务器启动成功")
            print(f"🔗 控制台: http://{host}:{port}")
            print(f"🔌 API基址: http://{host}:{port}/api")
            print(f"📊 当前管理 {len(config_manager.data.get('qr_codes', {}))} 个二维码")
            print("🔄 服务器运行中...")
            
            httpd.serve_forever()
            
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
