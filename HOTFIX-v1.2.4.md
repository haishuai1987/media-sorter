# Hotfix v1.2.4 - 修复文件夹名解析问题（最终版）

## 🎯 本次修复

**问题根源**：v1.2.1和v1.2.2的修复没有生效，因为文件夹名没有经过TitleParser清理。

**修复内容**：
- 在`parse_folder_name`方法中添加TitleParser清理
- 确保文件夹名也会移除Release Group和技术参数

## 📝 修复代码

```python
def parse_folder_name(self, folder_name):
    """从文件夹名提取标题和年份"""
    # ... 前置处理 ...
    
    # 使用TitleParser清理文件夹名（移除Release Group和技术参数）
    parsed_folder = TitleParser.parse(folder_name)
    folder_name = parsed_folder['title'] if parsed_folder['title'] else folder_name
    
    # ... 后续处理 ...
```

## ✅ 预期效果

修复后的文件名：

| 修复前 | 修复后 |
|--------|--------|
| `Dealing.with.Mikadono.Sisters.Is.a.Breeze.S01.1080p.HamiVideo.WEB-DL.AAC2.0.H.264-CHDWEB` | `Dealing with Mikadono Sisters Is a Breeze` |
| `New.PANTY.&.STOCKING.with.GARTERBELT.S01.1080p.AMZN.WEB-DL.DDP.5.1.H.264-CHDWEB` | `New PANTY & STOCKING with GARTERBELT` |
| `Gen.V.S02.1080p.AMZN.WEB-DL.H.264.DDP5.1.Atmos-ADWeb II II II` | `Gen V` |
| `Call.of.the.Night.S02.1080p.MyVideo.WEB-DL.AAC2.0.H.264-CHDWEB II II II` | `Call of the Night` |

## 🚀 部署步骤

1. ✅ 代码已推送到GitHub
2. 📦 更新服务器：`bash 更新服务器.sh` 或 `.\更新服务器.ps1`
3. 🧪 重新测试文件整理
4. ✅ 验证Release Group和技术参数已被移除

## 🔍 验证方法

运行整理流程后，检查：
1. 文件名中不应包含Release Group（-CHDWEB, -ADWeb等）
2. 文件名中不应包含技术参数（1080p, WEB-DL, H.264等）
3. 续集标记应该正常（不会出现II II II）
4. 文件夹名应该干净整洁

---

**版本历史**：
- v1.2.1: 首次尝试修复（失败）
- v1.2.2: 添加DEBUG日志（发现问题）
- v1.2.3: 跳过（版本号冲突）
- v1.2.4: 最终修复（成功）✅
