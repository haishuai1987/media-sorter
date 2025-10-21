# 媒体整理平台发展路线图 🚀

## 🎯 愿景

打造一个**简单、强大、易用**的媒体整理平台，融合 NASTool 和 MoviePilot 的优势，同时保持我们的独特性。

**核心理念：**
- ✅ **简单优先** - 单文件部署，零配置启动
- ✅ **渐进增强** - 从基础功能到高级功能，逐步演进
- ✅ **用户友好** - 实时反馈，清晰的错误提示
- ✅ **云原生** - 自动适配本地/云服务器环境

---

## 📊 竞品分析总结

### NASTool 的优势
- ✅ 100+ Release Group 识别
- ✅ 完整的识别词系统（屏蔽/替换/偏移）
- ✅ 副标题解析（"第7季"、"全12集"）
- ✅ 中文数字转换（cn2an）
- ✅ 成熟的文件转移逻辑

### MoviePilot 的优势
- ✅ 前后端分离架构
- ✅ 现代化 UI（Vue3 + Vuetify）
- ✅ 插件系统
- ✅ 工作流引擎
- ✅ AI 集成（LangChain）
- ✅ 多下载器支持

### 我们的优势
- ✅ **单文件部署** - 无需复杂配置
- ✅ **实时日志推送** - SSE 技术
- ✅ **云服务器自动检测** - 智能环境适配
- ✅ **零依赖** - 标准库实现
- ✅ **快速迭代** - 代码量小，易维护

---

## 🏗️ 架构设计

### 阶段 1: 单文件架构（当前 - v1.5）

**保持简单，逐步增强**

```
media-renamer/
├── app.py                    # 单文件核心（7000+ 行）
├── index.html                # 内嵌前端
├── public/                   # 静态资源
│   ├── style.css
│   └── index.html
├── config/                   # 配置文件
│   └── custom_words.json     # 自定义识别词
├── docs/                     # 文档
└── version.txt               # 版本号
```

**特点：**
- ✅ 一键启动：`python app.py`
- ✅ 零依赖（标准库）
- ✅ 适合个人用户

### 阶段 2: 模块化架构（v2.0 - v2.5）

**保持单文件部署，内部模块化**

```
media-renamer/
├── app.py                    # 主入口（精简到 500 行）
├── core/                     # 核心模块（可选导入）
│   ├── meta/                 # 元数据识别
│   │   ├── parser.py         # 标题解析
│   │   ├── releasegroup.py   # 制作组识别
│   │   ├── words.py          # 识别词处理
│   │   └── subtitle.py       # 副标题解析
│   ├── organizer.py          # 文件整理
│   ├── tmdb.py               # TMDB API
│   ├── douban.py             # 豆瓣 API
│   └── cloud115.py           # 115 网盘
├── plugins/                  # 插件系统（可选）
│   ├── __init__.py
│   ├── auto_subtitle.py      # 自动字幕
│   └── notification.py       # 通知插件
├── web/                      # Web 界面
│   ├── static/               # 静态资源
│   └── templates/            # 模板
└── config/
    ├── config.json           # 主配置
    └── custom_words.json     # 识别词
```

**部署方式：**
```bash
# 方式 1: 单文件模式（向后兼容）
python app.py

# 方式 2: 模块化模式（推荐）
python -m media_renamer
```

### 阶段 3: 前后端分离（v3.0+）

**可选的前后端分离，保持单文件部署选项**

```
media-renamer/
├── backend/                  # 后端（Python）
│   ├── app.py               # FastAPI 入口
│   ├── core/                # 核心模块
│   ├── api/                 # REST API
│   └── requirements.txt     # 依赖（可选）
├── frontend/                 # 前端（Vue3）
│   ├── src/
│   ├── dist/                # 构建产物
│   └── package.json
└── standalone/               # 单文件版本（向后兼容）
    └── app.py               # 包含前端的单文件版本
```

