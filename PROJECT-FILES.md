# 项目文件清单

## 核心代码

### 主程序
- `app.py` - 主程序入口
- `error_handler.py` - 错误处理框架 (v1.7.0)
- `batch_processor.py` - 批量处理器 (v1.9.0)
- `error_handler_integration.py` - 错误处理集成示例

### 核心模块 (v2.0.0)
- `core/__init__.py` - 核心模块初始化
- `core/config.py` - 配置管理器
- `core/logger.py` - 日志系统
- `core/utils.py` - 工具函数

### 插件系统 (v2.0.0)
- `plugins/__init__.py` - 插件系统初始化
- `plugins/base.py` - 插件基类
- `plugins/loader.py` - 插件加载器
- `plugins/example_plugin.py` - 示例插件

### Web资源
- `public/index.html` - 主页面
- `public/style.css` - 样式表
- `public/toast.js` - Toast通知系统 (v1.8.0)
- `public/error-stats.js` - 错误统计面板 (v1.8.0)
- `index.html` - 备用主页

## 测试文件

- `test_error_handler.py` - 错误处理测试
- `test_batch_processor.py` - 批量处理测试
- `test_architecture.py` - 架构测试
- `test_title_parser.py` - 标题解析测试
- `test_title_cleaning.py` - 标题清理测试
- `test_custom_words.py` - 自定义词测试
- `test_subtitle_parser.py` - 副标题解析测试
- `test_release_groups_v1.2.12.py` - Release Group 测试
- `test-web-ui.html` - Web界面测试页面

## 文档

### 项目文档
- `README.md` - 项目说明
- `LICENSE` - MIT 许可证
- `PROJECT-STRUCTURE.md` - 项目结构说明
- `PROJECT-FILES.md` - 项目文件清单（本文件）
- `CLEANUP-SUMMARY.md` - 清理总结

### 更新日志
- `CHANGELOG-v1.7.0.md` - 错误处理增强
- `CHANGELOG-v1.8.0.md` - Web界面优化
- `CHANGELOG-v1.9.0.md` - 批量操作增强
- `CHANGELOG-v2.0.0.md` - 架构重构

### 快速参考
- `ERROR-HANDLING-QUICK-REF.md` - 错误处理快速参考

### 用户文档 (docs/)
- `使用指南.md` - 基础使用指南
- `部署指南.md` - 部署说明
- `功能说明.md` - 功能详细说明
- `常见问题.md` - FAQ
- `快速开始.md` - 快速入门
- `快速开始-使用Cookie.md` - Cookie配置指南

### 功能文档 (docs/)
- `分类功能说明.md` - 分类功能
- `分类规则说明.md` - 分类规则
- `媒体库结构说明.md` - 媒体库结构
- `配置迁移指南.md` - 配置迁移
- `元数据查询优化说明.md` - 元数据优化
- `端口配置说明.md` - 端口配置
- `更新日志.md` - 完整更新日志

### 技术文档 (docs/)
- `API文档.md` - API接口文档
- `错误处理说明.md` - 错误处理 (v1.7.0)
- `Web界面优化说明.md` - Web界面 (v1.8.0)
- `批量操作说明.md` - 批量操作 (v1.9.0)
- `开发者指南.md` - 开发者指南 (v2.0.0)

### 部署文档 (docs/)
- `云服务器部署指南.md` - 云服务器部署
- `一键部署脚本使用说明.md` - 一键部署

## 配置文件

- `version.txt` - 版本号 (v2.0.0)
- `title_mapping.json` - 标题映射配置
- `.gitignore` - Git忽略文件
- `install.sh` - 安装脚本

## 参考代码 (reference/)

### MoviePilot
- `reference/moviepilot/MoviePilot-2/` - MoviePilot 参考代码

### NAS Tools
- `reference/nas-tools/` - NAS Tools 参考代码
- `reference/nas-tools-master/` - NAS Tools Master 参考代码

## 文件统计

### 代码文件
- Python 文件：~15 个
- JavaScript 文件：2 个
- HTML 文件：3 个
- CSS 文件：1 个

### 文档文件
- Markdown 文件：~30 个
- 更新日志：4 个
- 用户文档：~20 个

### 测试文件
- 测试文件：9 个
- 测试覆盖：核心功能 100%

## 项目规模

- 总代码行数：~5,000 行
- 核心代码：~2,500 行
- 测试代码：~1,500 行
- 文档：~1,000 行

## 版本历史

- v1.7.0 - 错误处理增强
- v1.8.0 - Web界面优化
- v1.9.0 - 批量操作增强
- v2.0.0 - 架构重构（当前版本）

---

**最后更新**: 2025-01-XX  
**当前版本**: v2.0.0  
**文件总数**: ~80 个
