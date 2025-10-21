# Hotfix v1.2.1

## 🐛 修复的问题

### 元数据查询优化功能未生效

**问题描述：**
v1.2.0中实现的TitleParser和QueryStrategy没有被实际调用，导致：
- Release Group标识没有被移除（如CHDWEB、ADWeb等）
- 技术参数没有被移除（如1080p、WEB-DL、x265等）
- 文件名识别不准确

**修复内容：**
1. 在`parse_media_filename`方法开始就调用`TitleParser.parse()`
2. 使用解析后的干净标题进行后续处理
3. 确保Release Group和技术参数被正确移除

**影响：**
- 文件名识别准确率大幅提升
- 标题更加干净和规范
- 查询TMDB时更容易匹配

## 📝 修改文件

- `app.py` - 修改parse_media_filename方法
- `version.txt` - v1.2.0 → v1.2.1

## 🧪 测试验证

修复前：
```
Dealing.with.Mikadono.Sisters.Is.a.Breeze.S01.1080p.HamiVideo.WEB-DL.AAC2.0.H.264-CHDWEB
```

修复后应该识别为：
```
Dealing with Mikadono Sisters Is a Breeze
```

## 🚀 部署

```bash
# GitHub Desktop提交
git add .
git commit -m "hotfix: v1.2.1 - 修复元数据查询优化功能未生效的问题"
git push origin main

# 服务器更新
powershell -ExecutionPolicy Bypass -Command "$SERVER_URL = 'http://192.168.51.105:8090'; $forceBody = '{\"use_proxy\": false, \"auto_restart\": true}'; Invoke-RestMethod -Uri \"$SERVER_URL/api/force-update\" -Method Post -ContentType 'application/json' -Body $forceBody"
```

## ⏱️ 发布时间

2025-10-21 14:00