**部署选项：**
```bash
# 选项 1: 单文件模式（零依赖）
python standalone/app.py

# 选项 2: 标准模式（推荐）
cd backend && python app.py

# 选项 3: Docker 模式
docker run -d media-renamer
```

---

## 🗓️ 详细路线图

### 🎯 v1.2.12 - Release Group 增强（本周）

**目标：** 立即提升标题清理效果

**借鉴：** NASTool 的 Release Group 列表

**改动：**
```python
# 1. 更新 Release Group 列表（13 → 100+）
RELEASE_GROUPS = {
    "chdbits": ['CHD(?:Bits|PAD|(?:|HK)TV|WEB)', 'StBOX', 'OneHD', ...],
    "hdchina": ['HDC(?:hina|TV)', 'k9611', 'tudou', ...],
    # ... 完整列表
}

# 2. 使用正则表达式匹配
def remove_release_group(title):
    pattern = '|'.join(all_groups)
    regex = re.compile(
        r"(?<=[-@\[￡【&])(?:" + pattern + r")(?=[@.\s\]\[】&])",
        re.IGNORECASE
    )
    return regex.sub('', title)
```

**预计时间：** 1 天  
**风险：** 低  
**收益：** 立即见效

---

### 🎯 v1.3.0 - 识别词系统（下周）

**目标：** 支持自定义识别词

**借鉴：** NASTool 的识别词系统

**功能：**
1. **屏蔽词** - 移除不需要的内容
   ```
   "大神版" → 移除
   ```

2. **替换词** - 修正标题
   ```
   "密室大逃脱大神版" => "密室大逃脱 大神版"
   ```

3. **集偏移** - 调整集数
   ```
   "EP <> >> EP+10"
   "某剧 EP05" → "某剧 EP15"
   ```

**实现：**
```python
class CustomWords:
    def __init__(self):
        self.words = self.load_words()
    
    def load_words(self):
        """从 config/custom_words.json 加载"""
        if os.path.exists('config/custom_words.json'):
            with open('config/custom_words.json', 'r') as f:
                return json.load(f)
        return []
    
    def process(self, title):
        """处理标题"""
        for word in self.words:
            if word['type'] == 'block':
                # 屏蔽词
                title = title.replace(word['pattern'], '')
            elif word['type'] == 'replace':
                # 替换词
                title = title.replace(word['old'], word['new'])
            elif word['type'] == 'offset':
                # 集偏移
                title = self.episode_offset(title, word)
        return title
```

**Web 界面：**
```html
<!-- 识别词管理页面 -->
<div class="custom-words">
    <h3>自定义识别词</h3>
    <button onclick="addWord()">添加识别词</button>
    
    <table>
        <tr>
            <th>类型</th>
            <th>规则</th>
            <th>操作</th>
        </tr>
        <tr>
            <td>屏蔽词</td>
            <td>大神版</td>
            <td><button>删除</button></td>
        </tr>
    </table>
</div>
```

**预计时间：** 3 天  
**风险：** 中  
**收益：** 大幅提升灵活性

---

### 🎯 v1.4.0 - 副标题解析（2周后）

**目标：** 支持中文副标题解析

**借鉴：** NASTool 的副标题解析 + cn2an 库

**功能：**
- "第七季" → season=7
- "全12集" → total_episodes=12
- "第1-3季" → begin_season=1, end_season=3

**依赖：**
```bash
# 首次引入外部依赖
pip install cn2an
```

**实现：**
```python
import cn2an

class SubtitleParser:
    def parse(self, subtitle):
        """解析副标题"""
        result = {}
        
        # 第X季
        season_match = re.search(
            r"(?<!全\s*|共\s*)[第\s]+([0-9一二三四五六七八九十S\-]+)\s*季",
            subtitle
        )
        if season_match:
            season_str = season_match.group(1)
            result['season'] = cn2an.cn2an(season_str, mode='smart')
        
        # 全X集
        episode_match = re.search(
            r"[全共]\s*([0-9一二三四五六七八九十百零]+)\s*集",
            subtitle
        )
        if episode_match:
            episode_str = episode_match.group(1)
            result['total_episodes'] = cn2an.cn2an(episode_str, mode='smart')
        
        return result
```

