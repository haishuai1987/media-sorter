# API 文档

## 概述

本文档描述媒体库文件管理器的所有 API 接口。

---

## 基础信息

**Base URL**: `http://localhost:8000`

**Content-Type**: `application/json`

**请求方法**: `POST`

---

## 文件管理 API

### 1. 扫描文件

**端点**: `/api/scan`

**描述**: 扫描指定目录中的媒体文件

**请求体**:
```json
{
  "folderPath": "/path/to/folder"
}
```

**响应**:
```json
{
  "files": [
    {
      "name": "movie.mkv",
      "path": "/path/to/folder/movie.mkv",
      "size": 1073741824,
      "modified": "2024-01-01 12:00:00"
    }
  ]
}
```

---

### 2. 智能重命名

**端点**: `/api/smart-rename`

**描述**: 智能识别、重命名和分类媒体文件

**请求体**:
```json
{
  "files": [
    {
      "name": "movie.mkv",
      "path": "/path/to/movie.mkv"
    }
  ],
  "basePath": "/path/to/folder",
  "mediaLibraryPath": "/path/to/media",
  "language": "zh",
  "movieOutputPath": "/path/to/movies",
  "tvOutputPath": "/path/to/tv",
  "autoDedupe": true
}
```

**参数说明**:
- `files`: 文件列表
- `basePath`: 待整理目录路径
- `mediaLibraryPath`: 媒体库路径（新配置）
- `language`: 语言偏好（zh/en）
- `movieOutputPath`: 电影输出路径（旧配置，向后兼容）
- `tvOutputPath`: 电视剧输出路径（旧配置，向后兼容）
- `autoDedupe`: 是否启用智能去重

**响应**:
```json
{
  "results": [
    {
      "oldName": "movie.mkv",
      "newName": "电影名 (2021).mkv",
      "oldPath": "/path/to/movie.mkv",
      "newPath": "/path/to/media/电影/动作/电影名 (2021)/电影名 (2021).mkv",
      "category": "动作",
      "type": "movie"
    }
  ],
  "toDelete": [
    {
      "name": "movie.low.mkv",
      "reason": "低质量版本"
    }
  ]
}
```

---

### 3. 重命名文件

**端点**: `/api/rename`

**描述**: 执行文件重命名和移动操作

**请求体**:
```json
{
  "oldPath": "/path/to/old.mkv",
  "newPath": "/path/to/new.mkv"
}
```

**响应**:
```json
{
  "success": true,
  "message": "文件重命名成功"
}
```

---

### 4. 删除文件

**端点**: `/api/delete`

**描述**: 删除指定文件

**请求体**:
```json
{
  "filePath": "/path/to/file.mkv"
}
```

**响应**:
```json
{
  "success": true,
  "message": "文件删除成功"
}
```

---

### 5. 解析文件名

**端点**: `/api/parse-filename`

**描述**: 解析文件名，提取媒体信息

**请求体**:
```json
{
  "filename": "Movie.Name.2021.1080p.BluRay.x264.mkv"
}
```

**响应**:
```json
{
  "title": "Movie Name",
  "year": "2021",
  "resolution": "1080p",
  "source": "BluRay",
  "codec": "x264",
  "type": "movie"
}
```

---

## 媒体库管理 API

### 6. 检测媒体库结构 ✨

**端点**: `/api/detect-media-library`

**描述**: 检测媒体库的目录结构和分类

**请求体**:
```json
{
  "path": "/path/to/media"
}
```

**响应**:
```json
{
  "success": true,
  "movie_dir": "电影",
  "tv_dir": "电视剧",
  "movie_path": "/path/to/media/电影",
  "tv_path": "/path/to/media/电视剧",
  "movie_categories": ["动作", "喜剧", "科幻"],
  "tv_categories": ["美剧", "日剧", "韩剧"]
}
```

**错误响应**:
```json
{
  "error": "路径不存在: /path/to/media"
}
```

---

### 7. 浏览文件夹

**端点**: `/api/browse-folders`

**描述**: 浏览指定路径下的文件夹

**请求体**:
```json
{
  "folderPath": "/path/to/folder"
}
```

**响应**:
```json
{
  "folders": [
    {
      "name": "subfolder",
      "path": "/path/to/folder/subfolder"
    }
  ],
  "parentPath": "/path/to"
}
```

---

### 8. 扫描所有文件

**端点**: `/api/scan-all`

**描述**: 递归扫描目录中的所有媒体文件

**请求体**:
```json
{
  "folderPath": "/path/to/folder"
}
```

**响应**:
```json
{
  "files": [
    {
      "name": "movie.mkv",
      "path": "/path/to/folder/movie.mkv",
      "size": 1073741824
    }
  ]
}
```

---

## 配置管理 API

### 9. 获取设置

**端点**: `/api/get-settings`

**描述**: 获取当前配置

**请求体**:
```json
{}
```

**响应**:
```json
{
  "tmdb_api_key": "your_api_key",
  "tmdb_proxy": "http://proxy:port",
  "douban_cookie": "your_cookie",
  "mediaLibraryPath": "/path/to/media",
  "language": "zh"
}
```

