# 设计文档

## 概述

本设计为媒体库管理器添加Web界面的一键更新功能，允许用户通过点击按钮从GitHub拉取最新代码并自动重启服务。系统支持版本号管理、代理配置、自动重启和错误处理，确保在不同网络环境下都能顺利完成更新。

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Web前端界面                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  版本显示    │  │  更新按钮    │  │  代理设置    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                      Python后端服务                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API端点层                                            │   │
│  │  /api/check-update  /api/update  /api/get-version   │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  更新管理器 (UpdateManager)                          │   │
│  │  - 版本检查  - Git操作  - 代理管理  - 服务重启      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  版本管理器 (VersionManager)                         │   │
│  │  - 读取版本  - 更新版本  - 版本比较                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      外部系统                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Git仓库     │  │  代理服务器  │  │  系统进程    │      │
│  │  (GitHub)    │  │  (可选)      │  │  管理        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生)
- **后端**: Python 3.x, http.server
- **版本控制**: Git
- **进程管理**: subprocess, threading
- **配置存储**: JSON文件

## 组件和接口

### 1. 版本管理器 (VersionManager)

负责版本号的读取、更新和比较。

```python
class VersionManager:
    """版本号管理器"""
    
    VERSION_FILE = 'version.txt'
    
    @staticmethod
    def get_current_version():
        """获取当前版本号"""
        # 从version.txt读取版本号
        # 格式: v1.0.1
        pass
    
    @staticmethod
    def get_remote_version():
        """获取远程最新版本号"""
        # 从GitHub获取最新版本号
        pass
    
    @staticmethod
    def compare_versions(v1, v2):
        """比较两个版本号"""
        # 返回: -1 (v1<v2), 0 (v1==v2), 1 (v1>v2)
        pass
    
    @staticmethod
    def increment_version(version_str, level='patch'):
        """递增版本号"""
        # level: 'major', 'minor', 'patch'
        # v1.0.1 -> v1.0.2 (patch)
        pass
    
    @staticmethod
    def save_version(version_str):
        """保存版本号到文件"""
        pass
```

### 2. 更新管理器 (UpdateManager)

负责执行更新操作，包括Git操作、代理管理和服务重启。

```python
class UpdateManager:
    """系统更新管理器"""
    
    def __init__(self, script_dir, config):
        self.script_dir = script_dir
        self.config = config
        self.use_proxy = False
    
    def check_git_repository(self):
        """检查是否是Git仓库"""
        pass
    
    def check_for_updates(self):
        """检查是否有可用更新"""
        # 返回: {
        #   'has_update': bool,
        #   'current_version': str,
        #   'latest_version': str,
        #   'commits_behind': int
        # }
        pass
    
    def fetch_remote(self, use_proxy=False):
        """获取远程更新"""
        # 使用git fetch
        pass
    
    def pull_updates(self, use_proxy=False):
        """拉取更新"""
        # 使用git pull
        pass
    
    def execute_git_command(self, cmd, use_proxy=False):
        """执行Git命令"""
        # 支持代理配置
        pass
    
    def restart_service(self):
        """重启服务"""
        # 使用stop.sh和start.sh
        pass
    
    def rollback(self):
        """回滚到上一版本"""
        # 使用git reset
        pass
```

### 3. API端点

#### 3.1 GET /api/get-version

获取当前版本信息。

**请求**: 无参数

**响应**:
```json
{
  "success": true,
  "current_version": "v1.0.1",
  "git_commit": "abc123",
  "git_branch": "main"
}
```

#### 3.2 POST /api/check-update

检查是否有可用更新。

**请求**:
```json
{
  "use_proxy": false
}
```

**响应**:
```json
{
  "success": true,
  "has_update": true,
  "current_version": "v1.0.1",
  "latest_version": "v1.0.5",
  "commits_behind": 4,
  "changelog": "修复了若干bug..."
}
```

#### 3.3 POST /api/update

执行系统更新。

**请求**:
```json
{
  "use_proxy": false,
  "auto_restart": true
}
```

**响应**:
```json
{
  "success": true,
  "updated": true,
  "new_version": "v1.0.5",
  "message": "更新成功，服务将在3秒后重启"
}
```

#### 3.4 POST /api/rollback

回滚到上一版本。

**请求**:
```json
{
  "target_version": "v1.0.1"
}
```

**响应**:
```json
{
  "success": true,
  "message": "已回滚到版本 v1.0.1"
}
```

#### 3.5 GET /api/update-history

获取更新历史记录。

**请求**: 无参数

**响应**:
```json
{
  "success": true,
  "history": [
    {
      "version": "v1.0.5",
      "timestamp": "2025-10-19 10:30:00",
      "status": "success",
      "user": "admin"
    }
  ]
}
```

### 4. 前端组件

#### 4.1 版本显示组件

显示当前版本号和状态。

```html
<div class="version-display">
  <span class="version-label">当前版本:</span>
  <span class="version-number">v1.0.1</span>
  <span class="version-status">最新</span>
</div>
```

#### 4.2 更新按钮组件

提供检查更新和立即更新功能。

```html
<div class="update-controls">
  <button id="checkUpdateBtn" class="btn-primary">检查更新</button>
  <button id="updateBtn" class="btn-success" disabled>立即更新</button>
  <div class="update-status"></div>
</div>
```

#### 4.3 代理配置组件

允许用户配置代理服务器。

```html
<div class="proxy-config">
  <label>
    <input type="checkbox" id="useProxy"> 使用代理
  </label>
  <input type="text" id="proxyUrl" placeholder="http://proxy.example.com:7890">
  <button id="saveProxyBtn">保存</button>
</div>
```

#### 4.4 更新历史组件

显示最近的更新记录。

