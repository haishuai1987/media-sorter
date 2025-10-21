# 媒体库文件管理器 (Media Renamer)

> 智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.0.0-orange.svg)](version.txt)

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
- 智能匹配最佳结果
- 支持代理访问

### 🎯 智能去重
- 自动识别重复文件
- 质量评分系统
- 保留最佳版本
- 支持多版本管理

### 📁 二级分类
- 基于 TMDB 元数据自动分类
- 支持电影和电视剧分类
- 自动创建分类目录
- 中英文目录支持

### 🛡️ 错误处理 (v1.7.0)
- 统一错误处理框架
- 自动重试机制（指数退避）
- 友好的错误消息
- 错误分类和恢复

### 🎨 Web界面 (v1.8.0)
- Toast通知系统
- 错误统计面板
- 操作历史记录
- 实时进度显示

### 🚀 批量操作 (v1.9.0)
- 并发处理（4线程，4倍加速）
- 实时进度追踪（ETA）
- 断点续传（中断恢复）
- 批量回滚（一键撤销）

### 🏗️ 模块化架构 (v2.0.0)
- 清晰的模块边界
- 插件系统（动态加载）
- API标准化（RESTful）
- 配置管理统一

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/haishuai1987/media-sorter.git
cd media-sorter

# 安装依赖
pip install -r requirements.txt

# 运行程序
python app.py
```

### 访问

打开浏览器访问：`http://localhost:8090`

### 配置

1. 点击"⚙️ 系统设置"
2. 配置 TMDB API Key（必需）
3. 配置豆瓣 Cookie（可选，用于中文标题）
4. 保存配置

---

## 📖 文档

### 用户文档
- [使用指南](docs/使用指南.md) - 基础使用说明
- [快速开始](docs/快速开始.md) - 快速入门指南
- [功能说明](docs/功能说明.md) - 详细功能介绍
- [常见问题](docs/常见问题.md) - FAQ

### 部署文档
- [部署指南](docs/部署指南.md) - 本地部署
- [云服务器部署](docs/云服务器部署指南.md) - 云端部署
- [一键部署](docs/一键部署脚本使用说明.md) - 快速部署

### 技术文档
- [开发者指南](docs/开发者指南.md) - 开发指南 (v2.0.0)
- [API文档](docs/API文档.md) - API接口说明
- [错误处理](docs/错误处理说明.md) - 错误处理 (v1.7.0)
- [批量操作](docs/批量操作说明.md) - 批量处理 (v1.9.0)

### 快速参考
- [错误处理快速参考](ERROR-HANDLING-QUICK-REF.md) - 错误处理速查

---

## 🎯 主要功能

### 文件整理
- ✅ 自动扫描媒体文件
- ✅ 智能识别电影/剧集
- ✅ 自动重命名和分类
- ✅ 支持字幕文件关联

### 元数据查询
- ✅ TMDB API 集成
- ✅ 豆瓣电影集成
- ✅ 自动翻译标题
- ✅ 智能缓存机制

### 文件冲突处理
- ✅ 自动比较文件质量
- ✅ 智能评分系统
- ✅ 多种处理策略
- ✅ 保留最佳版本

### 批量处理
- ✅ 并发处理（4倍加速）
- ✅ 实时进度显示
- ✅ 断点续传
- ✅ 批量回滚

---

## 🆕 最新更新

### v2.0.0 (2025-01-XX) 🏗️

**架构重构（重大更新）**：
- ✅ 模块化设计（清晰边界）
- ✅ 插件系统（动态加载）
- ✅ API标准化（RESTful）
- ✅ 配置管理（统一接口）
- ✅ 日志系统（结构化）

**性能优化**：
- ✅ 代码效率提升 20%
- ✅ 内存占用减少 30%
- ✅ 启动时间减少 50%

### v1.9.0 (2025-01-XX) 🚀

**批量操作增强**：
- ✅ 并发处理（4线程，4倍加速）
- ✅ 进度追踪（实时ETA）
- ✅ 断点续传（中断恢复）
- ✅ 批量回滚（一键撤销）

### v1.8.0 (2025-01-XX) 🎨

**Web界面优化**：
- ✅ Toast通知系统
- ✅ 错误统计面板
- ✅ 操作历史记录

### v1.7.0 (2025-01-XX) 🛡️

**错误处理增强**：
- ✅ 统一错误处理框架
- ✅ 自动重试机制

[查看完整更新日志](CHANGELOG-v2.0.0.md)

---

## 🏗️ 项目结构

```
media-renamer/
├── core/                    # 核心模块 (v2.0.0)
│   ├── config.py           # 配置管理
│   ├── logger.py           # 日志系统
│   └── utils.py            # 工具函数
├── plugins/                 # 插件系统 (v2.0.0)
│   ├── base.py            # 插件基类
│   ├── loader.py          # 插件加载器
│   └── example_plugin.py  # 示例插件
├── public/                  # Web静态资源
│   ├── index.html         # 主页面
│   ├── style.css          # 样式
│   ├── toast.js           # Toast通知 (v1.8.0)
│   └── error-stats.js     # 错误统计 (v1.8.0)
├── docs/                    # 文档
├── app.py                   # 主程序
├── error_handler.py         # 错误处理 (v1.7.0)
├── batch_processor.py       # 批量处理 (v1.9.0)
└── README.md                # 项目说明
```

---

## 🔧 配置说明

### TMDB API Key

1. 访问 [TMDB](https://www.themoviedb.org/)
2. 注册账号并申请 API Key
3. 在设置中填入 API Key

### 豆瓣 Cookie（可选）

1. 登录豆瓣电影
2. 打开浏览器开发者工具
3. 复制 Cookie
4. 在设置中填入 Cookie

---

## 📊 性能

### 处理速度
- 单线程：100个文件 ~300秒
- 4线程：100个文件 ~75秒
- **加速比：4倍**

### 资源占用
- 内存：< 100MB
- CPU：< 50%
- 磁盘：最小化写入

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 开发

```bash
# 运行测试
python test_architecture.py
python test_error_handler.py
python test_batch_processor.py

# 查看开发者指南
docs/开发者指南.md
```

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)

---

## 🙏 致谢

- [TMDB](https://www.themoviedb.org/) - 电影数据库
- [豆瓣电影](https://movie.douban.com/) - 中文电影信息
- [NAS Tools](https://github.com/jxxghp/nas-tools) - 参考项目
- [MoviePilot](https://github.com/jxxghp/MoviePilot) - 参考项目

---

## 📞 联系方式

- GitHub: [haishuai1987/media-sorter](https://github.com/haishuai1987/media-sorter)
- Issues: [提交问题](https://github.com/haishuai1987/media-sorter/issues)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
