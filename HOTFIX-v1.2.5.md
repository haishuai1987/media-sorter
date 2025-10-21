# Hotfix v1.2.5 - 修复语法错误

## 🐛 紧急修复

**问题**：v1.2.4推送后服务器无法启动，报语法错误：
```
SyntaxError: unterminated string literal (detected at line 3967)
```

**原因**：Kiro IDE的Autofix在格式化时将正则表达式字符串截断了：
```python
# 错误的代码（被截断）
name = re.sub(r'[-\[\(][A-Z0-9]+[\]\)]
# 缺少结束引号和参数！

# 正确的代码
name = re.sub(r'[-\[\(][A-Z0-9]+[\]\)]$', '', name)
```

## ✅ 修复内容

- 修复第3967行的正则表达式字符串
- 添加缺失的结束引号和参数

## 🚀 部署

立即推送并更新服务器！