```html
<div class="update-history">
  <h3>更新历史</h3>
  <ul id="historyList">
    <!-- 动态生成 -->
  </ul>
</div>
```

## 数据模型

### 1. 版本信息 (version.txt)

```
v1.0.1
```

格式: `v主版本.次版本.修订号`

### 2. 配置文件 (config.json)

```json
{
  "tmdb_api_key": "...",
  "tmdb_proxy": "...",
  "douban_cookie": "...",
  "update_proxy": "http://proxy.example.com:7890",
  "update_proxy_enabled": false,
  "auto_restart_after_update": true
}
```

### 3. 更新历史 (update_history.json)

```json
{
  "updates": [
    {
      "version": "v1.0.5",
      "timestamp": "2025-10-19T10:30:00",
      "status": "success",
      "user": "admin",
      "ip": "192.168.1.100",
      "commits": 4,
      "error": null
    }
  ]
}
```

## 错误处理

### 1. 网络错误

**场景**: 无法连接到GitHub

**处理策略**:
1. 检测网络连接失败
2. 如果未启用代理，提示用户配置代理
3. 如果已启用代理，自动尝试使用代理重试
4. 重试3次后仍失败，显示详细错误信息

**错误消息**:
```
无法连接到GitHub，请检查网络连接。
建议: 配置代理服务器后重试。
```

### 2. Git仓库错误

**场景**: 本地有未提交的修改

**处理策略**:
1. 检测到未提交的修改
2. 阻止更新操作
3. 提供"重置本地修改"按钮
4. 用户确认后执行 `git reset --hard`

**错误消息**:
```
检测到本地有未提交的修改，无法更新。
建议: 点击"重置本地修改"按钮清除修改后重试。
```

### 3. 权限错误

**场景**: 没有写入权限

**处理策略**:
1. 检测权限错误
2. 显示详细的权限信息
3. 提供解决方案指引

**错误消息**:
```
权限不足，无法更新文件。
解决方案: 请使用sudo权限运行服务，或修改文件权限。
```

### 4. 服务重启失败

**场景**: 更新成功但重启失败

**处理策略**:
1. 记录重启失败日志
2. 保持当前服务运行
3. 提示用户手动重启

**错误消息**:
```
更新成功，但自动重启失败。
请手动执行: ./stop.sh && ./start.sh
```

## 测试策略

### 1. 单元测试

- **VersionManager测试**
  - 测试版本号解析
  - 测试版本号比较
  - 测试版本号递增
  - 测试版本号保存和读取

- **UpdateManager测试**
  - 测试Git仓库检查
  - 测试更新检查逻辑
  - 测试Git命令执行
  - 测试代理配置

### 2. 集成测试

- **更新流程测试**
  - 测试完整的更新流程（检查 -> 拉取 -> 重启）
  - 测试代理切换功能
  - 测试错误恢复机制

- **API测试**
  - 测试所有API端点
  - 测试错误响应
  - 测试并发请求

### 3. 端到端测试

- **用户场景测试**
  - 正常更新流程
  - 使用代理更新
  - 更新失败回滚
  - 查看更新历史

### 4. 网络环境测试

- 直连GitHub环境
- 需要代理的环境
- 网络不稳定环境
- 完全离线环境

## 安全考虑

### 1. 权限验证

- 更新操作需要管理员权限
- 使用session或token验证用户身份
- 记录所有更新操作的审计日志

### 2. 代码完整性

- 验证Git提交签名（可选）
- 检查远程仓库URL是否被篡改
- 更新前备份关键文件

### 3. 配置安全

- 代理配置加密存储
- 敏感信息不记录到日志
- 限制配置文件访问权限

### 4. 操作限制

- 同一时间只允许一个更新操作
- 更新操作超时限制（60秒）
- 频率限制（防止滥用）

## 性能优化

### 1. 缓存策略

- 缓存版本检查结果（5分钟）
- 缓存Git状态信息
- 减少不必要的网络请求

### 2. 异步操作

- 更新操作在后台线程执行
- 使用WebSocket推送更新进度（可选）
- 避免阻塞主服务

### 3. 资源管理

- 限制Git操作的内存使用
- 清理临时文件
- 控制日志文件大小

## 部署考虑

### 1. 初始化

创建version.txt文件：
```bash
echo "v1.0.0" > version.txt
```

### 2. 上传脚本修改

修改upload-to-github.bat，自动递增版本号：
```batch
@echo off
REM 读取当前版本
set /p VERSION=<version.txt
REM 递增版本号（需要Python脚本辅助）
python increment_version.py
REM 提交并推送
git add .
git commit -m "Update to %VERSION%"
git push
```

### 3. 服务重启脚本

确保stop.sh和start.sh正确配置：
```bash
# stop.sh
#!/bin/bash
PID_FILE="media-renamer.pid"
if [ -f "$PID_FILE" ]; then
    kill $(cat $PID_FILE)
    rm $PID_FILE
fi

# start.sh
#!/bin/bash
nohup python3 app.py > media-renamer.log 2>&1 &
echo $! > media-renamer.pid
```

## 监控和日志

### 1. 更新日志

记录所有更新操作：
- 时间戳
- 操作用户
- 版本变化
- 执行结果
- 错误信息

### 2. 性能监控

- 更新操作耗时
- 网络请求延迟
- 服务重启时间

### 3. 告警机制

- 更新失败告警
- 服务重启失败告警
- 版本不一致告警

## 未来扩展

### 1. 自动更新

- 定时检查更新
- 自动在空闲时段更新
- 更新通知推送

### 2. 版本管理增强

- 支持多分支切换
- 支持回滚到任意版本
- 版本变更日志展示

### 3. 更新策略

- 灰度更新
- A/B测试
- 蓝绿部署

### 4. 备份恢复

- 更新前自动备份
- 一键恢复功能
- 备份文件管理
