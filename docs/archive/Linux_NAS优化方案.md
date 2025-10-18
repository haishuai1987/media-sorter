# Linux/NAS系统优化方案

## 当前系统分析

### 已有的良好设计
✅ 使用 `os.path` 模块（跨平台兼容）
✅ 使用 UTF-8 编码
✅ 使用 Python 3 标准库
✅ 路径处理使用 `os.path.join()`
✅ 使用 `#!/usr/bin/env python3` shebang

### 需要优化的方面

## 1. 路径兼容性优化

### 问题
- 当前代码混用了硬编码路径和动态路径
- 没有处理符号链接（NAS常用）
- 没有处理挂载点权限问题

### 解决方案

#### A. 使用 pathlib（推荐）
```python
from pathlib import Path

# 替代 os.path
file_path = Path(folder_path) / filename
if file_path.is_file():
    ...
```

#### B. 符号链接处理
```python
# 解析符号链接
real_path = os.path.realpath(file_path)
# 或使用 pathlib
real_path = Path(file_path).resolve()
```

#### C. 权限检查
```python
def check_path_permissions(path):
    """检查路径的读写权限"""
    if not os.access(path, os.R_OK):
        raise PermissionError(f"无读取权限: {path}")
    if not os.access(path, os.W_OK):
        raise PermissionError(f"无写入权限: {path}")
```

## 2. 文件系统兼容性

### 问题
- 不同文件系统对文件名的限制不同
- NAS可能使用 ext4, btrfs, ZFS, NTFS 等

### 解决方案

#### A. 文件名清理
```python
def sanitize_filename(filename):
    """清理文件名，确保跨文件系统兼容"""
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度（大多数文件系统限制255字节）
    if len(filename.encode('utf-8')) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext.encode('utf-8')) - 10
        filename = name[:max_name_len] + ext
    
    return filename
```

#### B. 大小写敏感性处理
```python
def case_insensitive_exists(path):
    """检查文件是否存在（不区分大小写）"""
    if os.path.exists(path):
        return True
    
    directory = os.path.dirname(path)
    filename = os.path.basename(path).lower()
    
    if os.path.exists(directory):
        for item in os.listdir(directory):
            if item.lower() == filename:
                return True
    return False
```

## 3. 网络文件系统优化

### 问题
- NFS/SMB/CIFS 挂载可能有延迟
- 网络中断可能导致操作失败

### 解决方案

#### A. 重试机制
```python
import time
from functools import wraps

def retry_on_network_error(max_retries=3, delay=1):
    """网络操作重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OSError, IOError) as e:
                    if attempt < max_retries - 1:
                        print(f"操作失败，{delay}秒后重试... ({attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

@retry_on_network_error(max_retries=3, delay=2)
def safe_rename(old_path, new_path):
    """带重试的文件重命名"""
    os.rename(old_path, new_path)
```

#### B. 增加同步等待时间
```python
# 网络文件系统操作后等待
time.sleep(1.0)  # 从0.3秒增加到1秒
```

## 4. 依赖管理优化

### 创建 requirements.txt
```txt
# 无外部依赖，仅使用Python标准库
# Python >= 3.6
```

### 创建 setup.sh（Linux安装脚本）
```bash
#!/bin/bash
# 自动安装脚本

echo "检查Python版本..."
python3 --version

if [ $? -ne 0 ]; then
    echo "错误: 未找到Python 3"
    exit 1
fi

echo "创建配置文件..."
mkdir -p ~/.media-renamer

echo "设置权限..."
chmod +x app.py

echo "安装完成！"
echo "运行: python3 app.py"
```

## 5. 系统服务化（systemd）

### 创建 media-renamer.service
```ini
[Unit]
Description=Media Renamer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/media-renamer
ExecStart=/usr/bin/python3 /path/to/media-renamer/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 安装服务
```bash
sudo cp media-renamer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable media-renamer
sudo systemctl start media-renamer
```

## 6. Docker支持

### 创建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY app.py .
COPY index.html .

EXPOSE 8090

CMD ["python3", "app.py"]
```

