# Media Renamer v2.5.0 快速启动指南

## 🚀 5分钟快速上手

### 1. 安装依赖

```bash
pip install flask-cors
```

### 2. 启动 Web UI

#### 方式一：简化版（推荐新手）
```bash
python app_v2_simple.py
```
- 访问: http://localhost:5000
- 特点: 轻量级，快速启动
- 适用: 测试和学习

#### 方式二：完整版（推荐生产）
```bash
python app_v2.py
```
- 访问: http://localhost:8090
- 特点: 完整功能，集成所有模块
- 适用: 实际使用

### 3. 使用界面

#### 📦 批量处理
1. 点击顶部"批量处理"标签
2. 在文本框中输入文件列表（每行一个）
   ```
   The.Matrix.1999.1080p.BluRay.x264.mkv
   Inception.2010.1080p.BluRay.x264.mkv
   权力的游戏.第一季.第一集.1080p.mkv
   ```
3. 选择模板（电影/电视剧）
4. 设置优先级（可选）
5. 点击"开始处理"
6. 查看实时进度和结果

#### 🔍 文件识别
1. 点击"文件识别"标签
2. 输入文件名
3. 点击"识别"按钮
4. 查看识别结果（JSON 格式）

#### 📝 模板管理
1. 点击"模板管理"标签
2. 查看所有可用模板
3. 了解模板格式

#### 📚 识别词管理
1. 点击"识别词"标签
2. 选择类型（屏蔽词/替换词）
3. 填写内容
4. 点击"添加"
5. 管理已有识别词（启用/禁用/删除）

#### 📊 统计信息
1. 点击"统计信息"标签
2. 查看处理统计
3. 监控队列状态
4. 查看速率限制信息

## 🎯 常见使用场景

### 场景1：批量重命名电影
```
输入文件:
The.Matrix.1999.1080p.BluRay.x264.mkv
Inception.2010.1080p.BluRay.x264.mkv

选择模板: movie_default

输出结果:
The Matrix (1999).mkv
Inception (2010).mkv
```

### 场景2：批量重命名电视剧
```
输入文件:
Game.of.Thrones.S01E01.1080p.mkv
Game.of.Thrones.S01E02.1080p.mkv

选择模板: tv_default

输出结果:
Game of Thrones S01E01.mkv
Game of Thrones S01E02.mkv
```

### 场景3：测试单个文件
```
输入: The.Matrix.1999.1080p.BluRay.x264.mkv

识别结果:
{
  "title": "The Matrix",
  "year": 1999,
  "resolution": "1080p",
  "source": "BluRay",
  "codec": "x264",
  "is_tv": false
}
```

### 场景4：添加屏蔽词
```
类型: 屏蔽词
内容: RARBG
描述: 屏蔽发布组标识

效果: 文件名中的 "RARBG" 将被自动移除
```

### 场景5：添加替换词
```
类型: 替换词
原文本: BluRay
新文本: Blu-ray
描述: 统一蓝光格式

效果: "BluRay" 将被替换为 "Blu-ray"
```

## 🔧 故障排除

### 问题1：端口被占用
```
错误: Address already in use

解决方案:
1. 使用不同端口的版本
   - app_v2_simple.py (端口 5000)
   - app_v2.py (端口 8090)

2. 或者杀掉占用端口的进程
   Windows: taskkill /F /IM python.exe
   Linux/Mac: killall python
```

### 问题2：模块未找到
```
错误: ModuleNotFoundError: No module named 'flask_cors'

解决方案:
pip install flask-cors
```

### 问题3：无法访问界面
```
错误: 浏览器显示"无法访问此网站"

解决方案:
1. 确认服务器已启动
2. 检查防火墙设置
3. 尝试使用 127.0.0.1 而不是 localhost
```

### 问题4：API 返回 404
```
错误: 404 Not Found

解决方案:
1. 确认使用正确的 URL
2. 检查服务器日志
3. 重启服务器
```

## 📱 移动端访问

### 局域网访问
1. 确认电脑和手机在同一网络
2. 查看电脑 IP 地址
   ```bash
   Windows: ipconfig
   Linux/Mac: ifconfig
   ```
3. 在手机浏览器访问
   ```
   http://[电脑IP]:5000
   或
   http://[电脑IP]:8090
   ```

### 示例
```
电脑 IP: 192.168.1.100
访问地址: http://192.168.1.100:5000
```

## 🎨 界面快捷键

- `Tab`: 切换输入框
- `Enter`: 提交表单（在输入框中）
- `Esc`: 关闭弹窗（如果有）

## 💡 使用技巧

### 技巧1：批量输入
- 从文件管理器复制文件名
- 直接粘贴到文本框
- 支持多行输入

### 技巧2：模板选择
- 电影使用 movie_* 模板
- 电视剧使用 tv_* 模板
- simple 版本更简洁
- detailed 版本更详细

### 技巧3：优先级设置
- 普通(5): 日常使用
- 高(7): 重要文件
- 关键(10): 紧急处理
- 低(3): 后台处理

### 技巧4：队列管理
- 开启: 使用队列系统，支持并发
- 关闭: 直接处理，适合小批量

### 技巧5：识别词管理
- 屏蔽词: 移除不需要的内容
- 替换词: 统一格式和命名
- 可随时启用/禁用

## 📚 更多资源

- **完整文档**: [docs/使用手册.md](docs/使用手册.md)
- **API 文档**: [docs/API文档.md](docs/API文档.md)
- **更新日志**: [CHANGELOG-v2.5.0.md](CHANGELOG-v2.5.0.md)
- **开发指南**: [docs/开发者指南.md](docs/开发者指南.md)

## 🆘 获取帮助

遇到问题？
1. 查看故障排除部分
2. 阅读完整文档
3. 提交 Issue
4. 联系开发者

## 🎉 开始使用

现在你已经准备好了！启动服务器，打开浏览器，开始享受现代化的媒体文件管理体验吧！

```bash
python app_v2_simple.py
```

然后访问: http://localhost:5000

祝使用愉快！🚀
