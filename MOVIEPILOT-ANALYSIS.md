# MoviePilot 代码分析与借鉴

## 📚 核心架构

### 1. 元数据识别 (`app/core/metainfo.py`)

**关键特点：**
- 使用 `MetaInfo()` 函数作为入口
- 自动判断是动漫还是普通视频
- 支持从文件名和路径中提取元数据
- 支持自定义识别词

**核心流程：**
```python
def MetaInfo(title, subtitle=None, custom_words=None):
    # 1. 预处理标题（使用 WordsMatcher）
    title, apply_words = WordsMatcher().prepare(title, custom_words)
    
    # 2. 提取媒体信息（TMDB ID、季集信息等）
    title, metainfo = find_metainfo(title)
    
    # 3. 判断是否为文件
    isfile = Path(title).suffix.lower() in settings.RMT_MEDIAEXT
    
    # 4. 选择合适的解析器
    meta = MetaAnime(title) if is_anime(title) else MetaVideo(title)
    
    # 5. 应用提取的元数据
    meta.tmdbid = metainfo.get('tmdbid')
    meta.begin_season = metainfo.get('begin_season')
    # ...
    
    return meta
```

**可借鉴的点：**
1. ✅ **分离动漫和普通视频的处理逻辑**
2. ✅ **支持从标题中提取 TMDB ID**（格式：`{[tmdbid=xxx]}`）
3. ✅ **使用 WordsMatcher 预处理标题**
4. ✅ **支持路径级别的元数据合并**

---

### 2. 标题预处理 (`WordsMatcher`)

**功能：**
- 移除 Release Group（如 CHDWEB, ADWeb）
- 移除技术参数（如 1080p, H.264）
- 移除来源标识（如 WEB-DL, BluRay）
- 应用自定义识别词

**我们当前的问题：**
- ❌ 没有系统化的标题清理
- ❌ 只是简单地提取中文部分
- ❌ 没有处理 Release Group

**改进方案：**
```python
class TitleCleaner:
    """标题清理器"""
    
    # Release Group 列表
    RELEASE_GROUPS = [
        'CHDWEB', 'ADWeb', 'HHWEB', 'DBTV', 'NGB', 
        'FRDS', 'mUHD', 'AilMWeb', 'UBWEB'
    ]
    
    # 技术参数
    TECH_PARAMS = [
        '2160p', '1080p', '720p', '4K',
        'H.264', 'H.265', 'x264', 'x265',
        'WEB-DL', 'BluRay', 'WEBRip', 'HDRip',
        'DDP', 'AAC', 'Atmos', 'DDP5.1'
    ]
    
    def clean(self, title):
        # 1. 移除 Release Group
        for group in self.RELEASE_GROUPS:
            title = re.sub(rf'-{group}$', '', title, flags=re.IGNORECASE)
        
        # 2. 移除技术参数
        for param in self.TECH_PARAMS:
            title = re.sub(rf'\.{param}\.', '.', title, flags=re.IGNORECASE)
        
        # 3. 提取中文标题
        return self.extract_chinese(title)
```

---

### 3. 元数据提取 (`find_metainfo`)

**支持的格式：**
```python
# 1. MoviePilot 自定义格式
{[tmdbid=12345;type=tv;s=1;e=1-10]}

# 2. Emby 格式
[tmdbid=12345]
[tmdbid-12345]
[tmdb=12345]
[tmdb-12345]

# 3. 花括号格式
{tmdbid=12345}
{tmdbid-12345}
{tmdb=12345}
{tmdb-12345}
```

**我们可以借鉴：**
```python
def extract_tmdb_id(title):
    """从标题中提取 TMDB ID"""
    patterns = [
        r'\[tmdbid[=\-](\d+)\]',
        r'\[tmdb[=\-](\d+)\]',
        r'\{tmdbid[=\-](\d+)\}',
        r'\{tmdb[=\-](\d+)\}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1), re.sub(pattern, '', title).strip()
    
    return None, title
```

---

### 4. 集数格式化 (`FormatParser`)

**功能：**
- 支持集数偏移（如 `EP+10`, `EP*2`）
- 支持集数范围（如 `1-10`）
- 支持自定义集数定位格式

**示例：**
```python
parser = FormatParser(
    eformat="S{season:02d}E{ep:02d}",  # 格式
    details="1-10",                     # 集数范围
    offset="EP+10",                     # 偏移量
    key="ep"                            # 关键字
)

# 解析文件名
start_ep, end_ep, part = parser.split_episode("S01E05.mkv", file_meta)
# 返回: (15, None, None)  # 5 + 10 = 15
```

**我们可以借鉴：**
- 支持更灵活的集数处理
- 支持集数偏移（处理特殊情况）

---

## 🎯 对我们项目的改进建议

### 优先级 1: 标题清理（立即实施）

**当前问题：**
```python
# TMDB 返回: "密室大逃脱 Great Escape"
# 我们的处理: 简单提取中文
# 结果: "密室大逃脱"  ✅ 正确

# TMDB 返回: "密室大逃脱大神版.第七季.Great.Escape.Super"
# 我们的处理: 提取中文
# 结果: "密室大逃脱大神版 第七季"  ❌ 应该是 "密室大逃脱大神版"
```

