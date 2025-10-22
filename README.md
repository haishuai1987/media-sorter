# 媒体库文件管理器 (Media Renamer)

> 🎬 智能媒体文件整理工具 - 自动识别、智能重命名、批量处理、中文标题解析

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.4.0-orange.svg)](CHANGELOG-v2.4.0.md)
[![Stars](https://img.shields.io/github/stars/haishuai1987/media-sorter?style=social)](https://github.com/haishuai1987/media-sorter)

---

## 📖 目录

- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [版本历史](#-版本历史)
- [使用指南](#-使用指南)
- [高级功能](#-高级功能)
- [配置说明](#-配置说明)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)

---

## ✨ 核心特性

### 🎯 v2.4.0 最新功能

#### 🔢 中文数字转换
- 自动转换中文数字为阿拉伯数字
- 支持内置转换器（无依赖，500k+ 次/秒）
- 可选 cn2an 库（更高准确性）
- 专门优化季集信息识别

```python
# 自动转换
"权力的游戏.第一季.第五集.mkv" → "权力的游戏 S01E05"
"流浪地球.第二部.2023.mkv" → "流浪地球 第2部 (2023)"
```

#### 🚀 智能队列管理
- 10级优先级调度
- 多线程并发处理
- 自动重试机制
- 超时保护

#### ⚡ 速率限制
- 令牌桶算法
- 滑动窗口算法
- 防止 API 限流
- 保护外部服务

### 🎬 智能识别

#### 高级识别器
- 自动识别电影/剧集信息
- 提取年份、季集、分辨率
- 识别视频编码、音频编码
- 识别来源（BluRay、WEB-DL等）
- 质量评分系统

#### 中文标题解析
- 豆瓣 + TMDB 双源查询
- 自动翻译英文标题为中文
- 智能匹配最佳结果
- 支持代理访问
- 缓存机制

### 📝 灵活的模板系统

#### 内置模板
- **电影模板**: `movie_default`, `movie_simple`, `movie_detailed`
- **电视剧模板**: `tv_default`, `tv_simple`, `tv_detailed`
- **NAS模板**: `nas_movie`, `nas_tv`
- **Plex模板**: `plex_movie`, `plex_tv`

#### 自定义模板
```python
# 自定义命名格式
template = "{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d}.{ext}"
```

### 🎨 事件驱动架构

- 解耦的模块设计
- 实时事件通知
- 可扩展的插件系统
- 详细的日志记录

### 🛠️ 实用工具

#### 环境自动检测
- 自动识别本地/云/Docker环境
- 根据环境自动调整配置
- 支持环境变量覆盖

#### 网络重试机制
- 自动重试网络操作（3次）
- 指数退避策略
- 超时控制
- NAS/网络文件系统优化

#### 自定义识别词
- 屏蔽词（移除不需要的内容）
- 替换词（修正标题）
- 正则表达式支持
- 持久化配置

---

## 🚀 快速开始

### 安装

#### 方式 1: 克隆仓库（推荐）
```bash
git clone https://github.com/haishuai1987/media-sorter.git
cd media-sorter
pip install -r requirements.txt
```

#### 方式 2: 直接下载
```bash
# 下载最新版本
wget https://github.com/haishuai1987/media-sorter/archive/refs/heads/main.zip
unzip main.zip
cd media-sorter-main
pip install -r requirements.txt
```

### 基本使用

#### 1. Python API
```python
from core.smart_batch_processor import SmartBatchProcessor

# 创建处理器
processor = SmartBatchProcessor()

# 批量处理文件
files = [
    "The.Matrix.1999.1080p.BluRay.x264.mkv",
    "权力的游戏.第一季.第一集.1080p.mkv",
    "流浪地球.2019.1080p.BluRay.x264.mkv"
]

result = processor.process_batch(files)

# 查看结果
for r in result['results']:
    print(f"{r['original_name']} → {r['new_name']}")
```

#### 2. 命令行工具（即将推出）
```bash
# 处理单个文件
media-renamer process "movie.mkv"

# 批量处理目录
media-renamer batch /path/to/movies

# 交互式配置
media-renamer config
```

#### 3. Web 界面
```bash
# 启动 Web 服务
python app.py

# 访问 http://localhost:8090
```

---

## 📚 版本历史

### v2.4.0 - 功能增强 (2025-01-XX)
- ✅ 中文数字转换
- ✅ 增强识别功能
- ✅ 性能优化

### v2.3.0 - 性能优化 (2025-01-XX)
- ✅ 智能队列管理
- ✅ 速率限制器
- ✅ 并发处理

### v2.2.0 - 基础增强 (2025-01-XX)
- ✅ 环境自动检测
- ✅ 网络重试机制
- ✅ 自定义识别词

### v2.1.0 - 核心功能 (2025-01-XX)
- ✅ 高级识别器
- ✅ 中文标题解析器
- ✅ 模板引擎
- ✅ 事件系统

[查看完整更新日志](CHANGELOG-v2.4.0.md)

---

## 📖 使用指南

### 基础功能

#### 识别文件
```python
from core.chinese_title_resolver import IntegratedRecognizer

recognizer = IntegratedRecognizer()

# 识别并获取中文标题
info = recognizer.recognize_with_chinese_title(
    "The.Matrix.1999.1080p.BluRay.x264.mkv"
)

print(f"标题: {info['title']}")
print(f"年份: {info['year']}")
print(f"分辨率: {info['resolution']}")
```

#### 批量处理
```python
from core.smart_batch_processor import SmartBatchProcessor

processor = SmartBatchProcessor()

# 进度回调
def progress_callback(progress, current_file, result):
    print(f"进度: {progress*100:.0f}% - {result['message']}")

# 批量处理
result = processor.process_batch(
    files,
    progress_callback=progress_callback
)
```

#### 使用模板
```python
from core.template_engine import get_template_engine

engine = get_template_engine()

# 渲染模板
new_name = engine.render('movie_default', {
    'title': '黑客帝国',
    'year': 1999,
    'resolution': '1080p',
    'source': 'BluRay',
    'ext': 'mkv'
})
```

---

## 🔥 高级功能

### 队列管理

```python
from core.smart_batch_processor import SmartBatchProcessor
from core.queue_manager import Priority

# 启用队列管理
processor = SmartBatchProcessor(
    use_queue=True,
    max_workers=4
)

# 使用优先级
result = processor.process_batch_with_queue(
    files,
    priority=Priority.HIGH
)
```

### 速率限制

```python
# 启用速率限制
processor = SmartBatchProcessor(
    use_rate_limit=True,
    rate_limit=10  # 10 请求/秒
)

result = processor.process_batch(files)
```

### 自定义识别词

```python
from core.custom_words import get_custom_words

cw = get_custom_words()

# 添加屏蔽词
cw.add_word({
    'type': 'block',
    'pattern': 'RARBG',
    'description': '屏蔽 RARBG 标识',
    'enabled': True
})

# 应用到标题
cleaned = cw.apply("The.Matrix.1999.RARBG.mkv")
```

### 环境检测

```python
from core.environment import get_environment

env = get_environment()

print(f"环境类型: {env.type}")  # local, cloud, docker
print(f"配置: {env.config}")
```

---

## ⚙️ 配置说明

### 环境变量

```bash
# 部署环境
export DEPLOY_ENV=cloud  # local, cloud, docker

# 服务配置
export HOST=0.0.0.0
export PORT=8090

# API 密钥
export TMDB_API_KEY=your_key
export DOUBAN_COOKIE=your_cookie
```

### 配置文件

配置文件位置: `~/.media-renamer/`

- `config.json` - 主配置文件
- `custom_words.json` - 自定义识别词
- `templates.json` - 自定义模板

---

## 🎯 使用场景

### 场景 1: 整理电影库
```python
processor = SmartBatchProcessor()

movies = [
    "The.Matrix.1999.1080p.BluRay.x264.mkv",
    "Inception.2010.1080p.BluRay.x264.mkv",
    "Interstellar.2014.1080p.BluRay.x264.mkv"
]

result = processor.process_batch(movies, template_name='movie_detailed')

# 结果:
# 黑客帝国 (1999)/黑客帝国 (1999) [1080p x264 BluRay].mkv
# 盗梦空间 (2010)/盗梦空间 (2010) [1080p x264 BluRay].mkv
# 星际穿越 (2014)/星际穿越 (2014) [1080p x264 BluRay].mkv
```

### 场景 2: 整理剧集
```python
episodes = [
    "Game.of.Thrones.S01E01.1080p.BluRay.x264.mkv",
    "Game.of.Thrones.S01E02.1080p.BluRay.x264.mkv",
    "Game.of.Thrones.S01E03.1080p.BluRay.x264.mkv"
]

result = processor.process_batch(episodes)

# 结果:
# 权力的游戏/Season 01/权力的游戏 - S01E01 [1080p-BluRay].mkv
# 权力的游戏/Season 01/权力的游戏 - S01E02 [1080p-BluRay].mkv
# 权力的游戏/Season 01/权力的游戏 - S01E03 [1080p-BluRay].mkv
```

### 场景 3: 大批量处理
```python
# 启用队列和速率限制
processor = SmartBatchProcessor(
    use_queue=True,
    use_rate_limit=True,
    max_workers=8,
    rate_limit=10
)

# 处理大量文件
large_batch = [...]  # 1000+ 文件

result = processor.process_batch_with_queue(large_batch)
```

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 识别准确性 | 90%+ |
| 处理速度 | 500+ 文件/秒 |
| 成功率 | 95%+ |
| 中文数字转换 | 500k+ 次/秒 |
| 并发处理 | 支持 |
| 内存占用 | < 100MB |

---

## ❓ 常见问题

### Q: 如何提高识别准确性？
A: 
1. 安装 cn2an: `pip install cn2an`
2. 配置 TMDB API Key
3. 配置豆瓣 Cookie
4. 使用自定义识别词

### Q: 如何处理大批量文件？
A: 启用队列管理和速率限制
```python
processor = SmartBatchProcessor(
    use_queue=True,
    use_rate_limit=True,
    max_workers=8
)
```

### Q: 如何自定义命名格式？
A: 使用模板引擎
```python
engine.add_template('my_template', 
    "{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d}.{ext}"
)
```

[查看更多问题](docs/常见问题.md)

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发环境设置
```bash
git clone https://github.com/haishuai1987/media-sorter.git
cd media-sorter
pip install -r requirements.txt

# 运行测试
python -m pytest

# 代码格式化
black .
```

### 提交规范
- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 🙏 致谢

- [TMDB](https://www.themoviedb.org/) - 电影数据库
- [豆瓣](https://movie.douban.com/) - 中文电影信息
- [cn2an](https://github.com/Ailln/cn2an) - 中文数字转换
- 所有贡献者

---

## 📞 联系方式

- GitHub: [@haishuai1987](https://github.com/haishuai1987)
- Issues: [提交问题](https://github.com/haishuai1987/media-sorter/issues)
- Discussions: [讨论区](https://github.com/haishuai1987/media-sorter/discussions)

---

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=haishuai1987/media-sorter&type=Date)](https://star-history.com/#haishuai1987/media-sorter&Date)

---

**Made with ❤️ by haishuai1987**
