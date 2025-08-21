# 🌐 动态二维码邮件系统

一个功能强大的动态二维码系统，用户扫描二维码后可直接跳转到邮件客户端发送预设的邮件。支持本地部署和云端部署，具有动态控制功能。

## ✨ 主要特性

- 🎯 **直接邮件跳转** - 扫描即可打开邮件客户端
- 🔄 **动态控制** - 可随时启用/停用二维码
- 🌍 **云端部署** - 支持Render等免费云平台
- 📊 **实时监控** - 扫描统计和状态管理
- 🎨 **图形界面** - 简单易用的GUI管理界面
- 🛡️ **稳定可靠** - 自动故障检测和恢复

## 🚀 快速开始

### 本地部署

1. **克隆项目**
   ```bash
   git clone https://github.com/你的用户名/dynamic-qr-system.git
   cd dynamic-qr-system
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动系统**
   ```bash
   python integrated_qr_system.py
   ```

4. **创建二维码**
   - 在GUI界面中填写邮箱信息
   - 点击"生成二维码"
   - 扫描生成的二维码测试

### 云端部署（Render）

1. **Fork此项目到您的GitHub**

2. **注册Render账号**
   - 访问 [Render.com](https://render.com)
   - 使用GitHub账号登录

3. **创建Web Service**
   - 选择您的GitHub仓库
   - 使用以下配置：
     ```
     Build Command: pip install -r requirements.txt
     Start Command: python render_server.py
     Plan: Free
     ```

4. **等待部署完成**
   - 获得公网访问地址
   - 重新生成二维码使用新地址

详细部署指南请参考：[Render免费托管部署指南.md](docs/Render免费托管部署指南.md)

## 📋 系统要求

- **Python**: 3.9+ (推荐3.13.4)
- **内存**: 最少512MB
- **网络**: 需要网络连接（云端部署）

## 📁 项目结构

```
dynamic-qr-system/
├── integrated_qr_system.py      # 主程序（GUI + 服务器）
├── render_server.py             # 云端部署启动文件
├── 简化服务器管理工具.py         # 服务器管理工具
├── 启动系统.py                  # 系统启动助手
├── network_helper.py            # 网络配置工具
├── requirements.txt             # Python依赖
├── runtime.txt                  # Python版本（Render用）
├── render.yaml                  # Render部署配置
└── docs/                        # 文档目录
    ├── Render免费托管部署指南.md
    └── Render部署清单.md
```

## 🎮 使用说明

### 基本操作

1. **创建二维码**
   - 填写收件人邮箱
   - 设置邮件主题和内容
   - 点击"生成二维码"

2. **管理二维码**
   - 查看所有二维码列表
   - 启用/停用特定二维码
   - 查看扫描统计

3. **网络配置**
   - 设置服务器端口
   - 检测本地和公网IP
   - 配置云端部署

### 高级功能

- **批量管理** - 一键启用/停用所有二维码
- **扫描日志** - 详细的访问记录
- **自动重启** - 服务器异常自动恢复
- **状态监控** - 实时服务器状态显示

## 🔧 部署选项

### 1. 本地网络部署
适合内网使用，同一WiFi下的设备可以扫描

### 2. 云服务器部署
使用Render、Heroku等免费云平台，全球访问

### 3. 内网穿透部署
使用ngrok等工具，将本地服务暴露到公网

## 📊 技术特点

- **动态控制** - 二维码指向服务器，可随时更改状态
- **直接跳转** - 使用mailto协议，直接打开邮件客户端
- **跨平台兼容** - 支持iOS、Android等主流扫码器
- **自动重启** - 检测到异常自动重启服务
- **数据持久化** - 使用SQLite存储二维码信息

## 🚨 常见问题

### Q: 二维码扫描后没有反应？
A: 检查服务器是否正常运行，使用服务器管理工具重启

### Q: 第一次能扫描，第二次不行？
A: 可能是服务器进程异常，重启服务器即可解决

### Q: 如何部署到云端？
A: 参考[Render部署指南](docs/Render免费托管部署指南.md)

### Q: 二维码失效怎么办？
A: 检查服务器状态，确保服务正常运行

## 🤝 贡献

欢迎提交Issues和Pull Requests！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢 [qrcode](https://github.com/lincolnloop/python-qrcode) 提供二维码生成功能
- 感谢 [Pillow](https://python-pillow.org/) 提供图像处理支持
- 感谢 [Render](https://render.com) 提供免费云托管服务

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看[常见问题解决方案](docs/)
2. 提交[Issue](https://github.com/你的用户名/dynamic-qr-system/issues)
3. 查看项目文档

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！