---

### 10. 保存设置

**端点**: `/api/save-settings`

**描述**: 保存配置

**请求体**:
```json
{
  "tmdb_api_key": "your_api_key",
  "tmdb_proxy": "http://proxy:port",
  "douban_cookie": "your_cookie",
  "mediaLibraryPath": "/path/to/media",
  "language": "zh"
}
```

**响应**:
```json
{
  "success": true,
  "message": "设置保存成功"
}
```

---

## 版本管理 API

### 11. 获取版本

**端点**: `/api/get-version`

**描述**: 获取当前版本信息

**请求体**:
```json
{}
```

**响应**:
```json
{
  "version": "1.0.0",
  "commit": "abc123"
}
```

---

### 12. 检查更新

**端点**: `/api/check-update`

**描述**: 检查是否有新版本

**请求体**:
```json
{}
```

**响应**:
```json
{
  "hasUpdate": true,
  "latestVersion": "1.1.0",
  "currentVersion": "1.0.0",
  "updateUrl": "https://github.com/..."
}
```

---

### 13. 执行更新

**端点**: `/api/update`

**描述**: 执行版本更新

**请求体**:
```json
{}
```

**响应**:
```json
{
  "success": true,
  "message": "更新成功"
}
```

---

### 14. 强制更新

**端点**: `/api/force-update`

**描述**: 强制执行版本更新

**请求体**:
```json
{}
```

**响应**:
```json
{
  "success": true,
  "message": "强制更新成功"
}
```

---

### 15. 回滚版本

**端点**: `/api/rollback`

**描述**: 回滚到上一个版本

**请求体**:
```json
{}
```

**响应**:
```json
{
  "success": true,
  "message": "回滚成功"
}
```

---

### 16. 更新历史

**端点**: `/api/update-history`

**描述**: 获取更新历史记录

**请求体**:
```json
{}
```

**响应**:
```json
{
  "history": [
    {
      "version": "1.1.0",
      "date": "2024-01-01",
      "status": "success"
    }
  ]
}
```

---

## 115网盘 API

### 17. 验证Cookie

**端点**: `/api/cloud/verify-cookie`

**描述**: 验证115网盘Cookie

**请求体**:
```json
{
  "cookie": "your_115_cookie"
}
```

**响应**:
```json
{
  "valid": true,
  "username": "用户名"
}
```

---

### 18. 列出文件

**端点**: `/api/cloud/list-files`

**描述**: 列出115网盘文件

**请求体**:
```json
{
  "folderId": "0"
}
```

**响应**:
```json
{
  "files": [
    {
      "name": "file.mkv",
      "id": "123456",
      "size": 1073741824
    }
  ]
}
```

---

### 19. 扫描网盘

**端点**: `/api/cloud/scan`

**描述**: 扫描115网盘目录

**请求体**:
```json
{
  "folderId": "0"
}
```

**响应**:
```json
{
  "files": [
    {
      "name": "file.mkv",
      "id": "123456"
    }
  ]
}
```

---

### 20. 智能整理

**端点**: `/api/cloud/smart-organize`

**描述**: 智能整理115网盘文件

**请求体**:
```json
{
  "files": [
    {
      "name": "file.mkv",
      "id": "123456"
    }
  ],
  "targetFolderId": "789"
}
```

**响应**:
```json
{
  "success": true,
  "results": [
    {
      "oldName": "file.mkv",
      "newName": "电影名 (2021).mkv"
    }
  ]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "error": "错误描述",
  "code": "ERROR_CODE"
}
```

### 常见错误码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误示例

```json
{
  "error": "路径不存在: /invalid/path",
  "code": "PATH_NOT_FOUND"
}
```

---

## 使用示例

### JavaScript

```javascript
// 检测媒体库结构
async function detectMediaLibrary() {
  const response = await fetch('/api/detect-media-library', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: '/path/to/media' })
  });
  
  const data = await response.json();
  console.log(data);
}
```

### Python

```python
import requests

# 检测媒体库结构
response = requests.post(
    'http://localhost:8000/api/detect-media-library',
    json={'path': '/path/to/media'}
)

data = response.json()
print(data)
```

### cURL

```bash
# 检测媒体库结构
curl -X POST http://localhost:8000/api/detect-media-library \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/media"}'
```

---

## 更新日志

### v1.1.0 (2024-01-01)

**新增 API**:
- `/api/detect-media-library` - 检测媒体库结构

**更新 API**:
- `/api/smart-rename` - 添加 `mediaLibraryPath` 和 `language` 参数

**废弃**:
- 无

---

## 技术细节

### 请求限制

- 无速率限制
- 建议单次处理文件数 < 100

### 超时设置

- 默认超时：30秒
- 大文件操作：60秒

### 并发处理

- 支持多个并发请求
- 建议并发数 < 5

---

## 获取帮助

如果遇到问题：
1. 查看 [常见问题](./常见问题.md)
2. 查看 [使用指南](./使用指南.md)
3. 提交 Issue
