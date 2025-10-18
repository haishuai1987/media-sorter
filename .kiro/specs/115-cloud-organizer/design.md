# 设计文档 - 115网盘整理模块

## 概述

本设计为媒体库管理器添加115网盘云端整理功能，通过115 API实现纯云端操作。系统架构采用模块化设计，将原有功能重构为"本地整理模块"，新增"115网盘整理模块"，两者共享核心识别逻辑，独立处理文件操作。

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Web前端界面                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  模块切换    │  │  本地整理    │  │  115整理     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                      Python后端服务                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API路由层                                            │   │
│  │  /api/local/*  /api/cloud/*  /api/common/*          │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  核心服务层（共享）                                   │   │
│  │  - MediaParser (文件名解析)                          │   │
│  │  - TMDBHelper (TMDB查询)                             │   │
│  │  - DoubanHelper (豆瓣查询)                           │   │
│  │  - CategoryManager (分类管理)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────┐  │  ┌─────────────────────────┐   │
│  │  本地模块           │  │  │  115网盘模块            │   │
│  │  - LocalScanner     │  │  │  - Cloud115API          │   │
│  │  - LocalRenamer     │  │  │  - CloudScanner         │   │
│  │  - LocalMover       │  │  │  - CloudRenamer         │   │
│  │  - LocalCleaner     │  │  │  - CloudMover           │   │
│  └─────────────────────┘  │  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      外部系统                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  本地文件系统│  │  115网盘API  │  │  TMDB/豆瓣   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生)
- **后端**: Python 3.x, http.server
- **115 API**: HTTP/HTTPS RESTful API
- **加密**: AES-256 (Cookie加密)
- **缓存**: 内存缓存 + 文件缓存

## 组件和接口

### 1. Cloud115API 类

115网盘API封装类，负责所有与115网盘的交互。

```python
class Cloud115API:
    """115网盘API封装"""
    
    BASE_URL = 'https://webapi.115.com/files'
    
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = self._create_session()
    
    def _create_session(self):
        """创建HTTP会话"""
        pass
    
    def verify_cookie(self):
        """验证Cookie有效性
        
        Returns:
            (valid: bool, user_info: dict)
        """
        pass
    
    def list_files(self, folder_id='0', offset=0, limit=1000):
        """列出文件夹内容
        
        Args:
            folder_id: 文件夹ID，'0'表示根目录
            offset: 偏移量
            limit: 返回数量限制
        
        Returns:
            {
                'files': [
                    {
                        'fid': '文件ID',
                        'cid': '父文件夹ID',
                        'name': '文件名',
                        'size': 文件大小,
                        'is_dir': True/False,
                        'time': '修改时间'
                    }
                ],
                'count': 总数量
            }
        """
        pass
    
    def rename_file(self, file_id, new_name):
        """重命名文件
        
        Args:
            file_id: 文件ID
            new_name: 新文件名
        
        Returns:
            (success: bool, message: str)
        """
        pass
    
    def move_file(self, file_id, target_folder_id):
        """移动文件
        
        Args:
            file_id: 文件ID
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success: bool, message: str)
        """
        pass
    
    def delete_file(self, file_id):
        """删除文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            (success: bool, message: str)
        """
        pass
    
    def create_folder(self, parent_id, folder_name):
        """创建文件夹
        
        Args:
            parent_id: 父文件夹ID
            folder_name: 文件夹名称
        
        Returns:
            (success: bool, folder_id: str, message: str)
        """
        pass
    
    def search_files(self, keyword, folder_id='0'):
        """搜索文件
        
        Args:
            keyword: 搜索关键词
            folder_id: 搜索范围文件夹ID
        
        Returns:
            list of files
        """
        pass
    
    def get_folder_tree(self, folder_id='0', max_depth=5):
        """获取文件夹树结构
        
        Args:
            folder_id: 起始文件夹ID
            max_depth: 最大深度
        
        Returns:
            树形结构数据
        """
        pass
```

### 2. CloudScanner 类

云端文件扫描器，负责扫描115网盘文件。

```python
class CloudScanner:
    """115网盘文件扫描器"""
    
    def __init__(self, api: Cloud115API):
        self.api = api
        self.media_extensions = MEDIA_EXTENSIONS
        self.subtitle_extensions = SUBTITLE_EXTENSIONS
    
    def scan_folder(self, folder_id, recursive=True):
        """扫描文件夹
        
        Args:
            folder_id: 文件夹ID
            recursive: 是否递归扫描
        
        Returns:
            {
                'media_files': [],
                'subtitle_files': [],
                'unsupported_files': [],
                'total_size': 0
            }
        """
        pass
    
    def filter_media_files(self, files):
        """过滤媒体文件"""
        pass
    
    def group_files_by_folder(self, files):
        """按文件夹分组"""
        pass
```

### 3. CloudRenamer 类

云端文件重命名器。

```python
class CloudRenamer:
    """115网盘文件重命名器"""
    
    def __init__(self, api: Cloud115API, parser: MediaParser):
        self.api = api
        self.parser = parser
    
    def rename_file(self, file_info, new_name):
        """重命名单个文件"""
        pass
    
    def batch_rename(self, files, template):
        """批量重命名"""
        pass
    
    def preview_rename(self, files):
        """预览重命名结果"""
        pass
```

### 4. CloudMover 类

云端文件移动器。

```python
class CloudMover:
    """115网盘文件移动器"""
    
    def __init__(self, api: Cloud115API):
        self.api = api
    
    def move_file(self, file_id, target_folder_id):
        """移动单个文件"""
        pass
    
    def batch_move(self, files, target_folder_id):
        """批量移动"""
        pass
    
    def create_category_structure(self, base_folder_id, categories):
        """创建分类文件夹结构"""
        pass
    
    def ensure_folder_exists(self, parent_id, folder_name):
        """确保文件夹存在，不存在则创建"""
        pass
```

### 5. API端点

#### 5.1 POST /api/cloud/verify-cookie

验证115网盘Cookie。

**请求**:
```json
{
  "cookie": "115网盘Cookie字符串"
}
```

**响应**:
```json
{
  "success": true,
  "user_info": {
    "user_id": "123456",
    "username": "用户名",
    "space_used": 1234567890,
    "space_total": 10737418240
  }
}
```

#### 5.2 POST /api/cloud/list-folders

列出文件夹内容。

**请求**:
```json
{
  "folder_id": "0",
  "offset": 0,
  "limit": 100
}
```

**响应**:
```json
{
  "success": true,
  "folders": [
    {
      "id": "folder_id",
      "name": "文件夹名",
      "file_count": 10,
      "size": 1234567
    }
  ],
  "files": [
    {
      "id": "file_id",
      "name": "文件名.mkv",
      "size": 1234567890,
      "type": "media"
    }
  ]
}
```

#### 5.3 POST /api/cloud/scan

扫描指定文件夹。

**请求**:
```json
{
  "folder_id": "folder_id",
  "recursive": true
}
```

**响应**:
```json
{
  "success": true,
  "media_files": [],
  "subtitle_files": [],
  "total_count": 100,
  "total_size": 12345678900
}
```

#### 5.4 POST /api/cloud/smart-organize

智能整理（重命名+分类+移动）。

**请求**:
```json
{
  "folder_id": "source_folder_id",
  "target_folder_id": "target_folder_id",
  "auto_dedupe": true,
  "conflict_strategy": "auto"
}
```

**响应**:
```json
{
  "success": true,
  "processed": 50,
  "renamed": 45,
  "moved": 45,
  "deleted": 5,
  "errors": []
}
```

#### 5.5 POST /api/cloud/get-history

获取操作历史。

**请求**:
```json
{
  "limit": 100,
  "offset": 0
}
```

**响应**:
```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2025-10-19 10:30:00",
      "operation": "rename",
      "file_name": "old_name.mkv",
      "new_name": "new_name.mkv",
      "status": "success"
    }
  ]
}
```

## 数据模型

### 1. 115网盘配置 (config.json)

```json
{
  "cloud_115": {
    "cookie": "加密后的Cookie",
    "cookie_expires": "2025-12-31",
    "default_source_folder": "folder_id",
    "default_movie_folder": "folder_id",
    "default_tv_folder": "folder_id",
    "auto_dedupe": true,
    "conflict_strategy": "auto"
  }
}
```

### 2. 云端操作历史 (cloud_history.json)

```json
{
  "operations": [
    {
      "id": "uuid",
      "timestamp": "2025-10-19T10:30:00",
      "operation_type": "rename|move|delete",
      "file_id": "file_id",
      "file_name": "原文件名",
      "new_name": "新文件名",
      "folder_id": "文件夹ID",
      "status": "success|failed",
      "error": null
    }
  ]
}
```

### 3. 115 API响应缓存

```python
# 内存缓存结构
cache = {
    'folder_list': {
        'folder_id': {
            'data': {...},
            'timestamp': 1234567890,
            'ttl': 300  # 5分钟
        }
    },
    'file_info': {
        'file_id': {
            'data': {...},
            'timestamp': 1234567890,
            'ttl': 600  # 10分钟
        }
    }
}
```

## 115 API 研究

### API端点（基于逆向工程）

```python
# 基础URL
BASE_URL = 'https://webapi.115.com'

# 主要端点
ENDPOINTS = {
    'user_info': '/user/info',
    'file_list': '/files',
    'file_rename': '/files/batch_rename',
    'file_move': '/files/move',
    'file_delete': '/rb/delete',
    'folder_create': '/files/add',
    'file_search': '/files/search'
}

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Cookie': cookie,
    'Content-Type': 'application/x-www-form-urlencoded'
}
```

### Cookie结构

115网盘Cookie通常包含：
- `UID`: 用户ID
- `CID`: 客户端ID
- `SEID`: 会话ID

### API限制

- **速率限制**: 约100请求/分钟
- **批量操作**: 单次最多50个文件
- **文件名长度**: 最大255字符
- **Cookie有效期**: 约30天

## 错误处理

### 1. Cookie错误

```python
class CookieError(Exception):
    """Cookie相关错误"""
    pass

class CookieExpiredError(CookieError):
    """Cookie过期"""
    pass

class CookieInvalidError(CookieError):
    """Cookie无效"""
    pass
```

### 2. API错误

```python
class APIError(Exception):
    """API调用错误"""
    pass

class RateLimitError(APIError):
    """速率限制"""
    pass

class NetworkError(APIError):
    """网络错误"""
    pass
```

### 3. 重试策略

```python
def retry_with_backoff(func, max_retries=3):
    """指数退避重试"""
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = 2 ** i  # 1s, 2s, 4s
            time.sleep(wait_time)
        except NetworkError:
            if i == max_retries - 1:
                raise
            time.sleep(1)
```

## 安全设计

### 1. Cookie加密

```python
from cryptography.fernet import Fernet

class CookieEncryption:
    """Cookie加密工具"""
    
    def __init__(self, key=None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, cookie):
        """加密Cookie"""
        return self.cipher.encrypt(cookie.encode()).decode()
    
    def decrypt(self, encrypted_cookie):
        """解密Cookie"""
        return self.cipher.decrypt(encrypted_cookie.encode()).decode()
```

### 2. 敏感信息处理

- Cookie只存储加密后的值
- 日志中不记录完整Cookie
- 内存中及时清理Cookie
- 提供Cookie清除功能

## 性能优化

### 1. 缓存策略

- **文件夹列表**: 缓存5分钟
- **文件信息**: 缓存10分钟
- **用户信息**: 缓存30分钟
- **搜索结果**: 不缓存

### 2. 批量操作

- 批量重命名: 50个/批次
- 批量移动: 50个/批次
- 批量删除: 50个/批次

### 3. 并发控制

- 最大并发请求: 5个
- 请求间隔: 100ms
- 超时时间: 30秒

## 测试策略

### 1. 单元测试

- Cloud115API各方法测试
- Cookie加密/解密测试
- 文件名解析测试
- 错误处理测试

### 2. 集成测试

- 完整整理流程测试
- API限流处理测试
- 网络异常恢复测试

### 3. 端到端测试

- 用户登录到整理完成
- 模块切换测试
- 历史记录查询测试

## 部署考虑

### 1. 依赖安装

```bash
pip install cryptography requests
```

### 2. 配置初始化

```python
# 首次使用时生成加密密钥
if not os.path.exists('.encryption_key'):
    key = Fernet.generate_key()
    with open('.encryption_key', 'wb') as f:
        f.write(key)
```

### 3. 数据迁移

- 保持本地模块配置不变
- 新增cloud_115配置节
- 创建cloud_history.json

## 未来扩展

### 1. 其他网盘支持

- 阿里云盘
- 百度网盘
- 天翼云盘

### 2. 高级功能

- 离线下载管理
- 分享链接管理
- 自动备份
- 多账号支持

### 3. 性能增强

- WebSocket实时推送
- 增量同步
- 智能预加载
