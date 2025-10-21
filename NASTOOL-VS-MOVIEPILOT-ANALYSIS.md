# NASTool vs MoviePilot 深度对比分析

## 📚 项目关系

- **NASTool**: 前一代作品，更成熟稳定
- **MoviePilot**: 新一代作品，架构重构

## 🔍 核心差异对比

### 1. Release Group 识别

#### NASTool 的实现 (`release_groups.py`)

**特点：**
- ✅ **站点分类管理** - 按PT站点分组管理 Release Group
- ✅ **预定义列表** - 内置了大量常见制作组
- ✅ **自定义支持** - 支持用户自定义制作组和分隔符
- ✅ **正则匹配** - 使用精确的正则表达式

**代码示例：**
```python
RELEASE_GROUPS = {
    "chdbits": ['CHD(?:|Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD'],
    "hdchina": ['HDC(?:|hina|TV)', 'k9611', 'tudou', 'iHD'],
    "hhanclub": ['HHWEB'],
    "keepfrds": ['FRDS', 'Yumi', 'cXcY'],
    # ... 更多站点
}

def match(self, title):
    groups_re = re.compile(r"(?<=[-@\[￡【&])(?:%s)(?=[@.\s\]\[】&])" % groups, re.I)
    return separator.join(re.findall(groups_re, title))
```

**优势：**
1. 按站点分类，便于管理和更新
2. 支持正则表达式，匹配更灵活
3. 处理重复识别，保留顺序
4. 自定义分隔符

#### MoviePilot 的实现

**特点：**
- 使用 `WordsMatcher` 预处理
- 没有专门的 Release Group 管理类
- 集成在整体的标题清理流程中

#### 我们当前的实现

**特点：**
- ❌ 简单的字符串列表
- ❌ 没有按站点分类
- ❌ 没有正则表达式支持

**改进建议：**
```python
# 借鉴 NASTool 的实现
class ReleaseGroupCleaner:
    RELEASE_GROUPS = {
        "chdbits": ['CHD(?:|Bits|PAD|(?:|HK)TV|WEB)', 'StBOX'],
        "hhanclub": ['HHWEB'],
        "keepfrds": ['FRDS'],
        # ...
    }
    
    def remove(self, title):
        # 使用正则表达式移除
        groups_pattern = self._build_pattern()
        return re.sub(groups_pattern, '', title)
```

---

### 2. 元数据识别流程

#### NASTool (`metainfo.py`)

**流程：**
```python
def MetaInfo(title, subtitle=None, mtype=None):
    # 1. 记录原始名称
    org_title = title
    
    # 2. 应用自定义识别词（WordsHelper）
    rev_title, msg, used_info = WordsHelper().process(title)
    
    # 3. 判断是否为文件
    fileflag = os.path.splitext(org_title)[-1] in RMT_MEDIAEXT
    
    # 4. 判断类型（动漫 vs 普通视频）
    if mtype == MediaType.ANIME or is_anime(rev_title):
        meta_info = MetaAnime(rev_title, subtitle, fileflag)
    else:
        meta_info = MetaVideo(rev_title, subtitle, fileflag)
    
    # 5. 保存识别信息
    meta_info.org_string = org_title
    meta_info.rev_string = rev_title
    meta_info.ignored_words = used_info.get("ignored")
    meta_info.replaced_words = used_info.get("replaced")
    meta_info.offset_words = used_info.get("offset")
    
    return meta_info
```

**关键特性：**
- ✅ **WordsHelper** - 统一的识别词处理
- ✅ **保留原始信息** - org_string, rev_string
- ✅ **识别词追踪** - 记录使用了哪些识别词
- ✅ **文件标识** - 区分文件和种子名

#### MoviePilot (`metainfo.py`)

**流程：**
```python
def MetaInfo(title, subtitle=None, custom_words=None):
    # 1. 预处理标题
    title, apply_words = WordsMatcher().prepare(title, custom_words)
    
    # 2. 提取媒体信息（TMDB ID等）
    title, metainfo = find_metainfo(title)
    
    # 3. 判断是否为文件
    isfile = Path(title).suffix.lower() in settings.RMT_MEDIAEXT
    
    # 4. 选择解析器
    meta = MetaAnime(title) if is_anime(title) else MetaVideo(title)
    
    # 5. 应用元数据
    meta.tmdbid = metainfo.get('tmdbid')
    meta.begin_season = metainfo.get('begin_season')
    
    return meta
```

**改进点：**
- ✅ 支持从标题中提取 TMDB ID
- ✅ 支持自定义识别词
- ✅ 更现代的 Path 处理

