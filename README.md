# 媒体库文件管理器

> 智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别、二级分类、一键更新

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20NAS-orange.svg)](docs/部署指南.md)

---

## ✨ 核心特性

### 🎬 智能重命名
- 自动识别电影/剧集信息
- 提取年份、季集、分辨率
- 标准化文件名格式
- 支持多种视频格式

### 🌐 中文标题识别
- 豆瓣 + TMDB 双源查询
- 自动翻译英文标题
- 支持代理访问
- 智能匹配最佳结果

### 🎯 智能去重
- 自动识别重复文件
- 质量评分系统
- 保留最佳版本
- 支持多版本管理

### 📁 二级分类 ✨ NEW
- **规则分类**：基于 TMDB 元数据自动分类（类型、语言、国家等）
- **自动检测结构**：识别现有媒体库目录
- **智能匹配分类**：自动匹配现有分类目录
- **中英文支持**：支持中英文目录名称
- **自动创建目录**：缺失的分类自动创建
- **路径预览**：查看完整配置和路径结构
- **一键迁移**：从旧配置自动迁移

**内置分类规则**：
- 电影：动画电影、华语电影、外语电影
- 电视剧：国漫、日番、纪录片、儿童、综艺、国产剧、欧美剧、日韩剧

### ⚙️ 灵活配置
- 统一的媒体库路径配置
- 支持HTTP/SOCKS5代理
- 配置文件持久化
- 向后兼容旧配置

### � 一实时监控
- 8步进度跟踪
- 实时日志显示
- 完成通知
- 详细的处理报告

### 📊 实时日志推送 🔥 NEW (v1.2.0)
- **实时进度显示**：Web界面实时查看处理进度
- **彩色日志级别**：DEBUG/INFO/WARNING/ERROR 颜色区分
- **进度条显示**：当前进度/总数实时更新
- **自动滚动**：自动滚动到最新日志
- **SSE技术**：Server-Sent Events 实时推送

### 🚀 元数据查询优化 🔥 NEW (v1.2.0)
- **TitleParser**：智能解析文件名，移除Release Group和技术参数
- **TitleMapper**：标题映射表，预配置30+常用作品
- **QueryStrategy**：5种查询策略，自动失败重试
- **QueryLogger**：详细查询日志，便于调试
- **识别准确率**：从60%提升到90%+

### 🔄 一键更新
- Web界面一键更新
- 自动版本管理
- 代理支持
- 自动重启服务
- 更新历史记录

### ☁️ 115网盘支持
- 二维码扫码登录
- 智能整理网盘文件
- 批量处理支持
- 操作历史记录

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

### 云服务器部署 ☁️

#### 方法 1：一键部署（推荐）🚀

**推荐系统**：Ubuntu 22.04 LTS

```bash
# 1. 下载部署脚本
wget https://raw.githubusercontent.com/haishuai1987/media-sorter/main/deploy-cloud.sh

# 2. 运行脚本
chmod +x deploy-cloud.sh
./deploy-cloud.sh

# 3. 按提示输入信息
# - 域名
# - 是否配置 SSL
# - 邮箱（如果配置 SSL）

# 4. 等待自动部署完成

# 5. 访问应用
# https://your-domain.com
```

详见 [一键部署脚本使用说明](docs/一键部署脚本使用说明.md)

---

#### 方法 2：手动部署

```bash
# 1. 克隆项目
git clone https://github.com/haishuai1987/media-sorter.git
cd media-renamer

# 2. 设置环境变量（可选）
cp .env.example .env
nano .env

# 3. 配置 Nginx 反向代理
sudo apt install nginx
# 配置文件见文档

# 4. 配置 SSL（可选）
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 5. 创建 Systemd 服务
sudo nano /etc/systemd/system/media-renamer.service
sudo systemctl enable media-renamer
sudo systemctl start media-renamer

# 6. 访问应用
# https://your-domain.com
```

详见 [云服务器部署指南](docs/云服务器部署指南.md)

---

## 📖 使用流程

### 1️⃣ 配置API密钥（首次使用）

点击 **⚙️ 设置** 按钮，配置：

