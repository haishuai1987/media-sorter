# 项目结构说明

## 目录结构

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
│   ├── 使用指南.md
│   ├── 部署指南.md
│   ├── 功能说明.md
│   ├── 常见问题.md
│   ├── 错误处理说明.md    # v1.7.0
│   ├── Web界面优化说明.md  # v1.8.0
│   ├── 批量操作说明.md     # v1.9.0
│   └── 开发者指南.md       # v2.0.0
├── app.py                   # 主程序
├── error_handler.py         # 错误处理 (v1.7.0)
├── batch_processor.py       # 批量处理 (v1.9.0)
├── test_error_handler.py    # 错误处理测试
├── test_batch_processor.py  # 批量处理测试
├── test_architecture.py     # 架构测试
├── version.txt              # 版本号
├── README.md                # 项目说明
├── LICENSE                  # 许可证
└── .gitignore              # Git忽略文件

```

## 核心功能

### v1.7.0 - 错误处理增强
- 统一错误处理框架
- 自动重试机制
- 友好错误消息

### v1.8.0 - Web界面优化
- Toast通知系统
- 错误统计面板
- 操作历史记录

### v1.9.0 - 批量操作增强
- 并发处理（4倍加速）
- 进度追踪
- 断点续传
- 批量回滚

### v2.0.0 - 架构重构
- 模块化设计
- 插件系统
- API标准化
- 配置管理

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python app.py

# 运行测试
python test_architecture.py
```

## 文档

- [使用指南](docs/使用指南.md)
- [部署指南](docs/部署指南.md)
- [开发者指南](docs/开发者指南.md)
- [更新日志](CHANGELOG-v2.0.0.md)
