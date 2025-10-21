# MoviePilot 三仓库架构深度分析

## 📦 仓库结构概览

MoviePilot 采用**前后端分离 + 资源独立**的三仓库架构：

```
MoviePilot 生态系统
├── MoviePilot (后端核心)          - Python FastAPI 后端服务
├── MoviePilot-Frontend (前端)     - Vue3 + Vuetify 前端界面
├── MoviePilot-Resources (资源)    - 站点认证资源（闭源）
├── MoviePilot-Plugins (插件)      - 社区插件仓库
└── MoviePilot-Server (服务端)     - 认证服务器
```

---

## 🏗️ 仓库 1: MoviePilot (后端核心)

### 目录结构

```
MoviePilot/
├── app/                          # 应用核心代码
│   ├── core/                     # 核心模块
│   │   ├── meta/                 # 元数据识别
│   │   │   ├── metainfo.py       # 元数据识别入口
│   │   │   ├── metavideo.py      # 视频识别
│   │   │   ├── metaanime.py      # 动漫识别
│   │   │   ├── releasegroup.py   # 制作组识别 ⭐
│   │   │   ├── words.py          # 识别词处理 ⭐
│   │   │   ├── customization.py  # 自定义规则
│   │   │   └── streamingplatform.py  # 流媒体平台
│   │   ├── config.py             # 配置管理
│   │   ├── event.py              # 事件系统
│   │   ├── plugin.py             # 插件系统
│   │   ├── module.py             # 模块管理
│   │   └── security.py           # 安全认证
│   ├── api/                      # REST API 接口
│   ├── chain/                    # 业务链（工作流）
│   ├── db/                       # 数据库操作
│   ├── helper/                   # 辅助工具
│   ├── modules/                  # 功能模块
│   ├── plugins/                  # 内置插件
│   ├── schemas/                  # 数据模型
│   ├── utils/                    # 工具函数
│   ├── workflow/                 # 工作流引擎
│   ├── main.py                   # 应用入口 ⭐
│   ├── factory.py                # FastAPI 工厂
│   └── scheduler.py              # 定时任务
├── config/                       # 配置文件
│   ├── app.env                   # 环境变量
│   └── category.yaml             # 分类规则
├── database/                     # 数据库迁移
├── docker/                       # Docker 配置
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── nginx.template.conf       # Nginx 配置
├── requirements.in               # 依赖列表 ⭐
└── version.py                    # 版本管理
```

### 核心技术栈

```python
# requirements.in (精简版)
fastapi~=0.115.14              # Web 框架
uvicorn~=0.34.3                # ASGI 服务器
SQLAlchemy~=2.0.41             # ORM
pydantic~=1.10.22              # 数据验证
alembic~=1.16.2                # 数据库迁移

# 元数据识别
regex~=2024.11.6               # 正则表达式
cn2an~=0.5.19                  # 中文数字转换 ⭐
anitopy~=2.1.1                 # 动漫标题解析
zhconv~=1.4.3                  # 简繁转换

# 下载器
qbittorrent-api==2025.5.0      # qBittorrent
transmission-rpc~=4.3.0        # Transmission

# 媒体服务器
plexapi~=4.17.0                # Plex

# 通知
pyTelegramBotAPI~=4.27.0       # Telegram
slack-bolt~=1.23.0             # Slack

# AI 集成
langchain==0.3.27              # LangChain 框架
langchain-openai==0.3.33       # OpenAI
langchain-google-genai==2.0.10 # Google Gemini
langchain-deepseek==0.1.4      # DeepSeek
openai==1.108.2                # OpenAI SDK

# 其他
APScheduler~=3.11.0            # 定时任务
playwright~=1.53.0             # 浏览器自动化
docker~=7.1.0                  # Docker API
watchdog~=6.0.0                # 文件监控
```

### 核心模块分析

#### 1. 元数据识别 (app/core/meta/)

**metainfo.py - 识别入口**
```python
def MetaInfo(title: str, subtitle: Optional[str] = None, 
             custom_words: List[str] = None) -> MetaBase:
    """
    根据标题和副标题识别元数据
    """
    # 1. 预处理标题（识别词）
    title, apply_words = WordsMatcher().prepare(title, custom_words)
    
    # 2. 提取媒体信息（tmdbid、doubanid等）
    title, metainfo = find_metainfo(title)
    
    # 3. 判断是否动漫
    meta = MetaAnime(title, subtitle) if is_anime(title) else MetaVideo(title, subtitle)
    
    # 4. 应用识别词
    meta.apply_words = apply_words
    
    return meta
```

