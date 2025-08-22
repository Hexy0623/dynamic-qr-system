#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地二维码管理工具 - 连接云端服务器
"""

import os
import sys
import json
import uuid
import qrcode
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

class CloudQRManager:
    """云端二维码管理器"""
    
    def __init__(self):
        self.config_file = "local_qr_config.json"
        self.cloud_url = "https://dynamic-qr-system.onrender.com"
        self.config_data = self.load_config()
        
    def load_config(self):
        """加载本地配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {"qr_codes": {}, "settings": {"cloud_url": self.cloud_url}}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def create_qr(self, email, subject="", body="", cc="", output_path=None):
        """创建二维码"""
        qr_id = str(uuid.uuid4())
        
        # 构建云端URL
        qr_url = f"{self.cloud_url}/qr/{qr_id}"
        
        # 生成二维码图片
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 保存图片
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"qr_{qr_id[:8]}_{timestamp}.png"
        
        img.save(output_path)
        
        # 保存到本地配置
        qr_data = {
            "qr_id": qr_id,
            "email": email,
            "subject": subject,
            "body": body,
            "cc": cc,
            "status": "active",
            "qr_url": qr_url,
            "qr_path": output_path,
            "created_at": datetime.now().isoformat()
        }
        
        self.config_data["qr_codes"][qr_id] = qr_data
        self.save_config()
        
        # 通知云端服务器（如果可用）
        self.sync_to_cloud(qr_id, email, subject, body, cc)
        
        return qr_data
    
    def sync_to_cloud(self, qr_id, email, subject, body, cc):
        """同步数据到云端服务器"""
        try:
            # 调用云端API创建二维码
            api_url = f"{self.cloud_url}/api/qr"
            data = {
                "qr_id": qr_id,
                "email": email,
                "subject": subject,
                "body": body,
                "cc": cc
            }
            
            response = requests.post(api_url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 云端同步成功: {qr_id[:8]}... -> {email}")
                return True
            else:
                print(f"⚠️ 云端同步失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 云端同步错误: {e}")
            return False
    
    def get_all_qr_codes(self):
        """获取所有二维码"""
        return self.config_data.get("qr_codes", {})
    
    def update_qr_status(self, qr_id, status):
        """更新二维码状态"""
        if qr_id in self.config_data["qr_codes"]:
            # 更新本地状态
            self.config_data["qr_codes"][qr_id]["status"] = status
            self.save_config()
            
            # 同步到云端
            self.sync_status_to_cloud(qr_id, status)
            return True
        return False
    
    def sync_status_to_cloud(self, qr_id, status):
        """同步状态到云端"""
        try:
            api_url = f"{self.cloud_url}/api/qr/{qr_id}/status"
            data = {"status": status}
            
            response = requests.post(api_url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 状态同步成功: {qr_id[:8]}... -> {status}")
                return True
            else:
                print(f"⚠️ 状态同步失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 状态同步错误: {e}")
            return False
    
    def test_cloud_connection(self):
        """测试云端连接"""
        try:
            response = requests.get(self.cloud_url, timeout=5)
            return response.status_code == 200
        except:
            return False

class QRManagerGUI:
    """二维码管理界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌐 云端二维码管理工具")
        self.root.geometry("800x600")
        
        self.qr_manager = CloudQRManager()
        self.save_path = None
        
        self.setup_ui()
        self.refresh_qr_list()
        self.check_cloud_status()
    
    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 云端状态
        status_frame = ttk.LabelFrame(main_frame, text="☁️ 云端状态", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.cloud_status_label = ttk.Label(status_frame, text="检查中...", foreground="orange")
        self.cloud_status_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(status_frame, text="🔄 刷新状态", 
                  command=self.check_cloud_status).grid(row=0, column=1, padx=(10, 0))
        
        # 创建二维码区域
        create_frame = ttk.LabelFrame(main_frame, text="➕ 创建新二维码", padding="10")
        create_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 邮箱
        ttk.Label(create_frame, text="收件邮箱:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(create_frame, textvariable=self.email_var, width=40)
        email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 主题
        ttk.Label(create_frame, text="邮件主题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.subject_var = tk.StringVar(value="来自二维码的咨询")
        subject_entry = ttk.Entry(create_frame, textvariable=self.subject_var, width=40)
        subject_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 内容
        ttk.Label(create_frame, text="邮件内容:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.body_text = tk.Text(create_frame, height=3, width=40)
        self.body_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.body_text.insert("1.0", "您好，我通过二维码联系您。")
        
        # 抄送
        ttk.Label(create_frame, text="抄送邮箱:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cc_var = tk.StringVar()
        cc_entry = ttk.Entry(create_frame, textvariable=self.cc_var, width=40)
        cc_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 按钮
        button_frame = ttk.Frame(create_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="📁 选择保存位置", 
                  command=self.select_save_path).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🚀 创建二维码", 
                  command=self.create_qr).pack(side=tk.LEFT, padx=5)
        
        # 二维码列表
        list_frame = ttk.LabelFrame(main_frame, text="📋 二维码列表", padding="10")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建表格
        columns = ("ID", "邮箱", "主题", "状态", "创建时间")
        self.qr_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列
        self.qr_tree.heading("ID", text="ID")
        self.qr_tree.heading("邮箱", text="邮箱")
        self.qr_tree.heading("主题", text="主题")
        self.qr_tree.heading("状态", text="状态")
        self.qr_tree.heading("创建时间", text="创建时间")
        
        self.qr_tree.column("ID", width=80)
        self.qr_tree.column("邮箱", width=200)
        self.qr_tree.column("主题", width=150)
        self.qr_tree.column("状态", width=80)
        self.qr_tree.column("创建时间", width=150)
        
        self.qr_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.qr_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.qr_tree.configure(yscrollcommand=scrollbar.set)
        
        # 操作按钮
        action_frame = ttk.Frame(list_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(action_frame, text="✅ 激活", 
                  command=lambda: self.update_status("active")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="⏸️ 停用", 
                  command=lambda: self.update_status("stopped")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="📄 查看详情", 
                  command=self.show_details).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🔄 刷新列表", 
                  command=self.refresh_qr_list).pack(side=tk.LEFT, padx=5)
        
        # 配置列权重
        create_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def check_cloud_status(self):
        """检查云端状态"""
        def check():
            if self.qr_manager.test_cloud_connection():
                self.root.after(0, lambda: self.cloud_status_label.config(
                    text=f"✅ 云端在线: {self.qr_manager.cloud_url}", 
                    foreground="green"
                ))
            else:
                self.root.after(0, lambda: self.cloud_status_label.config(
                    text=f"❌ 云端离线: {self.qr_manager.cloud_url}", 
                    foreground="red"
                ))
        
        import threading
        threading.Thread(target=check, daemon=True).start()
    
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
        
        subject = self.subject_var.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()
        cc = self.cc_var.get().strip()
        
        try:
            result = self.qr_manager.create_qr(email, subject, body, cc, self.save_path)
            
            messagebox.showinfo("成功", 
                              f"二维码创建成功！\n\n"
                              f"ID: {result['qr_id'][:8]}...\n"
                              f"文件: {result['qr_path']}\n"
                              f"云端URL: {result['qr_url']}")
            
            self.refresh_qr_list()
            self.save_path = None  # 重置保存路径
            
        except Exception as e:
            messagebox.showerror("错误", f"创建二维码失败: {str(e)}")
    
    def refresh_qr_list(self):
        """刷新二维码列表"""
        # 清空现有项目
        for item in self.qr_tree.get_children():
            self.qr_tree.delete(item)
        
        # 添加二维码数据
        qr_codes = self.qr_manager.get_all_qr_codes()
        for qr_id, data in qr_codes.items():
            created_time = data.get("created_at", "")
            if created_time:
                try:
                    dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    created_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            status_text = "✅ 激活" if data.get("status") == "active" else "⏸️ 停用"
            
            self.qr_tree.insert("", "end", values=(
                qr_id[:8] + "...",
                data.get("email", ""),
                data.get("subject", ""),
                status_text,
                created_time
            ))
    
    def update_status(self, status):
        """更新选中二维码的状态"""
        selection = self.qr_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要操作的二维码！")
            return
        
        # 获取完整ID
        item = self.qr_tree.item(selection[0])
        short_id = item["values"][0].replace("...", "")
        
        # 查找完整ID
        qr_codes = self.qr_manager.get_all_qr_codes()
        full_id = None
        for qr_id in qr_codes.keys():
            if qr_id.startswith(short_id):
                full_id = qr_id
                break
        
        if full_id:
            if self.qr_manager.update_qr_status(full_id, status):
                status_text = "激活" if status == "active" else "停用"
                messagebox.showinfo("成功", f"二维码已{status_text}！")
                self.refresh_qr_list()
            else:
                messagebox.showerror("错误", "更新状态失败！")
        else:
            messagebox.showerror("错误", "找不到对应的二维码！")
    
    def show_details(self):
        """显示二维码详情"""
        selection = self.qr_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要查看的二维码！")
            return
        
        # 获取完整ID和数据
        item = self.qr_tree.item(selection[0])
        short_id = item["values"][0].replace("...", "")
        
        qr_codes = self.qr_manager.get_all_qr_codes()
        qr_data = None
        for qr_id, data in qr_codes.items():
            if qr_id.startswith(short_id):
                qr_data = data
                break
        
        if qr_data:
            details = f"""二维码详细信息

ID: {qr_data.get('qr_id', '')}
邮箱: {qr_data.get('email', '')}
主题: {qr_data.get('subject', '')}
内容: {qr_data.get('body', '')}
抄送: {qr_data.get('cc', '')}
状态: {qr_data.get('status', '')}
云端URL: {qr_data.get('qr_url', '')}
本地文件: {qr_data.get('qr_path', '')}
创建时间: {qr_data.get('created_at', '')}"""
            
            messagebox.showinfo("二维码详情", details)
        else:
            messagebox.showerror("错误", "找不到对应的二维码数据！")
    
    def run(self):
        """运行界面"""
        self.root.mainloop()

def main():
    """主函数"""
    print("🌐 启动云端二维码管理工具...")
    
    # 检查依赖
    try:
        import qrcode
        import requests
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请运行: pip install qrcode[pil] requests")
        return 1
    
    # 启动GUI
    app = QRManagerGUI()
    app.run()
    
    return 0

if __name__ == "__main__":
    exit(main())