**配置选项：**
```json
{
  "subtitle_parsing": {
    "enabled": true,
    "use_cn2an": true  // 是否使用 cn2an（需要安装）
  }
}
```

**预计时间：** 2 天  
**风险：** 低（可选依赖）  
**收益：** 提升中文内容识别

---

### 🎯 v1.5.0 - 插件系统基础（1个月后）

**目标：** 支持简单的插件扩展

**借鉴：** MoviePilot 的插件系统（简化版）

**架构：**
```python
# plugins/__init__.py
class Plugin:
    """插件基类"""
    
    def __init__(self):
        self.name = ""
        self.version = ""
        self.author = ""
    
    def on_file_organized(self, file_info):
        """文件整理完成后的钩子"""
        pass
    
    def on_metadata_fetched(self, metadata):
        """元数据获取后的钩子"""
        pass

# plugins/auto_subtitle.py
class AutoSubtitlePlugin(Plugin):
    """自动字幕插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "自动字幕"
        self.version = "1.0.0"
    
    def on_file_organized(self, file_info):
        """文件整理后自动下载字幕"""
        # 调用字幕 API
        pass
```

**插件管理：**
```python
class PluginManager:
    def __init__(self):
        self.plugins = []
    
    def load_plugins(self):
        """加载插件"""
        for file in os.listdir('plugins'):
            if file.endswith('.py') and file != '__init__.py':
                module = importlib.import_module(f'plugins.{file[:-3]}')
                # 查找 Plugin 子类
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Plugin):
                        self.plugins.append(obj())
    
    def trigger(self, event, *args, **kwargs):
        """触发事件"""
        for plugin in self.plugins:
            method = getattr(plugin, event, None)
            if method:
                method(*args, **kwargs)
```

**内置插件：**
1. **自动字幕** - 整理后自动下载字幕
2. **通知推送** - 完成后发送通知
3. **重复检测** - 检测重复文件
4. **硬链接管理** - 自动创建硬链接

**预计时间：** 5 天  
**风险：** 中  
**收益：** 大幅提升扩展性

---

### 🎯 v2.0.0 - 模块化重构（2个月后）

**目标：** 内部模块化，保持单文件部署

**改动：**
1. **拆分 app.py** - 从 7000 行拆分到 500 行
2. **核心模块独立** - meta/、organizer.py 等
3. **可选导入** - 按需加载模块
4. **向后兼容** - 保持单文件部署选项

**目录结构：**
```
media-renamer/
├── app.py                    # 主入口（500 行）
├── core/                     # 核心模块
│   ├── __init__.py
│   ├── meta/                 # 元数据识别
│   ├── organizer.py          # 文件整理
│   ├── tmdb.py               # TMDB
│   └── douban.py             # 豆瓣
├── plugins/                  # 插件
├── web/                      # Web 界面
└── standalone.py             # 单文件版本（打包所有模块）
```

**部署方式：**
```bash
# 方式 1: 单文件（向后兼容）
python standalone.py

# 方式 2: 模块化（推荐）
python app.py
```

**打包脚本：**
```python
# build_standalone.py
def build_standalone():
    """将所有模块打包成单文件"""
    with open('standalone.py', 'w') as f:
        # 1. 写入 app.py
        f.write(open('app.py').read())
        
        # 2. 写入所有模块
        for module in ['core/meta/parser.py', 'core/organizer.py', ...]:
            f.write(f"\n# === {module} ===\n")
            f.write(open(module).read())
```

**预计时间：** 2 周  
**风险：** 高（大规模重构）  
**收益：** 代码可维护性大幅提升

---

### 🎯 v2.5.0 - 工作流引擎（3个月后）