**releasegroup.py - 制作组识别**
```python
class ReleaseGroupsMatcher:
    RELEASE_GROUPS = {
        "chdbits": ['CHD(?:Bits|PAD|(?:|HK)TV|WEB|)', 'StBOX', ...],
        "hdchina": ['HDC(?:hina|TV|)', 'k9611', ...],
        # ... 100+ 制作组
    }
    
    def match(self, title: str, groups: str = None):
        """使用正则表达式匹配制作组"""
        # 支持自定义制作组
        custom_groups = SystemConfigOper().get(SystemConfigKey.CustomReleaseGroups)
        
        # 边界匹配
        groups_re = re.compile(
            r"(?<=[-@\[￡【&])(?:%s)(?=[@.\s\]\[】&])" % groups,
            re.I
        )
        return groups_re.findall(title)
```

**words.py - 识别词处理**
```python
class WordsMatcher:
    def prepare(self, title: str, custom_words: List[str] = None):
        """
        支持三种格式：
        1. 屏蔽词：直接移除
        2. 替换词：被替换词 => 替换词
        3. 集偏移：前定位词 <> 后定位词 >> 偏移量（EP）
        """
        # 示例：
        # "大神版" => ""  # 屏蔽
        # "密室大逃脱大神版" => "密室大逃脱 大神版"  # 替换
        # "EP <> >> EP+10"  # 集偏移
```

#### 2. 插件系统 (app/core/plugin.py)

```python
class PluginManager:
    """插件管理器"""
    
    def load_plugins(self):
        """动态加载插件"""
        # 从 app/plugins/ 加载内置插件
        # 从用户目录加载自定义插件
    
    def run_plugin(self, plugin_id: str, **kwargs):
        """执行插件"""
```

#### 3. 工作流引擎 (app/workflow/)

```python
class WorkflowEngine:
    """工作流引擎"""
    
    def execute(self, workflow: dict):
        """执行工作流"""
        # 支持条件判断、循环、并行等
```

---

## 🎨 仓库 2: MoviePilot-Frontend (前端)

### 技术栈

```json
{
  "dependencies": {
    "vue": "^3.x",              // Vue 3
    "vuetify": "^3.x",          // Material Design 组件库
    "vue-router": "^4.x",       // 路由
    "pinia": "^2.x",            // 状态管理
    "axios": "^1.x",            // HTTP 客户端
    "vite": "^5.x"              // 构建工具
  }
}
```

### 构建产物 (reference/dist/)

```
dist/
├── index.html                    # 入口页面
├── assets/                       # 静态资源
│   ├── style-*.css              # 样式文件
│   ├── *.js                     # JS 模块
│   └── images/                  # 图片资源
├── plugin_icon/                  # 插件图标（500+）
│   ├── Emby_A.png
│   ├── Plex_A.png
│   ├── Jellyfin_A.png
│   └── ...
├── manifest.webmanifest          # PWA 配置
├── service-worker.js             # Service Worker
└── nginx.conf                    # Nginx 配置

# 页面模块
├── dashboard.js                  # 仪表盘
├── discover.js                   # 发现页
├── subscribe.js                  # 订阅管理
├── downloading.js                # 下载管理
├── history.js                    # 历史记录
├── media.js                      # 媒体库
├── plugin.js                     # 插件管理
├── setting.js                    # 设置页
└── ...
```

### 特点

1. **PWA 支持** - 可安装为桌面应用
2. **响应式设计** - 适配移动端和桌面端
3. **Material Design** - 现代化 UI
4. **模块化构建** - 按需加载
5. **500+ 插件图标** - 丰富的视觉资源

---

## 🔒 仓库 3: MoviePilot-Resources (资源)

### 目录结构