#### 我们当前的实现

**问题：**
- ❌ 没有 WordsHelper/WordsMatcher
- ❌ 没有识别词追踪
- ❌ 标题清理逻辑分散

**改进建议：**
```python
class TitleProcessor:
    def __init__(self):
        self.release_group_cleaner = ReleaseGroupCleaner()
        self.tech_param_cleaner = TechParamCleaner()
    
    def process(self, title):
        # 1. 记录原始标题
        original = title
        
        # 2. 移除 Release Group
        title = self.release_group_cleaner.remove(title)
        
        # 3. 移除技术参数
        title = self.tech_param_cleaner.remove(title)
        
        # 4. 提取中文标题
        title = self.extract_chinese(title)
        
        return {
            'original': original,
            'cleaned': title,
            'removed_groups': [...],
            'removed_params': [...]
        }
```

---

### 3. 副标题解析

#### NASTool 的创新 (`_base.py`)

**功能：**
```python
# 副标题正则表达式
_subtitle_season_re = r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十S\-]+)\s*季(?!\s*全|\s*共)"
_subtitle_season_all_re = r"[全共]\s*([0-9一二三四五六七八九十]+)\s*季|([0-9一二三四五六七八九十]+)\s*季\s*[全共]"
_subtitle_episode_re = r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十百零EP\-]+)\s*[集话話期](?!\s*全|\s*共)"
_subtitle_episode_all_re = r"([0-9一二三四五六七八九十百零]+)\s*集\s*[全共]|[共全]\s*([0-9一二三四五六七八九十百零]+)\s*[集话話期]"

def init_subtitle(self, title_text):
    # 从副标题中提取季集信息
    # 支持：第1季、第1-3季、全12集、12集全等
```

**示例：**
```
"密室大逃脱 第七季" → begin_season=7
"全12集" → total_episodes=12
"第1-3季" → begin_season=1, end_season=3
```

**我们没有的功能：**
- ❌ 副标题解析
- ❌ 中文数字转换（cn2an）
- ❌ "全X集"、"X集全" 识别

---

### 4. Release Group 数据对比

#### NASTool 的 Release Group 列表

**按站点分类（部分）：**
```python
"chdbits": ['CHD(?:|Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD', 'Lee', 'xiaopie']
"hdchina": ['HDC(?:|hina|TV)', 'k9611', 'tudou', 'iHD']
"hhanclub": ['HHWEB']
"keepfrds": ['FRDS', 'Yumi', 'cXcY']
"lemonhd": ['L(?:eague(?:(?:C|H)D|(?:M|T)V|NF|WEB)|HD)', 'i18n', 'CiNT']
"mteam": ['MTeam(?:|TV)', 'MPAD']
"ourbits": ['Our(?:Bits|TV)', 'FLTTH', 'Ao', 'PbK', 'MGs', 'iLove(?:HD|TV)']
"pterclub": ['PTer(?:|DIY|Game|(?:M|T)V|WEB)']
"pthome": ['PTH(?:|Audio|eBook|music|ome|tv|WEB)']
"ptsbao": ['PTsbao', 'OPS', 'F(?:Fans(?:AIeNcE|BD|D(?:VD|IY)|TV|WEB)|HDMv)', 'SGXT']
"totheglory": ['TTG', 'WiKi', 'NGB', 'DoA', '(?:ARi|ExRE)N']
"others": ['B(?:MDru|eyondHD|TN)', 'C(?:fandora|trlhd|MRG)', 'DON', 'EVO', 'FLUX', 
           'HONE(?:|yG)', 'N(?:oGroup|T(?:b|G))', 'PandaMoon', 'SMURF', 'T(?:EPES|aengoo|rollHD)']
"anime": ['ANi', 'HYSUB', 'KTXP', 'LoliHouse', 'MCE', 'Nekomoe kissaten', 
          '(?:Lilith|NC)-Raws', '织梦字幕组']
```

**我们当前的列表：**
```python
release_groups = [
    'CHDWEB', 'CHDWEBII', 'CHDWEBIII', 'ADWeb', 'HHWEB', 'DBTV', 
    'NGB', 'FRDS', 'mUHD', 'AilMWeb', 'UBWEB', 'CHDTV', 'HDCTV'
]
```

**差距：**
- NASTool: 100+ 制作组，支持正则变体
- 我们: 13 个制作组，简单字符串匹配

---

## 🎯 立即可以借鉴的改进

### 优先级 1: 使用 NASTool 的 Release Group 列表

