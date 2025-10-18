# 媒体库文件管理器 v1.4

> 智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20NAS-orange.svg)](docs/部署指南.md)

---

## ✨ 核心特性

### 🎬 智能重命名
- 自动识别电影/剧集信息
- 提取年份、季集、分辨率
- 标准化文件名格式

### 🌐 中文标题识别
- 豆瓣 + TMDB 双源查询
- 自动翻译英文标题
- 支持代理访问

### 🎯 智能去重
- 自动识别重复文件
- 质量评分系统
- 保留最佳版本

### 📁 智能分类
- **电影**：动画/华语/外语
- **剧集**：国漫/日番/纪录片/国产剧/日韩剧/欧美剧

### ⚙️ 独立配置
- 每个用户配置自己的API密钥
- 支持HTTP/SOCKS5代理
- 配置文件持久化

### 📊 实时监控
- 8步进度跟踪
- 实时日志显示
- 完成通知

---

## 🚀 快速开始

### 一键安装

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/media-renamer.git
cd media-renamer

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 启动服务
python3 app.py

# 4. 访问应用
# 浏览器打开: http://localhost:8090
```

### Docker部署

```bash
# 1. 修改配置
nano docker-compose.yml

# 2. 启动容器
docker-compose up -d

# 3. 访问应用
# http://localhost:8090
```

---

## 📖 使用流程

### 1️⃣ 配置API密钥（首次使用）

点击 **⚙️ 设置** 按钮，配置：

- **TMDB API Key**: [获取地址](https://www.themoviedb.org/settings/api)
- **TMDB代理**: http://proxy:port（可选）
- **豆瓣Cookie**: 登录豆瓣 → F12 → Network → 复制Cookie

### 2️⃣ 配置路径

```
待整理目录: /path/to/待整理
电影输出目录: /path/to/电影
剧集输出目录: /path/to/剧集
```

### 3️⃣ 选择冲突策略

- **自动比较**: 智能比较质量（推荐）
- **跳过**: 保留旧文件
- **替换**: 用新文件替换
- **保留两个**: 添加版本号

### 4️⃣ 开始整理

点击 **🚀 一键整理入库**

### 5️⃣ 查看进度

点击 **📊 整理详情** 实时监控

---

## 🎬 命名规则

### 电影
```
电影名称 (年份) [分辨率-来源].扩展名
例如: 流浪地球 (2019) [1080p-BluRay].mkv
```

### 剧集
```
剧集名称 (年份)/Season XX/剧集名称 - SXXEXX [分辨率-来源].扩展名
例如: 三体 (2023)/Season 01/三体 - S01E01 [1080p-WEB-DL].mkv
```

---

## 📊 处理流程

系统自动完成8个步骤：

1. **📂 智能扫描** - 扫描待整理目录
2. **🌐 中文标题识别** - 获取中文标题
3. **🎯 智能去重** - 识别并删除重复
4. **📝 标准化重命名** - 生成标准文件名
5. **📁 智能分类** - 自动分类
6. **🚚 自动移动** - 移动到目标目录
7. **⚔️ 冲突处理** - 处理同名文件
8. **🧹 自动清理** - 清理和整理

---

## 🔧 系统要求

### 最低要求
- Python 3.6+
- 512MB 内存
- 100MB 磁盘空间

### 支持的系统
- Ubuntu, Debian, CentOS
- Synology DSM
- QNAP QTS
- TrueNAS/FreeNAS
- Unraid

### 支持的文件系统
- ext4, btrfs, ZFS
- XFS, NTFS, exFAT
- NFS, SMB/CIFS

---

## 📚 文档

### 用户文档
- [快速开始](docs/快速开始.md) - 5分钟快速部署
- [使用指南](docs/使用指南.md) - 详细使用说明
- [部署指南](docs/部署指南.md) - 各系统部署方法

### 功能文档
- [功能说明](docs/功能说明.md) - 所有功能详解
- [常见问题](docs/常见问题.md) - FAQ和故障排查

### 开发文档
- [更新日志](docs/更新日志.md) - 版本历史
- [开发指南](docs/开发指南.md) - 贡献指南

---

## 🐛 故障排查

### 无法访问
```bash
# 检查服务
ps aux | grep app.py

# 检查端口
netstat -tuln | grep 8090
```

### 权限错误
```bash
# 修改权限
sudo chmod -R 755 /path/to/media
```

### API无法访问
- 检查API Key是否正确
- 检查代理是否正常
- 检查网络连接

更多问题请查看 [常见问题文档](docs/常见问题.md)

---

## 🔄 更新日志

### v1.4 (2025-01-XX)
- ✅ 添加设置功能
- ✅ 添加整理详情弹窗
- ✅ Linux/NAS全面优化
- ✅ 配置文件支持
- ✅ 代理支持

[查看完整更新日志](docs/更新日志.md)

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 🎉 致谢

感谢所有使用和支持本项目的用户！

---

**享受自动化的媒体库管理体验！** 🎬
