# 媒体库文件管理器 v1.4

> 智能媒体文件整理工具 - 支持自动重命名、智能分类、去重、中文标题识别

## 🌟 v1.4 新特性

### 核心更新
- ✅ **设置功能**：独立配置TMDB API Key和豆瓣Cookie
- ✅ **整理详情**：实时进度弹窗，8步进度跟踪
- ✅ **Linux/NAS优化**：完全兼容各种Linux系统和NAS
- ✅ **配置管理**：用户配置文件支持
- ✅ **代理支持**：HTTP/SOCKS5代理配置

### 界面优化
- ✅ 三个主按钮：一键整理入库 | 整理详情 | 设置
- ✅ 实时进度显示和日志
- ✅ 完成通知
- ✅ 简洁的设置界面

### 系统兼容
- ✅ Ubuntu, Debian, CentOS
- ✅ Synology DSM
- ✅ QNAP QTS
- ✅ TrueNAS/FreeNAS
- ✅ Unraid
- ✅ 支持所有主流文件系统

---

## 📦 快速开始

### 方法1: 自动安装（推荐）

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
# http://localhost:8090
```

### 方法2: Docker部署

```bash
# 1. 修改配置
nano docker-compose.yml

# 2. 启动容器
docker-compose up -d

# 3. 访问应用
# http://localhost:8090
```

---

## 🎯 使用流程

### 1. 配置API密钥（首次使用）

点击 **⚙️ 设置** 按钮：

```
TMDB API Key: 你的密钥
TMDB代理: http://proxy:port（可选）
豆瓣Cookie: 你的Cookie
```

**获取方法**：
- TMDB: https://www.themoviedb.org/settings/api
- 豆瓣: 登录 → F12 → Network → 复制Cookie

### 2. 配置路径

```
待整理目录: /path/to/待整理
电影输出: /path/to/电影
剧集输出: /path/to/剧集
```

### 3. 选择策略

- **自动比较**：智能比较质量（推荐）
- **跳过**：保留旧文件
- **替换**：用新文件替换
- **保留两个**：添加版本号

### 4. 开始整理

点击 **🚀 一键整理入库**

### 5. 查看进度

点击 **📊 整理详情** 查看实时进度

---

## 🔥 核心功能

### 智能重命名
- 自动识别电影/剧集
- 提取年份、季集信息
- 识别分辨率和来源
- 标准化文件名格式

### 中文标题识别
- 豆瓣优先（中文标题）
- TMDB备用（英文标题）
- 自动翻译英文标题
- 支持代理访问

### 智能去重
- 自动识别重复文件
- 质量评分系统
- 保留最佳版本
- 自动删除低质量版本

### 智能分类
- **电影**：动画电影、华语电影、外语电影
- **剧集**：国漫、日番、纪录片、国产剧、日韩剧、欧美剧

### 冲突处理
- 自动比较文件质量
- 智能决策保留/替换
- 支持保留多版本
- 实时处理冲突

### 自动清理
- 清理跳过的文件
- 删除空文件夹
- 释放磁盘空间
- 保持目录整洁

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

### 字幕
```
与视频文件同名，添加语言标识
例如: 流浪地球 (2019) [1080p-BluRay].chs.srt
```

---

## 🔧 系统要求

### 最低要求
- Python 3.6+
- 512MB 内存
- 100MB 磁盘空间

### 推荐配置
- Python 3.9+
- 1GB+ 内存
- 千兆局域网

### 支持的系统
- Ubuntu 20.04+
- Debian 11+
- CentOS 7+
- Synology DSM 7+
- QNAP QTS 5+
- TrueNAS CORE/SCALE
- Unraid 6+

### 支持的文件系统
- ext4, btrfs, ZFS（推荐）
- XFS, NTFS, exFAT
- NFS, SMB/CIFS

---

## 📁 项目结构

```
media-renamer/
├── app.py                      # 主程序
├── index.html                  # Web界面
├── install.sh                  # 安装脚本
├── Dockerfile                  # Docker镜像
├── docker-compose.yml          # Docker编排
├── README.md                   # 说明文档
├── 快速开始.md                 # 快速指南
├── NAS部署指南.md              # NAS部署
├── Linux_NAS优化方案.md        # 优化方案
├── 设置功能说明.md             # 设置说明
└── 最终部署检查清单.md         # 检查清单
```

---

## 🚀 部署方式

### 1. 直接运行
```bash
python3 app.py
```

### 2. systemd服务
```bash
sudo systemctl start media-renamer
sudo systemctl enable media-renamer
```

### 3. Docker容器
```bash
docker-compose up -d
```

### 4. NAS套件
参考 `NAS部署指南.md`

---

## 🔒 安全建议

### 网络安全
```bash
# 仅允许局域网访问
sudo ufw allow from 192.168.1.0/24 to any port 8090
```

### 配置安全
```bash
# 限制配置文件权限
chmod 600 ~/.media-renamer/config.json
```

### API密钥
- 使用自己的TMDB API Key
- 定期更新豆瓣Cookie
- 不要分享配置文件

---

## 📖 文档

### 用户文档
- [快速开始](快速开始.md) - 5分钟快速部署
- [设置功能说明](设置功能说明.md) - API配置指南
- [NAS部署指南](NAS部署指南.md) - NAS系统部署

### 技术文档
- [Linux/NAS优化方案](Linux_NAS优化方案.md) - 优化详情
- [Linux/NAS优化总结](Linux_NAS优化总结.md) - 优化总结
- [最终部署检查清单](最终部署检查清单.md) - 部署检查

### 功能文档
- [整理详情功能说明](整理详情功能说明.md) - 进度监控
- [文件冲突处理说明](文件冲突处理说明.md) - 冲突策略
- [自动清理功能说明](自动清理功能说明.md) - 清理机制

---

## 🐛 故障排查

### 常见问题

#### 1. 无法访问
```bash
# 检查服务
ps aux | grep app.py

# 检查端口
netstat -tuln | grep 8090
```

#### 2. 权限错误
```bash
# 修改权限
sudo chmod -R 755 /path/to/media
sudo chown -R $USER:$USER /path/to/media
```

#### 3. API无法访问
- 检查API Key是否正确
- 检查代理是否正常
- 检查网络连接

#### 4. 豆瓣Cookie过期
- 重新登录豆瓣
- 获取新的Cookie
- 在设置中更新

---

## 🔄 更新日志

### v1.4 (2025-01-XX)
- ✅ 添加设置功能
- ✅ 添加整理详情弹窗
- ✅ Linux/NAS全面优化
- ✅ 配置文件支持
- ✅ 代理支持（HTTP/SOCKS5）

### v1.3 (2025-01-XX)
- ✅ 自动清理功能
- ✅ 文件冲突处理
- ✅ 智能分类
- ✅ 中文标题识别

### v1.2 (2024-XX-XX)
- ✅ 智能去重
- ✅ 质量评分系统

### v1.1 (2024-XX-XX)
- ✅ 基础重命名功能
- ✅ Web界面

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 💬 支持

如遇问题，请提供：
1. 系统版本
2. Python版本
3. 错误日志
4. 复现步骤

---

## 🎉 致谢

感谢所有使用和支持本项目的用户！

---

**享受自动化的媒体库管理体验！** 🎬