- **TMDB API Key**: [获取地址](https://www.themoviedb.org/settings/api)
- **TMDB代理**: http://proxy:port（可选）
- **豆瓣Cookie**: 登录豆瓣 → F12 → Network → 复制Cookie

### 2️⃣ 配置路径

**新配置方式（推荐）** ✨

```
待整理路径: /path/to/待整理
媒体库路径: /path/to/媒体库
语言偏好: 中文 或 English
```

**功能**：
- 🔍 点击检测按钮，自动识别现有结构
- 👁️ 点击预览路径，查看配置详情
- 📁 支持二级分类（动作、喜剧、美剧等）
- 🌐 支持中英文目录名称
- 🔄 自动配置迁移提示

**旧配置方式（兼容）**

```
待整理目录: /path/to/待整理
电影输出目录: /path/to/电影
剧集输出目录: /path/to/剧集
```

详见 [配置迁移指南](docs/配置迁移指南.md)

### 3️⃣ 选择冲突策略

- **自动比较**: 智能比较质量（推荐）
- **跳过**: 保留旧文件
- **替换**: 用新文件替换
- **保留两个**: 添加版本号

### 4️⃣ 预览路径（可选）

点击 **👁️ 预览路径** 查看：
- 待整理路径
- 媒体库路径
- 检测到的目录结构
- 文件将保存到的路径格式

### 5️⃣ 开始整理

点击 **🚀 一键整理入库**

### 6️⃣ 查看进度

点击 **📊 整理详情** 实时监控

---

## 🎬 目录结构

### 标准结构

```
媒体库/
├── 电影/（或 Movies/）
│   ├── 动作/（或 Action/）
│   │   └── 速度与激情9 (2021)/
│   │       └── 速度与激情9 (2021).mkv
│   ├── 喜剧/（或 Comedy/）
│   └── 科幻/（或 Sci-Fi/）
└── 电视剧/（或 TV Shows/）
    ├── 美剧/（或 US Drama/）
    │   └── 权力的游戏/
    │       └── Season 01/
    │           └── 权力的游戏 - S01E01 - 第 01 集.mkv
    ├── 日剧/（或 Japanese Drama/）
    └── 韩剧/（或 Korean Drama/）
```

### 文件命名

**电影**：
```
电影名 (年份).ext
例如: 流浪地球 (2019).mkv
```

**电视剧**：
```
剧名 - SXXEXX - 第 XX 集.ext
例如: 三体 - S01E01 - 第 01 集.mkv
```

详见 [媒体库结构说明](docs/媒体库结构说明.md)

---

## 📊 处理流程

系统自动完成以下步骤：

1. **📂 智能扫描** - 扫描待整理目录
2. **🌐 中文标题识别** - 获取中文标题
3. **🎯 智能去重** - 识别并删除重复
4. **📝 标准化重命名** - 生成标准文件名
5. **📁 智能分类** - 自动分类到二级目录
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

### 支持的文件格式
- **视频**: mp4, mkv, avi, mov, ts, iso, rmvb, mpeg, mpg, wmv, 3gp, asf, m4v, flv, m2ts, tp, f4v
- **字幕**: srt, ass, ssa

---

## 📚 文档

### 快速入门
- [📖 文档索引](docs/README.md) - 所有文档导航
- [� 快速开始](docs/快速开始.md) - 5分钟快速部署
- [📘 使用指南](docs/使用指南.md) - 详细使用说明

### 功能文档
- [⚙️ 功能说明](docs/功能说明.md) - 所有功能详解
- [📁 媒体库结构说明](docs/媒体库结构说明.md) ✨ - 目录结构和命名规则
- [🔄 配置迁移指南](docs/配置迁移指南.md) ✨ - 从旧配置迁移到新配置
- [❓ 常见问题](docs/常见问题.md) - FAQ和故障排查

### 技术文档
- [🔌 API文档](docs/API文档.md) ✨ - API接口说明
- [🚀 部署指南](docs/部署指南.md) - 各系统部署方法
- [📝 更新日志](docs/更新日志.md) - 版本历史

### 专题文档
- [☁️ 115网盘](docs/115网盘/) - 115网盘相关文档
- [🔄 更新相关](docs/更新相关/) - 更新功能相关文档

---

## 🐛 故障排查

### 无法访问
```bash
# 检查服务
ps aux | grep app.py

# 检查端口
netstat -tuln | grep 8000
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

### 配置问题
- 查看 [配置迁移指南](docs/配置迁移指南.md)
- 查看 [常见问题](docs/常见问题.md)

---

## 🆕 最新更新

### v1.8.0 (2025-01-XX) 🎨

**Web界面优化**：
- ✅ Toast通知系统
- ✅ 错误统计面板
- ✅ 操作历史记录
- ✅ 实时错误提示
- ✅ 友好的用户反馈

**新增API**：
- ✅ /api/error-stats - 错误统计
- ✅ /api/operation-history - 操作历史

**用户体验**：
- ✅ 实时反馈
- ✅ 自动消失通知
- ✅ 滑入/滑出动画
- ✅ 点击关闭

### v1.7.0 (2025-01-XX) 🛡️

**错误处理增强**：
- ✅ 统一错误处理框架
- ✅ 自动重试机制
- ✅ 用户友好的错误消息
- ✅ 错误分类和恢复策略

### v1.6.0 (2025-01-XX) ⚡

**性能优化**：
- ✅ Release Group 正则预编译
- ✅ 性能提升 10-20 倍

[查看完整更新日志](docs/更新日志.md)

---

## 🎯 特色功能

### 二级分类 ✨

**分类方式**：
1. **规则分类**：基于 TMDB 元数据（类型、语言、国家）自动分类
2. **目录检测**：检测现有分类目录，智能匹配文件位置

**内置分类规则**：

**电影**：
- 动画电影（genre_ids: 16）
- 华语电影（语言：中文）
- 外语电影（其他语言）

**电视剧**：
- 国漫（动画 + 中国）
- 日番（动画 + 日本）
- 纪录片（genre_ids: 99）
- 儿童（genre_ids: 10762）
- 综艺（genre_ids: 10764, 10767）
- 国产剧（中国、台湾、香港）
- 欧美剧（美国、英国、法国等）
- 日韩剧（日本、韩国、泰国等）
- 未分类（其他）

**智能匹配**：
- 根据 TMDB 元数据自动分类
- 检测现有分类目录
- 精确和模糊匹配
- 支持中英文混合
- 自动创建缺失分类

### 配置迁移 🔄

**自动迁移**：
- 检测旧配置
- 智能推断媒体库路径
- 一键完成迁移
- 保留旧配置备份

**手动迁移**：
- 详细的迁移指南
- 步骤说明
- 常见问题解答

### 路径预览 👁️

**预览内容**：
- 待整理路径
- 媒体库路径
- 检测到的目录结构
- 文件将保存到的路径格式
- 冲突处理策略

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南
1. Fork 本项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🎉 致谢

感谢所有使用和支持本项目的用户！

特别感谢：
- TMDB 提供的电影数据库API
- 豆瓣提供的中文电影信息
- 所有贡献者和反馈用户

---

## 📞 联系方式

- 📧 提交 Issue
- 📖 查看 [文档](docs/README.md)
- ❓ 查看 [常见问题](docs/常见问题.md)

---

**享受自动化的媒体库管理体验！** 🎬✨