**改进方案：**
```python
def extract_chinese_title(title):
    """借鉴 MoviePilot 的方法"""
    # 1. 移除 Release Group
    title = remove_release_group(title)
    
    # 2. 移除技术参数
    title = remove_tech_params(title)
    
    # 3. 提取中文部分
    chinese_parts = []
    for part in title.split():
        if any('\u4e00' <= c <= '\u9fff' for c in part):
            chinese_parts.append(part)
    
    result = ' '.join(chinese_parts)
    
    # 4. 移除冗余信息（但保留版本标识）
    result = re.sub(r'\s*第[一二三四五六七八九十\d]+季$', '', result)
    
    return result.strip()
```

### 优先级 2: 支持 TMDB ID 提取（中期）

```python
def parse_media_filename(filename):
    # 1. 提取 TMDB ID
    tmdb_id, filename = extract_tmdb_id(filename)
    
    # 2. 如果有 TMDB ID，直接查询
    if tmdb_id:
        metadata = query_by_tmdb_id(tmdb_id)
        return metadata
    
    # 3. 否则使用标题查询
    return query_by_title(filename)
```

### 优先级 3: 使用 PTN 库（长期）

**PTN (Parse Torrent Name)** 是一个专门解析种子文件名的库：

```python
import PTN

info = PTN.parse("密室大逃脱大神版.第七季.Great.Escape.Super.S07E11.2019.2160p.WEB-DL.H265.AAC-HHWEB.mp4")

# 返回:
# {
#   'title': '密室大逃脱大神版 第七季 Great Escape Super',
#   'season': 7,
#   'episode': 11,
#   'year': 2019,
#   'resolution': '2160p',
#   'codec': 'H265',
#   'audio': 'AAC',
#   'quality': 'WEB-DL',
#   'group': 'HHWEB'
# }
```

**优点：**
- 自动识别所有技术参数
- 自动提取 Release Group
- 支持多种命名格式

---

## 📝 立即可以实施的改进

### 1. 改进 `extract_chinese_title()`

```python
@staticmethod
def extract_chinese_title(title):
    """从混合标题中提取纯中文标题（借鉴 MoviePilot）"""
    if not title:
        return title
    
    # 检查是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in title)
    if not has_chinese:
        return title
    
    # 1. 移除 Release Group（常见的制作组）
    release_groups = ['CHDWEB', 'ADWeb', 'HHWEB', 'DBTV', 'NGB', 'FRDS', 'mUHD', 'AilMWeb', 'UBWEB']
    for group in release_groups:
        title = re.sub(rf'-{group}$', '', title, flags=re.IGNORECASE)
        title = re.sub(rf'\.{group}\.', '.', title, flags=re.IGNORECASE)
    
    # 2. 移除技术参数
    tech_params = ['2160p', '1080p', '720p', '4K', 'H.264', 'H.265', 'x264', 'x265',
                   'WEB-DL', 'BluRay', 'WEBRip', 'HDRip', 'DDP', 'AAC', 'Atmos']
    for param in tech_params:
        title = re.sub(rf'\.{param}\.', '.', title, flags=re.IGNORECASE)
    
    # 3. 替换点号为空格
    cleaned = title.replace('.', ' ')
    
    # 4. 提取中文部分
    parts = cleaned.split()
    chinese_parts = []
    for part in parts:
        if any('\u4e00' <= c <= '\u9fff' for c in part):
            chinese_parts.append(part)
        elif part.isdigit():
            chinese_parts.append(part)
    
    if chinese_parts:
        result = ' '.join(chinese_parts)
        result = ' '.join(result.split())
        # 只移除"第X季"，保留"大神版"等版本标识
        result = re.sub(r'\s*第[一二三四五六七八九十\d]+季$', '', result)
        return result.strip()
    
    return title
```

### 2. 添加 Release Group 检测

```python
@staticmethod
def remove_release_group(title):
    """移除 Release Group"""
    release_groups = [
        'CHDWEB', 'ADWeb', 'HHWEB', 'DBTV', 'NGB', 
        'FRDS', 'mUHD', 'AilMWeb', 'UBWEB', 'CHDWEBII', 'CHDWEBIII'
    ]
    
    for group in release_groups:
        # 移除末尾的 -GROUP
        title = re.sub(rf'-{group}$', '', title, flags=re.IGNORECASE)
        # 移除中间的 .GROUP.
        title = re.sub(rf'\.{group}\.', '.', title, flags=re.IGNORECASE)
    
    return title
```

---

## 🚀 下一步行动

1. **立即修复** - 改进 `extract_chinese_title()` 方法
2. **测试验证** - 使用实际文件名测试
3. **推送部署** - 推送 v1.2.11 到服务器
4. **长期优化** - 考虑集成 PTN 库或借鉴更多 MoviePilot 的实现

---

## 📊 对比总结

| 功能 | 我们的实现 | MoviePilot | 改进建议 |
|------|-----------|-----------|---------|
| 标题清理 | 简单提取中文 | WordsMatcher + 规则引擎 | ✅ 添加 Release Group 移除 |
| TMDB 查询 | 直接查询 | 支持 TMDB ID 提取 | 🔄 中期添加 |
| 文件名解析 | 自定义正则 | PTN 库 | 🔄 长期考虑 |
| 集数处理 | 基础支持 | 支持偏移和范围 | 🔄 按需添加 |
| 架构设计 | 单文件 | 模块化 | 🔄 逐步优化 |