### 创建 docker-compose.yml
```yaml
version: '3'
services:
  media-renamer:
    build: .
    ports:
      - "8090:8090"
    volumes:
      - /path/to/media:/media
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

## 7. 日志系统

### 添加日志记录
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
log_file = '/var/log/media-renamer/app.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
```

## 8. 配置文件支持

### 创建 config.json
```json
{
  "port": 8090,
  "scan_path": "/media/待整理",
  "movie_output": "/media/电影",
  "tv_output": "/media/剧集",
  "tmdb_api_key": "your-api-key",
  "tmdb_proxy": "http://proxy:port",
  "douban_cookie": "your-cookie",
  "network_delay": 1.0,
  "max_retries": 3
}
```

### 读取配置
```python
import json

def load_config():
    config_paths = [
        './config.json',
        os.path.expanduser('~/.media-renamer/config.json'),
        '/etc/media-renamer/config.json'
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return {}  # 返回默认配置
```

## 9. 常见NAS系统适配

### Synology DSM
- 使用 `/volume1/` 作为基础路径
- 支持 Docker
- 可以使用 Task Scheduler 定时运行

### QNAP
- 使用 `/share/` 作为基础路径
- 支持 Container Station (Docker)
- 可以使用 Cron 定时任务

### TrueNAS/FreeNAS
- 使用 `/mnt/` 作为基础路径
- 支持 Jails 或 Docker
- 注意 ZFS 文件系统特性

### Unraid
- 使用 `/mnt/user/` 作为基础路径
- 原生 Docker 支持
- 可以使用 Community Applications

## 10. 性能优化

### A. 批量操作优化
```python
def batch_rename(files, batch_size=10):
    """批量处理文件，避免一次性处理太多"""
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        for file in batch:
            process_file(file)
        time.sleep(0.5)  # 批次间延迟
```

### B. 缓存机制
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_tmdb_info(title, year):
    """缓存TMDB查询结果"""
    return fetch_tmdb_info(title, year)
```

## 11. 安全性增强

### A. 路径验证
```python
def validate_path(path, base_path):
    """验证路径，防止目录遍历攻击"""
    real_path = os.path.realpath(path)
    real_base = os.path.realpath(base_path)
    
    if not real_path.startswith(real_base):
        raise ValueError("非法路径访问")
    
    return real_path
```

### B. 文件大小限制
```python
MAX_FILE_SIZE = 100 * 1024 * 1024 * 1024  # 100GB

def check_file_size(file_path):
    """检查文件大小"""
    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"文件过大: {size / 1024 / 1024 / 1024:.2f}GB")
```

## 12. 监控和健康检查

### 添加健康检查端点
```python
def handle_health_check(self):
    """健康检查接口"""
    self.send_json_response({
        'status': 'healthy',
        'version': '1.3',
        'uptime': time.time() - start_time
    })
```

## 实施优先级

### 高优先级（必须）
1. ✅ 路径兼容性优化
2. ✅ 文件名清理
3. ✅ 权限检查
4. ✅ 重试机制

### 中优先级（推荐）
5. 📋 配置文件支持
6. 📋 日志系统
7. 📋 Docker支持

### 低优先级（可选）
8. 📋 systemd服务
9. 📋 性能优化
10. 📋 监控系统

## 测试建议

### 测试环境
- Ubuntu 20.04/22.04
- Debian 11/12
- CentOS 7/8
- Synology DSM 7
- QNAP QTS 5

### 测试场景
1. 本地文件系统（ext4, btrfs）
2. NFS挂载
3. SMB/CIFS挂载
4. 符号链接
5. 大文件处理（>10GB）
6. 网络中断恢复
7. 并发操作

## 总结

通过以上优化，系统将：
- ✅ 完全兼容各种Linux发行版
- ✅ 支持主流NAS系统
- ✅ 处理网络文件系统的特殊情况
- ✅ 提供更好的错误处理和恢复能力
- ✅ 支持容器化部署
- ✅ 提供系统服务化选项