```
MoviePilot-Resources/
├── resources/                    # Python 3.11 资源
│   ├── sites.cp311-win_amd64.pyd           # Windows x64
│   ├── sites.cp312-win_amd64.pyd           # Windows x64 (3.12)
│   ├── sites.cpython-311-x86_64-linux-gnu.so  # Linux x64
│   ├── sites.cpython-311-aarch64-linux-gnu.so # Linux ARM64
│   ├── sites.cpython-311-darwin.so         # macOS
│   ├── user.sites.bin                      # 用户站点数据
│   └── user.sites.v2.bin                   # 用户站点数据 v2
├── resources.v2/                 # Python 3.12 资源
│   └── ...
├── package.json                  # 版本信息
└── README.md
```

### 资源说明

**闭源原因（官方说明）：**
> 这部分闭源的目的，是为了防止MoviePilot泛滥传播，肆意添加颜色站点支持等，影响项目可持续发展。

**包含内容：**
1. **站点认证** - PT 站点登录、Cookie 管理
2. **站点索引** - 种子搜索、RSS 订阅
3. **站点规则** - 各站点的特殊规则

**使用方式：**
```python
# 在 app/helper/ 目录下
from app.helper import sites  # 加载 .so/.pyd 文件

# 站点认证
sites.login(site_name, username, password)

# 搜索种子
sites.search(keyword, site_name)
```

---

## 🔄 三仓库协作流程

### 开发流程

```
1. 后端开发 (MoviePilot)
   ├── 修改 Python 代码
   ├── 运行 python3 -m app.main
   └── API 文档: http://localhost:3001/docs

2. 前端开发 (MoviePilot-Frontend)
   ├── 修改 Vue 代码
   ├── 运行 yarn dev
   └── 访问: http://localhost:5173

3. 构建前端
   ├── yarn build
   └── 产物输出到 dist/

4. 集成部署
   ├── 复制 dist/ 到后端项目
   ├── 复制 resources/ 到 app/helper/
   └── Docker 构建
```

### Docker 部署流程

```dockerfile
# docker/Dockerfile (简化版)
FROM python:3.12-slim

# 1. 安装后端依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2. 复制后端代码
COPY app/ /app/

# 3. 复制前端构建产物
COPY dist/ /public/

# 4. 复制资源文件
COPY resources/ /app/helper/

# 5. 配置 Nginx
COPY docker/nginx.template.conf /etc/nginx/

# 6. 启动服务
CMD ["sh", "docker/entrypoint.sh"]
```

**entrypoint.sh**
```bash
#!/bin/bash

# 1. 启动 Nginx（前端）
nginx -c /etc/nginx/nginx.conf

# 2. 启动 FastAPI（后端）
python3 -m app.main
```

---

## 🆚 与我们的项目对比

### 架构对比

| 维度 | MoviePilot | 我们的项目 |
|------|-----------|----------|
| **架构** | 前后端分离 | 单文件集成 |
| **前端** | Vue3 + Vuetify | 原生 HTML/CSS/JS |
| **后端** | FastAPI | Python HTTP Server |
| **数据库** | SQLAlchemy + PostgreSQL/SQLite | JSON 文件 |
| **部署** | Docker / 独立运行 | 单文件运行 |
| **依赖** | 80+ Python 包 | 0 依赖（标准库） |
| **插件** | 动态加载 | 无插件系统 |
| **工作流** | 工作流引擎 | 简单脚本 |

### 功能对比

| 功能 | MoviePilot | 我们的项目 |
|------|-----------|----------|
| **元数据识别** | ✅ 完整（100+ 制作组） | ⚠️ 基础（13 个制作组） |
| **识别词系统** | ✅ 4 种类型 | ❌ 无 |
| **中文数字转换** | ✅ cn2an | ❌ 无 |
| **副标题解析** | ✅ 完整 | ❌ 无 |
| **下载器集成** | ✅ qB/TR | ❌ 无 |
| **媒体服务器** | ✅ Plex/Emby/Jellyfin | ❌ 无 |
| **通知系统** | ✅ 10+ 渠道 | ❌ 无 |
| **AI 集成** | ✅ LangChain | ❌ 无 |
| **实时日志** | ❌ 无 | ✅ SSE 推送 |
| **云服务器支持** | ⚠️ 需配置 | ✅ 自动检测 |

---

## 💡 可借鉴的设计

### 1. 元数据识别模块 ⭐⭐⭐

**优先级：高**

