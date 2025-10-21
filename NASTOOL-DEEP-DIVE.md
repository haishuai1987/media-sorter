# NASTool 深度分析 - 核心实现解析

## 🏗️ 架构概览

NASTool 采用模块化设计，核心模块：

```
app/
├── media/              # 媒体信息处理
│   ├── meta/          # 元数据识别
│   │   ├── metainfo.py       # 入口
│   │   ├── _base.py          # 基类
│   │   ├── metavideo.py      # 视频识别
│   │   ├── metaanime.py      # 动漫识别
│   │   └── release_groups.py # 制作组识别
│   ├── douban.py      # 豆瓣API
│   ├── media.py       # 媒体查询
│   └── category.py    # 分类管理
├── helper/            # 辅助工具
│   └── words_helper.py # 识别词处理
└── filetransfer.py    # 文件转移
```

---

## 🎯 核心功能深度解析

### 1. WordsHelper - 识别词系统

**功能类型：**

#### 类型1: 屏蔽词
```python
# 移除不需要的内容
"密室大逃脱.大神版.第七季" → "密室大逃脱.第七季"
```

#### 类型2: 替换词
```python
# 修正错误的标题
"密室大逃脱大神版" → "密室大逃脱 大神版"
```

#### 类型3: 替换+集偏移
```python
# 同时替换标题和调整集数
"某剧 EP10" → "某剧 EP20"  # 偏移 +10
```

#### 类型4: 集数偏移
```python
# 只调整集数
front="EP", back="", offset="EP+10"
"EP05" → "EP15"
```

**实现细节：**
```python
def process(self, title):
    # 1. 遍历所有识别词
    for word_info in self.words_info:
        match word_info.TYPE:
            case 1:  # 屏蔽
                title = self.replace(title, word, "")
            case 2:  # 替换
                title = self.replace(title, old, new)
            case 3:  # 替换+偏移
                title = self.replace(title, old, new)
                title = self.episode_offset(title, front, back, offset)
            case 4:  # 偏移
                title = self.episode_offset(title, front, back, offset)
    
    return title, messages, used_words
```

**集数偏移算法：**
```python
def episode_offset(title, front, back, offset):
    # 1. 查找集数位置
    pattern = r'(?<=%s.*?)[0-9一二三四五六七八九十]+(?=.*?%s)' % (front, back)
    episode_nums = re.findall(pattern, title)
    
    # 2. 转换中文数字
    for ep_str in episode_nums:
        ep_int = cn2an.cn2an(ep_str, "smart")  # "十二" → 12
        
        # 3. 计算偏移
        offset_calc = offset.replace("EP", str(ep_int))
        ep_offset = eval(offset_calc)  # "EP+10" → 12+10 = 22
        
        # 4. 转换回原格式
        if not ep_str.isdigit():
            ep_offset_str = cn2an.an2cn(ep_offset, "low")  # 22 → "二十二"
        else:
            ep_offset_str = str(ep_offset).zfill(len(ep_str))  # 保持补零
        
        # 5. 替换
        title = title.replace(ep_str, ep_offset_str)
    
    return title
```

---

### 2. Release Group 识别

#### NASTool 的完整列表

**按站点分类（完整版）：**
```python
RELEASE_GROUPS = {
    "chdbits": [
        'CHD(?:|Bits|PAD|(?:|HK)TV|WEB)',  # CHD, CHDBits, CHDPAD, CHDTV, CHDHKTV, CHDWEB
        'StBOX', 'OneHD', 'Lee', 'xiaopie'
    ],
    "hdchina": [
        'HDC(?:|hina|TV)',  # HDC, HDChina, HDCTV
        'k9611', 'tudou', 'iHD'
    ],
    "hhanclub": ['HHWEB'],
    "keepfrds": ['FRDS', 'Yumi', 'cXcY'],
    "lemonhd": [
        'L(?:eague(?:(?:C|H)D|(?:M|T)V|NF|WEB)|HD)',  # League系列
        'i18n', 'CiNT'
    ],
    "mteam": ['MTeam(?:|TV)', 'MPAD'],
    "ourbits": [
        'Our(?:Bits|TV)',  # OurBits, OurTV
        'FLTTH', 'Ao', 'PbK', 'MGs', 'iLove(?:HD|TV)'
    ],
    "pterclub": ['PTer(?:|DIY|Game|(?:M|T)V|WEB)'],
    "pthome": ['PTH(?:|Audio|eBook|music|ome|tv|WEB)'],
    "ptsbao": [
        'PTsbao', 'OPS',
        'F(?:Fans(?:AIeNcE|BD|D(?:VD|IY)|TV|WEB)|HDMv)',
        'SGXT'
    ],
    "totheglory": [
        'TTG', 'WiKi', 'NGB', 'DoA',
        '(?:ARi|ExRE)N'
    ],
    "others": [
        'B(?:MDru|eyondHD|TN)',
        'C(?:fandora|trlhd|MRG)',
        'DON', 'EVO', 'FLUX',
        'HONE(?:|yG)',
        'N(?:oGroup|T(?:b|G))',
        'PandaMoon', 'SMURF',
        'T(?:EPES|aengoo|rollHD)'
    ],
    "anime": [
        'ANi', 'HYSUB', 'KTXP', 'LoliHouse', 'MCE',
        'Nekomoe kissaten',
        '(?:Lilith|NC)-Raws',
        '织梦字幕组'
    ]
}
```