**目标：** 支持自定义工作流

**借鉴：** MoviePilot 的工作流引擎（简化版）

**功能：**
```yaml
# workflows/auto_organize.yaml
name: 自动整理工作流
trigger:
  - type: file_added
    path: /downloads

steps:
  - name: 识别元数据
    action: recognize_metadata
    
  - name: 查询 TMDB
    action: query_tmdb
    
  - name: 整理文件
    action: organize_file
    params:
      target_dir: /media
      
  - name: 发送通知
    action: send_notification
    params:
      message: "文件整理完成"
```

**实现：**
```python
class WorkflowEngine:
    def __init__(self):
        self.workflows = self.load_workflows()
    
    def load_workflows(self):
        """加载工作流"""
        workflows = []
        for file in os.listdir('workflows'):
            if file.endswith('.yaml'):
                with open(f'workflows/{file}') as f:
                    workflows.append(yaml.safe_load(f))
        return workflows
    
    def execute(self, workflow, context):
        """执行工作流"""
        for step in workflow['steps']:
            action = self.get_action(step['action'])
            result = action(context, step.get('params', {}))
            context.update(result)
        return context
```

**预计时间：** 1 周  
**风险：** 中  
**收益：** 灵活性大幅提升

---

### 🎯 v3.0.0 - 前后端分离（6个月后）

**目标：** 现代化 Web 界面

**借鉴：** MoviePilot 的前后端架构

**技术栈：**
- **后端：** FastAPI（可选，保持标准库版本）
- **前端：** Vue3 + Vuetify
- **部署：** 保持单文件选项

**架构：**
```
media-renamer/
├── backend/                  # 后端
│   ├── app.py               # FastAPI 入口
│   ├── core/                # 核心模块
│   └── api/                 # REST API
├── frontend/                 # 前端
│   ├── src/
│   │   ├── views/           # 页面
│   │   ├── components/      # 组件
│   │   └── App.vue
│   └── dist/                # 构建产物
└── standalone/               # 单文件版本
    └── app.py               # 包含前端的单文件
```

**API 设计：**
```python
# backend/api/organize.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/organize")
async def organize_files(request: OrganizeRequest):
    """整理文件"""
    return {"status": "success"}

@router.get("/api/metadata/{tmdb_id}")
async def get_metadata(tmdb_id: int):
    """获取元数据"""
    return {"title": "...", "year": 2024}
```

**前端页面：**
```vue
<!-- frontend/src/views/Dashboard.vue -->
<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>本地整理</v-card-title>
          <v-card-text>
            <v-file-input label="选择文件夹"></v-file-input>
            <v-btn @click="organize">开始整理</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const organize = async () => {
  const response = await axios.post('/api/organize', {
    source_dir: '/downloads'
  })
  console.log(response.data)
}
</script>
```

**预计时间：** 1 个月  
**风险：** 高  
**收益：** 用户体验大幅提升

---

## 🎨 UI/UX 改进路线

### v1.x - 渐进式改进

**当前（v1.2.11）：**
```html
<!-- 简单的表单界面 -->
<form>
  <input type="text" placeholder="源目录">
  <button>开始整理</button>
</form>
```

**v1.3.0 - 添加识别词管理：**
```html
<!-- 新增识别词管理页面 -->
<div class="tab-content" id="custom-words">
  <h3>自定义识别词</h3>
  <table>
    <tr>
      <th>类型</th>
      <th>规则</th>
      <th>操作</th>
    </tr>
  </table>
</div>
```

**v1.5.0 - 添加插件管理：**
```html
<!-- 插件管理页面 -->
<div class="plugins">
  <div class="plugin-card">
    <h4>自动字幕</h4>
    <p>整理后自动下载字幕</p>
    <button>启用</button>
  </div>
</div>
```

### v2.x - 现代化界面

**v2.0.0 - 响应式设计：**
- ✅ 移动端适配
- ✅ 暗色模式
- ✅ 卡片式布局