```python
class ReleaseGroupCleaner:
    """借鉴 NASTool 的 Release Group 管理"""
    
    RELEASE_GROUPS = {
        # 复制 NASTool 的完整列表
        "chdbits": ['CHD(?:|Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD'],
        "hdchina": ['HDC(?:|hina|TV)', 'k9611', 'tudou', 'iHD'],
        # ... 更多
    }
    
    def __init__(self):
        # 合并所有制作组
        all_groups = []
        for site_groups in self.RELEASE_GROUPS.values():
            all_groups.extend(site_groups)
        self.pattern = '|'.join(all_groups)
    
    def remove(self, title):
        """移除 Release Group"""
        # 使用 NASTool 的正则模式
        groups_re = re.compile(
            r"(?<=[-@\[￡【&])(?:%s)(?=[@.\s\]\[】&])" % self.pattern, 
            re.I
        )
        return re.sub(groups_re, '', title)
```

### 优先级 2: 添加副标题解析

```python
def parse_subtitle(self, subtitle):
    """解析副标题中的季集信息"""
    if not subtitle:
        return
    
    # 第X季
    season_match = re.search(
        r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十S\-]+)\s*季",
        subtitle
    )
    if season_match:
        season_str = season_match.group(1)
        # 使用 cn2an 转换中文数字
        self.begin_season = cn2an.cn2an(season_str, mode='smart')
    
    # 全X集
    episode_match = re.search(
        r"[全共]\s*([0-9一二三四五六七八九十百零]+)\s*集",
        subtitle
    )
    if episode_match:
        episode_str = episode_match.group(1)
        self.total_episodes = cn2an.cn2an(episode_str, mode='smart')
```

### 优先级 3: 保留识别历史

```python
class MetaInfo:
    def __init__(self, title):
        self.original_title = title
        self.cleaned_title = None
        self.removed_groups = []
        self.removed_params = []
        self.processing_log = []
    
    def log_step(self, step, before, after):
        """记录处理步骤"""
        self.processing_log.append({
            'step': step,
            'before': before,
            'after': after,
            'removed': self._diff(before, after)
        })
```

---

## 📊 功能对比表

| 功能 | NASTool | MoviePilot | 我们的实现 | 改进建议 |
|------|---------|-----------|-----------|---------|
| Release Group 识别 | ✅ 100+ 正则 | ⚠️ 集成在 WordsMatcher | ❌ 13个简单字符串 | 🔥 立即采用 NASTool 列表 |
| 按站点分类 | ✅ | ❌ | ❌ | 🔄 中期添加 |
| 副标题解析 | ✅ | ❌ | ❌ | 🔄 中期添加 |
| 中文数字转换 | ✅ cn2an | ❌ | ❌ | 🔄 按需添加 |
| 识别词追踪 | ✅ | ✅ | ❌ | 🔄 长期优化 |
| TMDB ID 提取 | ❌ | ✅ | ❌ | 🔄 中期添加 |
| 自定义识别词 | ✅ | ✅ | ❌ | 🔄 长期优化 |

---

## 🚀 下一步行动

### 立即实施（v1.2.12）

1. **采用 NASTool 的 Release Group 列表**
   - 复制完整的 RELEASE_GROUPS 字典
   - 使用正则表达式匹配
   - 支持更多制作组

2. **改进正则匹配模式**
   - 使用 NASTool 的边界匹配模式
   - `(?<=[-@\[￡【&])(?:groups)(?=[@.\s\]\[】&])`

### 中期优化（v1.3.0）

1. **添加副标题解析**
   - 支持"第X季"、"全X集"
   - 集成 cn2an 库

2. **添加识别词追踪**
   - 记录处理步骤
   - 便于调试和优化

### 长期规划（v2.0.0）

1. **完整的 WordsHelper 系统**
   - 自定义识别词
   - 识别词优先级
   - 识别词冲突处理

2. **按站点分类管理**
   - 支持用户自定义站点
   - 站点特定的识别规则

---

## 📝 总结

**NASTool 的优势：**
- 更成熟的 Release Group 管理
- 完善的副标题解析
- 详细的识别词追踪

**MoviePilot 的优势：**
- 更现代的架构
- 支持 TMDB ID 提取
- 更好的模块化设计

**我们应该：**
1. ✅ 立即采用 NASTool 的 Release Group 列表
2. ✅ 借鉴 NASTool 的正则匹配模式
3. 🔄 逐步添加副标题解析功能
4. 🔄 长期建立完整的识别词系统

通过结合两者的优势，我们可以打造更强大的标题识别系统！
