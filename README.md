# 🌐 动态二维码系统

专业的云端二维码管理系统，支持动态控制和API管理。

## ✨ 功能特点

- 🔄 **动态控制** - 随时激活/停用二维码
- 📊 **数据统计** - 扫描次数、使用情况分析
- 🌍 **云端部署** - 24/7在线，全球访问
- 🔌 **完整API** - 支持程序化管理
- 📱 **移动友好** - 完美支持手机扫描

## 🚀 快速部署

### Render 部署

1. Fork 本仓库到您的 GitHub
2. 在 [Render](https://render.com) 创建新的 Web Service
3. 连接您的 GitHub 仓库
4. Render 会自动检测配置并部署

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/your-username/dynamic-qr-system.git
cd dynamic-qr-system

# 启动服务器
python app.py
```

## 📋 API 接口

### 基础接口

- `GET /` - 控制台界面
- `GET /health` - 健康检查
- `GET /qr/{id}` - 二维码重定向

### 管理接口

- `GET /api/qr` - 获取二维码列表
- `POST /api/qr` - 创建新二维码
- `POST /api/qr/{id}/status` - 更新二维码状态
- `GET /api/stats` - 获取统计信息

### 创建二维码

```bash
curl -X POST https://your-app.onrender.com/api/qr \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "unique-id",
    "email": "contact@example.com",
    "subject": "联系我们",
    "body": "您好，我通过二维码联系您。"
  }'
```

### 更新状态

```bash
curl -X POST https://your-app.onrender.com/api/qr/unique-id/status \
  -H "Content-Type: application/json" \
  -d '{"status": "stopped"}'
```

## 📁 文件结构

```
├── app.py              # 主服务器程序
├── render.yaml         # Render 部署配置
├── requirements.txt    # Python 依赖
├── runtime.txt        # Python 版本
├── README.md          # 项目文档
└── qr_data.json       # 数据存储 (自动生成)
```

## 🔧 环境变量

- `HOST` - 服务器地址 (默认: 0.0.0.0)
- `PORT` - 服务器端口 (默认: 10000)

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！