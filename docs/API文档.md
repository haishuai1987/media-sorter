# Media Renamer v2.8.0 API 文档

## 📋 概述

Media Renamer v2.8.0 提供完整的 RESTful API 和 WebSocket 接口，支持所有核心功能。

**Base URL**: `http://localhost:8090`  
**API Version**: v2.8.0  
**Content-Type**: `application/json`

---

## 🔌 WebSocket 连接

### 连接地址

```
ws://localhost:8090/socket.io/
```

### 事件类型

#### 客户端 → 服务器

| 事件 | 说明 | 参数 |
|------|------|------|
| `connect` | 建立连接 | - |
| `disconnect` | 断开连接 | - |
| `request_progress` | 请求进度更新 | - |

#### 服务器 → 客户端

| 事件 | 说明 | 数据格式 |
|------|------|----------|
| `connected` | 连接成功 | `{message: string}` |
| `progress_update` | 进度更新 | `{current, total, percentage, current_file, message}` |

### 示例代码

```javascript
// 连接 WebSocket
const socket = io();

// 监听连接
socket.on('connected', (data) => {
    console.log('已连接:', data.message);
});

// 监听进度更新
socket.on('progress_update', (data) => {
    console.log(`进度: ${data.percentage}%`);
    console.log(`当前文件: ${data.current_file}`);
    console.log(`已完成: ${data.current}/${data.total}`);
});

// 请求进度
socket.emit('request_progress');
```

---

## 📦 批量处理 API

### 1. 批量处理文件

**POST** `/api/process`

处理多个文件，支持队列管理。

#### 请求参数

```json
{
    "files": ["file1.mkv", "file2.mkv"],
    "template": "movie_default",
    "use_queue": true,
    "priority": "normal"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | array | 是 | 文件名列表 |
| template | string | 否 | 模板名称，默认 movie_default |
| use_queue | boolean | 否 | 是否使用队列，默认 true |
| priority | string | 否 | 优先级：normal/high/low |

#### 响应

```json
{
    "success": true,
    "message": "处理已开始"
}
```

#### 示例

```bash
curl -X POST http://localhost:8090/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "files": ["The.Matrix.1999.1080p.mkv"],
    "template": "movie_default"
  }'
