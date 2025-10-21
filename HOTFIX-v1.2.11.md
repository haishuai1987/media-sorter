# 🔧 HOTFIX v1.2.11 - 标题清理修复

## 📋 问题描述

TMDB返回的标题包含英文部分，导致重命名后的文件名不纯净：

**问题示例：**
```
原始文件：密室大逃脱大神版.第七季.Great.Escape.Super.S07E11.2019.mp4
TMDB返回：密室大逃脱 Great Escape
重命名后：密室大逃脱 Great Escape - S07E11 - 第 11 集.mp4  ❌ 包含英文
```

**期望结果：**
```
重命名后：密室大逃脱大神版 - S07E11 - 第 11 集.mp4  ✅ 纯中文
```

## ✅ 修复内容

### 1. 新增 `extract_chinese_title()` 方法

```python
@staticmethod
def extract_chinese_title(title):
    """从混合标题中提取纯中文标题
    
    - "密室大逃脱 Great Escape" → "密室大逃脱"
    - "密室大逃脱大神版 Great Escape Super" → "密室大逃脱大神版"
    - "花牌情缘：巡 Chihayafuru Full Circle" → "花牌情缘：巡"
    """
```

### 2. 修改查询方法

- `TMDBHelper.search_tv()` - 自动清理标题
- `TMDBHelper.search_movie()` - 自动清理标题

### 3. 测试验证

✅ 所有测试用例通过：
```
✓ '密室大逃脱 Great Escape' → '密室大逃脱'
✓ '密室大逃脱大神版 Great Escape Super' → '密室大逃脱大神版'
✓ '密室大逃脱大神版.第七季.Great.Escape.Super' → '密室大逃脱大神版'
✓ 'Great Escape' → 'Great Escape'
✓ '花牌情缘：巡 Chihayafuru Full Circle' → '花牌情缘：巡'
✓ '间谍过家家 Spy x Family' → '间谍过家家'
✓ 'Black Rabbit' → 'Black Rabbit'
✓ '奔跑吧 Keep Running' → '奔跑吧'
```

## 🎯 影响范围

- 所有通过TMDB查询的标题都会被自动清理
- 只保留中文部分，移除英文副标题
- 保留版本标识（如"大神版"）
- 不影响纯英文标题

## 📦 部署步骤

### 1. 推送到GitHub
```bash
双击运行：PUSH-NOW-v1.2.11.bat
```

### 2. 更新服务器
```bash
ssh root@8.134.215.137
cd /root/media-sorter
git pull origin main
pkill -f "python.*app.py"
nohup python3 app.py > app.log 2>&1 &
```

或者直接运行：
```powershell
双击运行：更新服务器.ps1
```

## 📝 版本信息

- **版本号**: v1.2.11
- **修复类型**: 标题清理
- **优先级**: 中等
- **影响**: 所有TMDB查询结果
