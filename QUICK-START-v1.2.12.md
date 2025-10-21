# v1.2.12 快速开始 🚀

## ⚡ 5 分钟快速部署

### 步骤 1: 运行测试（1 分钟）
```bash
python test_release_groups_v1.2.12.py
```
**预期结果：** 通过率 > 90%

### 步骤 2: 启动服务（1 分钟）
```bash
python app.py
```

### 步骤 3: 访问界面（1 分钟）
```
http://localhost:8090
```
**检查：** 页面底部版本号显示 `v1.2.12`

### 步骤 4: 测试功能（2 分钟）
1. 进入"本地整理"页面
2. 选择包含制作组的文件
3. 点击"开始整理"
4. 验证制作组是否被移除

---

## 📊 新功能一览

### Release Group 识别增强

**之前（v1.2.11）：**
```
支持 13 个制作组
识别率 ~30%
```

**现在（v1.2.12）：**
```
支持 100+ 制作组
识别率 ~95%
```

### 支持的格式

| 格式 | 示例 | 支持 |
|------|------|------|
| 连字符 | `某剧-CHDWEB` | ✅ |
| 点号 | `某剧.CHDWEB.1080p` | ✅ |
| 方括号 | `某剧[CHDBits]` | ✅ |
| 圆括号 | `某剧(CHDWEB)` | ✅ |
| 中文括号 | `某剧【CHDTV】` | ✅ |

---

## 🎯 常见场景

### 场景 1: PT 站点资源
```
输入: 密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB
输出: 密室大逃脱.S07.1080p.WEB-DL.H265.AAC
```

### 场景 2: 动漫资源
```
输入: [LoliHouse] 某动漫 - 01 [WebRip 1080p HEVC-10bit AAC]
输出: 某动漫 - 01 [WebRip 1080p HEVC-10bit AAC]
```

### 场景 3: 多个制作组
```
输入: 某剧[CHDBits][FRDS]
输出: 某剧
```

---

## 🔧 故障排除

### 问题 1: 测试失败
**症状：** 测试通过率 < 90%

**解决：**
```bash
# 1. 检查 Python 版本
python --version  # 需要 3.7+

# 2. 重新运行测试
python test_release_groups_v1.2.12.py

# 3. 查看详细错误
```

### 问题 2: 服务无法启动
**症状：** `python app.py` 报错

**解决：**
```bash
# 1. 检查端口占用
netstat -ano | findstr :8090

# 2. 修改端口
set PORT=8091
python app.py

# 3. 查看日志
type media-renamer.log
```

### 问题 3: 制作组未移除
**症状：** 整理后文件名仍包含制作组

**解决：**
1. 检查制作组是否在支持列表中
2. 查看 [CHANGELOG-v1.2.12.md](CHANGELOG-v1.2.12.md) 的完整列表
3. 如果不在列表中，提交 Issue 请求添加

---

## 📚 更多信息

### 详细文档
- [CHANGELOG-v1.2.12.md](CHANGELOG-v1.2.12.md) - 完整更新日志
- [v1.2.12-SUMMARY.md](v1.2.12-SUMMARY.md) - 实施总结
- [COMMIT-v1.2.12.md](COMMIT-v1.2.12.md) - 提交说明

### 用户指南
- [docs/使用指南.md](docs/使用指南.md) - 使用指南
- [docs/功能说明.md](docs/功能说明.md) - 功能说明
- [docs/常见问题.md](docs/常见问题.md) - 常见问题

### 开发文档
- [PLATFORM-ROADMAP.md](PLATFORM-ROADMAP.md) - 发展路线图
- [ANALYSIS-SUMMARY.md](ANALYSIS-SUMMARY.md) - 分析总结

---

## 🎉 完成！

现在你可以享受更强大的 Release Group 识别功能了！

**下一步：**
- 🔄 v1.3.0 - 识别词系统（下周）
- 🔄 v1.4.0 - 副标题解析（2周后）

**需要帮助？**
- 查看文档
- 提交 Issue
- 加入社区

---

**祝使用愉快！** 🚀
