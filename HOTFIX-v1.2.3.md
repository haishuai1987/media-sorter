# Hotfix v1.2.3 - 修复文件夹名解析问题

## 🐛 问题根源

v1.2.1和v1.2.2的修复没有生效，因为：

1. **TitleParser被调用了，但结果被覆盖**
2. **文件夹名没有经过TitleParser清理**
3. **folder_title优先级高于TitleParser结果**

导致文件夹名如：
```
Dealing.with.Mikadono.Sisters.Is.a.Breeze.S01.1080p.HamiVideo.WEB-DL.AAC2.0.H.264-CHDWEB
```

被直接当作标题使用，包含了所有Release Group和技术参数！

## ✅ 修复方案

在`parse_folder_name`方法中添加TitleParser清理：

```python
# 使用TitleParser清理文件夹名（移除Release Group和技术参数）
parsed_folder = TitleParser.parse(folder_name)
folder_name = parsed_folder['title'] if parsed_folder['title'] else folder_name
```

## 📝 预期效果

修复后：
- ❌ `Dealing.with.Mikadono.Sisters.Is.a.Breeze.S01.1080p.HamiVideo.WEB-DL.AAC2.0.H.264-CHDWEB`
- ✅ `Dealing with Mikadono Sisters Is a Breeze`

- ❌ `Gen.V.S02.1080p.AMZN.WEB-DL.H.264.DDP5.1.Atmos-ADWeb II II II`
- ✅ `Gen V`

## 🚀 部署步骤

1. 推送到GitHub
2. 更新服务器到v1.2.3
3. 重新测试文件重命名
4. 验证Release Group和技术参数已被移除