```

---

### 2. 预览处理结果

**POST** `/api/preview`

预览文件处理结果，不实际执行。

#### 请求参数

```json
{
    "files": ["file1.mkv"],
    "template": "movie_default"
}
```

#### 响应

```json
{
    "success": true,
    "data": [
        {
            "original": "The.Matrix.1999.1080p.mkv",
            "new_name": "黑客帝国 (1999)/黑客帝国 (1999) [1080p-BluRay].mkv",
            "info": {
                "title": "黑客帝国",
                "year": 1999,
                "resolution": "1080p"
            }
        }
    ]
}
```

---

### 3. 获取处理状态

**GET** `/api/status`

获取当前处理状态和进度。

#### 响应

```json
{
    "success": true,
    "data": {
        "is_processing": true,
        "current_file": "file1.mkv",
        "progress": 60,
        "total_files": 10,
        "processed_files": 6,
        "results": []
    }
}
```

---

## 🔍 文件识别 API

### 1. 识别单个文件

**POST** `/api/recognize`

识别单个文件的详细信息。

#### 请求参数

```json
{
    "filename": "The.Matrix.1999.1080p.BluRay.x264.mkv",
    "template": "movie_default"
}
```

#### 响应

```json
{
    "success": true,
    "data": {
        "original_name": "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "title": "黑客帝国",
        "year": 1999,
        "resolution": "1080p",
        "video_codec": "x264",
        "source": "BluRay",
        "new_name": "黑客帝国 (1999)/黑客帝国 (1999) [1080p-BluRay].mkv"
    }
}
```

---

## ✏️ 批量编辑 API

### 1. 预览批量编辑

**POST** `/api/batch-edit/preview`

预览批量编辑结果。

#### 请求参数

```json
{
    "files": ["file1.mkv", "file2.mkv"],
    "operation": "add_prefix",
    "params": {
        "prefix": "[1080p]"
    }
}
```

#### 操作类型

| 操作 | 参数 | 说明 |
|------|------|------|
| add_prefix | prefix | 添加前缀 |
| add_suffix | suffix | 添加后缀 |
| replace | find, replace | 替换文本 |
| remove | text | 删除文本 |
| regex_replace | pattern, replace | 正则替换 |
| case_transform | case_type | 大小写转换 |

#### 响应

```json
{
    "success": true,
    "data": [
        {
            "original": "file1.mkv",
            "new_name": "[1080p]file1.mkv"
        }
    ]
}
```

---

### 2. 应用批量编辑

**POST** `/api/batch-edit/apply`

应用批量编辑操作。

#### 请求参数

同预览接口

#### 响应

```json
{
    "success": true,
    "message": "批量编辑完成",
    "data": {
        "total": 2,
        "success": 2,
        "failed": 0
    }
}
```

---

## 📜 历史记录 API

### 1. 获取历史记录

**GET** `/api/history`

获取处理历史记录。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| limit | int | 每页数量，默认 20 |
| offset | int | 偏移量，默认 0 |
| search | string | 搜索关键词 |

#### 响应

```json
{
    "success": true,
    "data": {
        "total": 100,
        "items": [
            {
                "id": 1,
                "original_name": "file1.mkv",
                "new_name": "新文件名.mkv",
                "status": "success",
                "timestamp": "2025-10-23T10:00:00"
            }
        ]
    }
}
```

---

### 2. 清空历史记录

**DELETE** `/api/history`

清空所有历史记录。

#### 响应

```json
{
    "success": true,
    "message": "历史记录已清空"
}
```

---

## ⚙️ 配置管理 API

### 1. 获取配置列表

**GET** `/api/configs`

获取所有保存的配置。

#### 响应

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "默认配置",
            "description": "常用配置",
            "config": {
                "template": "movie_default",
                "priority": "normal"
            },
            "created_at": "2025-10-23T10:00:00"
        }
    ]
}
```

---

### 2. 添加配置

**POST** `/api/configs`

保存新配置。

#### 请求参数

```json
{
    "name": "我的配置",
    "description": "描述",
    "config": {
        "template": "movie_default",
        "priority": "high"
    }
}
```

#### 响应

```json
{
    "success": true,
    "message": "配置已保存",
    "data": {
        "id": 2
    }
}
```

---

### 3. 删除配置

**DELETE** `/api/configs/{id}`

删除指定配置。

#### 响应

```json
{
    "success": true,
    "message": "配置已删除"
}
```

---

### 4. 导出配置

**GET** `/api/configs/export`

导出所有配置为 JSON。

#### 响应

```json
{
    "success": true,
    "data": {
        "configs": [],
        "export_time": "2025-10-23T10:00:00"
    }
}
```

---

### 5. 导入配置

**POST** `/api/configs/import`

导入配置 JSON。

#### 请求参数

```json
{
    "configs": []
}
```

#### 响应

```json
{
    "success": true,
    "message": "配置已导入",
    "data": {
        "imported": 5
    }
}
```

---

## 📝 模板管理 API

### 1. 获取模板列表

**GET** `/api/templates`

获取所有可用模板。

#### 响应

```json
{
    "success": true,
    "data": {
        "movie": [
            {
                "name": "movie_default",
                "format": "{title} ({year})/{title} ({year}) [{resolution}-{source}].{ext}",
                "description": "电影默认模板"
            }
        ],
        "tv": []
    }
}
```

---

### 2. 获取模板详情

**GET** `/api/templates/{name}`

获取指定模板的详细信息。

#### 响应

```json
{
    "success": true,
    "data": {
        "name": "movie_default",
        "format": "{title} ({year})/{title} ({year}) [{resolution}-{source}].{ext}",
        "type": "movie",
        "variables": ["title", "year", "resolution", "source", "ext"]
    }
}
```