**v2.5.0 - 可视化工作流：**
- ✅ 拖拽式工作流编辑器
- ✅ 实时预览
- ✅ 流程图展示

### v3.x - Material Design

**v3.0.0 - Vue3 + Vuetify：**
- ✅ Material Design 3
- ✅ 动画效果
- ✅ PWA 支持

---

## 📦 部署方式演进

### v1.x - 单文件部署

```bash
# 下载单文件
wget https://github.com/xxx/media-renamer/releases/download/v1.2.12/app.py

# 运行
python app.py

# 访问
http://localhost:8090
```

### v2.x - 模块化部署

```bash
# 克隆仓库
git clone https://github.com/xxx/media-renamer

# 运行
python app.py

# 或者使用单文件版本
python standalone.py
```

### v3.x - 多种部署方式

```bash
# 方式 1: 单文件（零依赖）
python standalone.py

# 方式 2: 标准部署
pip install -r requirements.txt
python app.py

# 方式 3: Docker
docker run -d -p 8090:8090 media-renamer

# 方式 4: Docker Compose
docker-compose up -d
```

---

## 🔧 技术债务管理

### 立即处理（v1.2.12）
- ✅ 更新 Release Group 列表
- ✅ 使用正则表达式匹配

### 短期处理（v1.3-v1.5）
- 🔄 添加单元测试
- 🔄 代码注释完善
- 🔄 错误处理优化

### 中期处理（v2.0）
- 🔄 模块化重构
- 🔄 性能优化
- 🔄 日志系统改进

### 长期处理（v3.0）
- 🔄 前后端分离
- 🔄 API 文档
- 🔄 国际化支持

---

## 📊 成功指标

### 用户指标
- **下载量：** GitHub Releases 下载次数
- **Star 数：** GitHub Stars
- **活跃用户：** 月活跃用户数

### 技术指标
- **代码质量：** 测试覆盖率 > 80%
- **性能：** 整理 1000 个文件 < 5 分钟
- **稳定性：** 崩溃率 < 0.1%

### 社区指标
- **Issue 响应时间：** < 24 小时
- **PR 合并时间：** < 7 天
- **文档完整度：** 100%

---

## 🎯 下一步行动

### 本周（v1.2.12）
1. ✅ 更新 Release Group 列表
2. ✅ 使用正则表达式匹配
3. ✅ 添加测试用例
4. ✅ 更新文档

### 下周（v1.3.0）
1. 🔄 设计识别词数据结构
2. 🔄 实现识别词处理逻辑
3. 🔄 添加 Web 管理界面
4. 🔄 编写使用文档

### 本月（v1.4.0）
1. 🔄 集成 cn2an 库
2. 🔄 实现副标题解析
3. 🔄 添加配置选项
4. 🔄 性能测试

---

## 💡 总结

**我们的定位：**
- 🎯 **简单易用** - 比 NASTool 和 MoviePilot 更简单
- 🎯 **功能强大** - 融合两者的优势
- 🎯 **渐进增强** - 从零依赖到可选依赖
- 🎯 **保持独特** - 实时日志、云服务器支持

**竞争优势：**
1. ✅ **零配置启动** - 下载即用
2. ✅ **实时反馈** - SSE 日志推送
3. ✅ **云原生** - 自动环境检测
4. ✅ **渐进式** - 从简单到复杂

**发展方向：**
- **短期（3个月）：** 完善核心功能（识别词、副标题、插件）
- **中期（6个月）：** 模块化重构，工作流引擎
- **长期（1年）：** 前后端分离，现代化 UI

---

## 🚀 准备好了吗？

要不要我现在就帮你开始 **v1.2.12** 的实施？

**第一步：** 更新 Release Group 列表  
**第二步：** 使用正则表达式匹配  
**第三步：** 添加测试用例  

**预计时间：** 1 天  
**立即见效！** 🎯
