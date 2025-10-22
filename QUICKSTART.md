# 快速开始指南

> 5分钟快速上手 Media Renamer

## 📦 安装

### 方式 1: Git 克隆（推荐）
```bash
git clone https://github.com/haishuai1987/media-sorter.git
cd media-sorter
pip install -r requirements.txt
```

### 方式 2: 下载 ZIP
1. 访问 https://github.com/haishuai1987/media-sorter
2. 点击 "Code" → "Download ZIP"
3. 解压到本地目录
4. 运行 `pip install -r requirements.txt`

---

## 🚀 第一次使用

### 1. 测试安装
```bash
python -c "from core.smart_batch_processor import SmartBatchProcessor; print('✓ 安装成功!')"
```

### 2. 处理第一个文件
```python
from core.smart_batch_processor import SmartBatchProcessor

# 创建处理器
processor = SmartBatchProcessor()

# 处理文件
files = ["The.Matrix.1999.1080p.BluRay.x264.mkv"]
result = processor.process_batch(files)

# 查看结果
for r in result['results']:
    if r['success']:
        print(f"✓ {r['original_name']}")
        print(f"  → {r['new_name']}")
```

### 3. 运行测试
```bash
# 测试所有功能
python test_v2.4.0_features.py
```

---

## 💡 常用场景

### 场景 1: 整理电影
```python
from core.smart_batch_processor import SmartBatchProcessor

processor = SmartBatchProcessor()

movies = [
    "The.Matrix.1999.1080p.BluRay.x264.mkv",
    "Inception.2010.1080p.BluRay.x264.mkv"
]

result = processor.process_batch(movies)
```

### 场景 2: 整理剧集
```python
episodes = [
    "Game.of.Thrones.S01E01.1080p.mkv",
    "Game.of.Thrones.S01E02.1080p.mkv"
]

result = processor.process_batch(episodes)
```

### 场景 3: 中文文件
```python
chinese_files = [
    "权力的游戏.第一季.第一集.1080p.mkv",
    "流浪地球.2019.1080p.BluRay.x264.mkv"
]

result = processor.process_batch(chinese_files)
```

---

## ⚙️ 可选配置

### 安装 cn2an（提升中文数字识别）
```bash
pip install cn2an
```

### 配置 API 密钥（提升识别准确性）
```python
processor = SmartBatchProcessor(
    tmdb_api_key='your_tmdb_key',
    douban_cookie='your_douban_cookie'
)
```

---

## 🎯 下一步

- 📖 阅读[完整文档](README.md)
- 🔧 查看[配置说明](docs/使用手册.md)
- 💬 加入[讨论区](https://github.com/haishuai1987/media-sorter/discussions)
- ⭐ 给项目一个 Star

---

## ❓ 遇到问题？

1. 查看[常见问题](docs/常见问题.md)
2. 搜索[Issues](https://github.com/haishuai1987/media-sorter/issues)
3. 提交新的 Issue

---

**祝使用愉快！** 🎉