---

### 3. 添加自定义模板

**POST** `/api/templates`

添加自定义模板。

#### 请求参数

```json
{
    "name": "my_template",
    "format": "{title} [{year}].{ext}",
    "type": "movie"
}
```

#### 响应

```json
{
    "success": true,
    "message": "模板已添加"
}
```

---

## 📚 识别词管理 API

### 1. 获取识别词列表

**GET** `/api/words`

获取所有识别词。

#### 响应

```json
{
    "success": true,
    "data": {
        "block_words": ["sample", "test"],
        "replace_words": {
            "权利的游戏": "权力的游戏"
        }
    }
}
```

---

### 2. 添加识别词

**POST** `/api/words`

添加识别词。

#### 请求参数

```json
{
    "type": "block",
    "word": "sample",
    "replace_with": ""
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| type | string | 类型：block/replace |
| word | string | 词语 |
| replace_with | string | 替换词（仅 replace 类型） |

#### 响应

```json
{
    "success": true,
    "message": "识别词已添加"
}
```

---

### 3. 删除识别词

**DELETE** `/api/words`

删除识别词。

#### 请求参数

```json
{
    "type": "block",
    "word": "sample"
}
```

#### 响应

```json
{
    "success": true,
    "message": "识别词已删除"
}
```

---

## 📊 统计信息 API

### 获取统计信息

**GET** `/api/stats`

获取系统统计信息。

#### 响应

```json
{
    "success": true,
    "data": {
        "total_processed": 1000,
        "success_count": 950,
        "failed_count": 50,
        "avg_process_time": 1.5,
        "last_process_time": "2025-10-23T10:00:00"
    }
}
```

---

## 🔧 系统信息 API

### 获取系统信息

**GET** `/api/system/info`

获取系统信息。

#### 响应

```json
{
    "success": true,
    "data": {
        "version": "2.8.0",
        "python_version": "3.9.0",
        "platform": "Linux",
        "uptime": 3600
    }
}
```

---

## 📄 静态文件

### 访问前端文件

| 路径 | 说明 |
|------|------|
| `/` | 主页面 |
| `/static/app_v2.js` | 前端 JS |
| `/static/style_v2.css` | 样式表 |
| `/static/i18n.js` | 国际化 |

---

## 🔒 错误处理

### 错误响应格式

```json
{
    "success": false,
    "error": "错误信息"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 接口不存在 |
| 500 | 服务器内部错误 |

---

## 💡 使用示例

### Python 示例

```python
import requests

# 批量处理
response = requests.post('http://localhost:8090/api/process', json={
    'files': ['The.Matrix.1999.1080p.mkv'],
    'template': 'movie_default'
})
print(response.json())

# 获取历史记录
response = requests.get('http://localhost:8090/api/history?limit=10')
print(response.json())
```

### JavaScript 示例

```javascript
// 批量处理
fetch('http://localhost:8090/api/process', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        files: ['The.Matrix.1999.1080p.mkv'],
        template: 'movie_default'
    })
})
.then(res => res.json())
.then(data => console.log(data));

// WebSocket 连接
const socket = io('http://localhost:8090');
socket.on('progress_update', (data) => {
    console.log(`进度: ${data.percentage}%`);
});
```

### cURL 示例

```bash
# 批量处理
curl -X POST http://localhost:8090/api/process \
  -H "Content-Type: application/json" \
  -d '{"files":["file.mkv"],"template":"movie_default"}'

# 获取历史
curl http://localhost:8090/api/history?limit=10

# 添加配置
curl -X POST http://localhost:8090/api/configs \
  -H "Content-Type: application/json" \
  -d '{"name":"test","config":{}}'
```

---

## 📚 相关文档

- [快速开始](./快速开始.md) - 快速上手指南
- [使用手册](./使用手册.md) - 完整功能说明
- [部署手册](./部署手册.md) - 部署指南
- [开发者指南](./开发者指南.md) - 开发文档

---

**API 文档持续更新中！** 🚀