**匹配模式：**
```python
# 边界匹配：前面必须是 [-@[￡【&]，后面必须是 [@.\s][】&]
groups_re = re.compile(
    r"(?<=[-@\[￡【&])(?:%s)(?=[@.\s\]\[】&])" % groups,
    re.I
)
```

**示例：**
```
"密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB"
                                        ^^^^^^
                                        匹配到 CHDWEB
```

---

### 3. 副标题解析

#### NASTool 的正则表达式

```python
# 第X季（不包括"全X季"）
_subtitle_season_re = r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十S\-]+)\s*季(?!\s*全|\s*共)"

# 全X季 / X季全
_subtitle_season_all_re = r"[全共]\s*([0-9一二三四五六七八九十]+)\s*季|([0-9一二三四五六七八九十]+)\s*季\s*[全共]"

# 第X集（不包括"全X集"）
_subtitle_episode_re = r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十百零EP\-]+)\s*[集话話期](?!\s*全|\s*共)"

# 全X集 / X集全
_subtitle_episode_all_re = r"([0-9一二三四五六七八九十百零]+)\s*集\s*[全共]|[共全]\s*([0-9一二三四五六七八九十百零]+)\s*[集话話期]"
```

**支持的格式：**
```
✓ "第七季" → season=7
✓ "第1-3季" → begin_season=1, end_season=3
✓ "全12集" → total_episodes=12
✓ "12集全" → total_episodes=12
✓ "第10集" → episode=10
✓ "第1-5集" → begin_episode=1, end_episode=5
```

**中文数字转换：**
```python
import cn2an

cn2an.cn2an("七", mode='smart')      # → 7
cn2an.cn2an("十二", mode='smart')    # → 12
cn2an.cn2an("二十", mode='smart')    # → 20
cn2an.an2cn(22, "low")               # → "二十二"
```

---

### 4. 文件转移逻辑

#### NASTool 的重命名格式

**默认格式：**
```python
# 电影
DEFAULT_MOVIE_FORMAT = "{{title}}{% if year %} ({{year}}){% endif %}/{{title}}{% if year %} ({{year}}){% endif %}{% if part %}-{{part}}{% endif %}{% if videoFormat %} - {{videoFormat}}{% endif %}{{fileExt}}"

# 电视剧
DEFAULT_TV_FORMAT = "{{title}}{% if year %} ({{year}}){% endif %}/Season {{season}}/{{title}} - {{season_episode}}{% if part %}-{{part}}{% endif %}{% if episode %} - 第 {{episode}} 集{% endif %}{{fileExt}}"
```

**支持的变量：**
```
{{title}}          - 标题
{{year}}           - 年份
{{season}}         - 季数（补零）
{{season_episode}} - S01E01
{{episode}}        - 集数
{{part}}           - Part信息
{{videoFormat}}    - 视频格式（1080p等）
{{fileExt}}        - 文件扩展名
```

**我们当前的实现：**
- ✅ 已经支持类似的格式
- ✅ 使用 Jinja2 模板（和 NASTool 一样）

---

## 🚀 立即可以实施的改进

### v1.2.12 - 采用 NASTool 的 Release Group 列表