```python
# 借鉴 MoviePilot 的识别流程
class MetaInfoRecognizer:
    def recognize(self, title: str):
        # 1. 识别词预处理
        title = self.apply_custom_words(title)
        
        # 2. Release Group 识别（正则表达式）
        title = self.remove_release_groups(title)
        
        # 3. 技术参数识别
        title = self.remove_tech_params(title)
        
        # 4. 季集信息提取
        season, episode = self.extract_season_episode(title)
        
        # 5. 年份提取
        year = self.extract_year(title)
        
        return MetaInfo(title, season, episode, year)
```

### 2. 识别词系统 ⭐⭐

**优先级：中**

```python
# 支持三种识别词
class CustomWords:
    def process(self, title: str, words: List[str]):
        for word in words:
            if " => " in word:
                # 替换词
                old, new = word.split(" => ")
                title = title.replace(old, new)
            elif " >> " in word and " <> " in word:
                # 集偏移
                title = self.episode_offset(title, word)
            else:
                # 屏蔽词
                title = title.replace(word, "")
        return title
```

### 3. 插件系统 ⭐

**优先级：低**

```python
# 简化的插件系统
class PluginManager:
    def load_plugins(self):
        """从 plugins/ 目录加载插件"""
        for file in os.listdir('plugins'):
            if file.endswith('.py'):
                module = importlib.import_module(f'plugins.{file[:-3]}')
                self.plugins.append(module)
    
    def run_plugin(self, name: str, **kwargs):
        """执行插件"""
        plugin = self.get_plugin(name)
        return plugin.execute(**kwargs)
```

---

## 🎯 改进建议

### 阶段 1: v1.2.12 - 元数据识别增强（本周）

**借鉴 MoviePilot 的 Release Group 列表**

```python
# 更新 app.py
RELEASE_GROUPS = {
    "chdbits": ['CHD(?:Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD', ...],
    "hdchina": ['HDC(?:hina|TV)', 'k9611', 'tudou', ...],
    # ... 复制 MoviePilot 的完整列表
}
```

### 阶段 2: v1.3.0 - 识别词系统（下周）

**添加自定义识别词功能**

```python
# 在 Web 界面添加识别词管理
# 支持：屏蔽词、替换词、集偏移
```

### 阶段 3: v1.4.0 - 副标题解析（未来）

**集成 cn2an 库**

```bash
pip install cn2an
```

```python
import cn2an

# "第七季" → 7
season = cn2an.cn2an("七", mode='smart')

# "全12集" → 12
episodes = cn2an.cn2an("十二", mode='smart')
```

### 阶段 4: v2.0.0 - 架构升级（远期）

**考虑前后端分离**

- 保持单文件部署的优势
- 可选的前后端分离模式
- 渐进式升级路径

---

## 📊 总结

### MoviePilot 的优势

1. ✅ **架构清晰** - 前后端分离，模块化设计
2. ✅ **功能完整** - 元数据识别、下载器、媒体服务器集成
3. ✅ **扩展性强** - 插件系统、工作流引擎
4. ✅ **现代化 UI** - Vue3 + Vuetify
5. ✅ **AI 集成** - LangChain 支持

### 我们的优势

1. ✅ **简单易用** - 单文件部署，零配置
2. ✅ **实时日志** - SSE 推送，体验更好
3. ✅ **云服务器支持** - 自动检测环境
4. ✅ **无依赖** - 标准库实现
5. ✅ **快速迭代** - 代码量小，易于维护

### 改进方向

**立即行动（v1.2.12）：**
- ✅ 采用 MoviePilot 的 Release Group 列表
- ✅ 使用正则表达式匹配

**中期目标（v1.3.0-v1.4.0）：**
- 🔄 添加识别词系统
- 🔄 集成 cn2an 库
- 🔄 副标题解析

**长期规划（v2.0.0+）：**
- 🔄 可选的前后端分离
- 🔄 插件系统
- 🔄 工作流引擎

---

## 🚀 下一步

要不要我现在就帮你实施 **v1.2.12**？

**改动内容：**
1. 更新 Release Group 列表（从 13 个扩展到 100+）
2. 使用正则表达式匹配（借鉴 MoviePilot 的实现）
3. 添加测试用例

**预计时间：** 10 分钟  
**风险：** 低  
**收益：** 立即提升标题清理效果 🎯
