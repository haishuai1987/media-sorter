# 🚀 快速启动指南

## v1.2.0 新功能体验

### 1️⃣ 启动服务

```bash
python app.py
```

### 2️⃣ 访问Web界面

打开浏览器访问：`http://localhost:8090`

### 3️⃣ 体验实时日志推送

1. 在Web界面选择文件夹
2. 点击"扫描文件"
3. 点击"智能重命名"
4. **查看实时日志** - 在页面下方会出现实时日志查看器

### 4️⃣ 测试元数据查询优化

```bash
# 运行测试脚本
python test_title_parser.py
```

**测试内容：**
- TitleParser：文件名解析
- TitleMapper：标题映射查询
- QueryStrategy：多策略查询（需要TMDB API Key）

### 5️⃣ 自定义标题映射

编辑 `title_mapping.json` 添加你的常用剧集：

```json
{
  "mappings": {
    "你的剧集英文名": {
      "tmdb_id": TMDB_ID,
      "chinese_title": "中文名",
      "type": "tv"
    }
  }
}
```

保存后自动生效，无需重启！

## 📊 功能对比

### 实时日志推送

**优化前：**
- ❌ 无法看到处理进度
- ❌ 需要SSH查看日志
- ❌ 不知道处理到哪一步

**优化后：**
- ✅ 实时显示处理日志
- ✅ 进度条显示
- ✅ 彩色日志级别
- ✅ 自动滚动

### 元数据查询

**优化前：**
```
文件名: The.Mandalorian.S02E01.2160p.WEB-DL.x265-ADWeb.mkv
识别: The Mandalorian S02E01 2160p WEB-DL x265-ADWeb ❌
```

**优化后：**
```
文件名: The.Mandalorian.S02E01.2160p.WEB-DL.x265-ADWeb.mkv
解析: The Mandalorian
查询: 标题映射表
识别: 曼达洛人 - S02E01 ✅
```

## 🎯 推荐配置

### 1. 添加常用剧集到映射表

在 `title_mapping.json` 中添加你经常下载的剧集。

### 2. 配置TMDB API Key

在Web界面的"设置"中配置TMDB API Key。

### 3. 启用查询日志（可选）

如需调试，在 `app.py` 中修改：
```python
query_logger = QueryLogger(enable_file_log=True)
```

## 📚 更多文档

- [元数据查询优化说明](docs/元数据查询优化说明.md)
- [v1.2.0功能更新说明](docs/v1.2.0功能更新说明.md)
- [使用指南](docs/使用指南.md)

## 🐛 遇到问题？

查看 [常见问题](docs/常见问题.md) 或提交Issue。

---

**享受新功能！** 🎉