```python
class ReleaseGroupCleaner:
    """借鉴 NASTool 的完整实现"""
    
    # 复制 NASTool 的完整列表
    RELEASE_GROUPS = {
        "chdbits": ['CHD(?:|Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD', 'Lee', 'xiaopie'],
        "hdchina": ['HDC(?:|hina|TV)', 'k9611', 'tudou', 'iHD'],
        "hhanclub": ['HHWEB'],
        "keepfrds": ['FRDS', 'Yumi', 'cXcY'],
        "lemonhd": ['L(?:eague(?:(?:C|H)D|(?:M|T)V|NF|WEB)|HD)', 'i18n', 'CiNT'],
        "mteam": ['MTeam(?:|TV)', 'MPAD'],
        "ourbits": ['Our(?:Bits|TV)', 'FLTTH', 'Ao', 'PbK', 'MGs', 'iLove(?:HD|TV)'],
        "pterclub": ['PTer(?:|DIY|Game|(?:M|T)V|WEB)'],
        "pthome": ['PTH(?:|Audio|eBook|music|ome|tv|WEB)'],
        "ptsbao": ['PTsbao', 'OPS', 'F(?:Fans(?:AIeNcE|BD|D(?:VD|IY)|TV|WEB)|HDMv)', 'SGXT'],
        "totheglory": ['TTG', 'WiKi', 'NGB', 'DoA', '(?:ARi|ExRE)N'],
        "others": ['B(?:MDru|eyondHD|TN)', 'C(?:fandora|trlhd|MRG)', 'DON', 'EVO', 'FLUX',
                   'HONE(?:|yG)', 'N(?:oGroup|T(?:b|G))', 'PandaMoon', 'SMURF', 'T(?:EPES|aengoo|rollHD)'],
        "anime": ['ANi', 'HYSUB', 'KTXP', 'LoliHouse', 'MCE', 'Nekomoe kissaten',
                  '(?:Lilith|NC)-Raws', '织梦字幕组']
    }
    
    def __init__(self):
        # 合并所有制作组
        all_groups = []
        for site_groups in self.RELEASE_GROUPS.values():
            all_groups.extend(site_groups)
        self.pattern = '|'.join(all_groups)
    
    def remove(self, title):
        """使用 NASTool 的边界匹配模式"""
        groups_re = re.compile(
            r"(?<=[-@\[￡【&])(?:%s)(?=[@.\s\]\[】&])" % self.pattern,
            re.I
        )
        # 移除匹配到的制作组
        return re.sub(groups_re, '', title)
```

**优势：**
- ✅ 支持 100+ 制作组
- ✅ 正则表达式支持变体
- ✅ 精确的边界匹配
- ✅ 避免误匹配

---

### v1.3.0 - 添加副标题解析

```python
def parse_subtitle(self, subtitle):
    """解析副标题（借鉴 NASTool）"""
    if not subtitle:
        return
    
    # 安装 cn2an: pip install cn2an
    import cn2an
    
    # 第X季
    season_match = re.search(
        r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十S\-]+)\s*季(?!\s*全|\s*共)",
        subtitle
    )
    if season_match:
        season_str = season_match.group(1).replace('S', '').strip()
        try:
            if '-' in season_str:
                # 第1-3季
                parts = season_str.split('-')
                self.begin_season = cn2an.cn2an(parts[0], mode='smart')
                self.end_season = cn2an.cn2an(parts[1], mode='smart')
            else:
                # 第7季
                self.begin_season = cn2an.cn2an(season_str, mode='smart')
        except:
            pass
    
    # 全X集
    episode_all_match = re.search(
        r"[全共]\s*([0-9一二三四五六七八九十百零]+)\s*集",
        subtitle
    )
    if episode_all_match:
        episode_str = episode_all_match.group(1)
        try:
            self.total_episodes = cn2an.cn2an(episode_str, mode='smart')
        except:
            pass
```

---

## 📊 对比总结

### NASTool 的优势

1. **Release Group 管理**
   - 100+ 制作组
   - 按站点分类
   - 正则表达式支持

2. **识别词系统**
   - 4种类型（屏蔽、替换、偏移、组合）
   - 支持正则表达式
   - 数据库存储

3. **副标题解析**
   - 支持中文表达
   - 中文数字转换
   - 季集范围识别

4. **文件转移**
   - 多种转移模式（复制、移动、硬链接、软链接）
   - 文件大小过滤
   - 路径忽略规则

### 我们当前的优势

1. **简单易用**
   - 单文件部署
   - 无数据库依赖
   - Web界面友好

2. **实时日志**
   - SSE 推送
   - 进度显示
   - 错误追踪

3. **云服务器支持**
   - 自动环境检测
   - 远程更新
   - API 管理

---

## 🎯 改进路线图

### v1.2.12 - Release Group 增强（立即）
- ✅ 采用 NASTool 的完整 Release Group 列表
- ✅ 使用正则表达式匹配
- ✅ 边界匹配模式

### v1.3.0 - 副标题解析（中期）
- 🔄 添加副标题解析功能
- 🔄 集成 cn2an 库
- 🔄 支持中文数字转换

### v1.4.0 - 识别词系统（长期）
- 🔄 完整的识别词管理
- 🔄 支持屏蔽、替换、偏移
- 🔄 Web界面配置

### v2.0.0 - 架构重构（远期）
- 🔄 模块化设计
- 🔄 插件系统
- 🔄 工作流引擎

---

## 💡 建议

**当前最重要的改进：**
1. 立即采用 NASTool 的 Release Group 列表（v1.2.12）
2. 保持我们的简单架构和实时日志优势
3. 逐步添加高级功能

**不要盲目追求复杂：**
- NASTool 有数据库、插件系统、工作流引擎
- 但我们的单文件架构更适合快速部署
- 保持简单，逐步优化

要不要我现在就帮你实施 **v1.2.12 - 采用 NASTool 的完整 Release Group 列表**？
