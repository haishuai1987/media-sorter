# 贡献指南

感谢你考虑为媒体库文件管理器做出贡献！

## 如何贡献

### 报告Bug

如果你发现了Bug，请创建一个Issue并包含：

1. **问题描述**：清楚地描述问题
2. **复现步骤**：详细的复现步骤
3. **预期行为**：你期望发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - 操作系统和版本
   - Python版本
   - 浏览器版本（如果相关）
6. **错误日志**：相关的错误信息
7. **截图**：如果适用

### 提出新功能

如果你有新功能的想法：

1. 先检查是否已有类似的Issue
2. 创建一个Feature Request
3. 清楚地描述功能和使用场景
4. 说明为什么这个功能有用

### 提交代码

1. **Fork项目**
   ```bash
   # 在GitHub上点击Fork按钮
   ```

2. **克隆你的Fork**
   ```bash
   git clone https://github.com/your-username/media-renamer.git
   cd media-renamer
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行修改**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 更新相关文档

5. **测试你的修改**
   ```bash
   python3 app.py
   # 测试所有相关功能
   ```

6. **提交修改**
   ```bash
   git add .
   git commit -m "描述你的修改"
   ```

7. **推送到你的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建Pull Request**
   - 在GitHub上创建PR
   - 清楚地描述你的修改
   - 引用相关的Issue

## 代码规范

### Python代码

- 使用Python 3.6+兼容的语法
- 遵循PEP 8风格指南
- 使用有意义的变量名
- 添加必要的注释
- 函数应该有文档字符串

### 前端代码

- 使用清晰的HTML结构
- CSS使用有意义的类名
- JavaScript使用ES6+语法
- 添加必要的注释

### 提交信息

使用清晰的提交信息：

```
类型: 简短描述

详细描述（如果需要）

相关Issue: #123
```

类型：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat: 添加SOCKS5代理支持

- 添加代理类型选择
- 更新配置文件格式
- 更新文档

相关Issue: #45
```

## 文档贡献

文档同样重要！

- 修正错别字
- 改进说明
- 添加示例
- 翻译文档

文档位于 `docs/` 目录。

## 测试

在提交PR前，请确保：

1. 代码可以正常运行
2. 没有引入新的Bug
3. 所有功能正常工作
4. 文档已更新

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性的批评
- 关注项目的最佳利益

## 问题？

如果有任何问题，欢迎：

- 创建Issue讨论
- 在PR中提问
- 查看现有的Issue和PR

## 感谢

感谢你的贡献！每一个贡献都让这个项目变得更好。

---

**Happy Coding!** 🎉
