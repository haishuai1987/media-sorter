# 端口配置指南

## 🔌 端口冲突解决方案

Media Renamer v2.5.0 支持灵活的端口配置，避免与 NAS 系统或其他服务冲突。

---

## 📋 常见端口占用情况

### NAS 系统默认端口
- **5000**: Synology DSM、QNAP QTS
- **8000**: 部分 NAS 管理界面
- **8080**: qBittorrent、Transmission
- **8081**: 部分下载工具
- **9091**: Transmission Web UI

### 推荐可用端口
- **8090** (默认) - 通常可用
- **8091-8099** - 备选端口
- **9000-9009** - 备选端口
- **7000-7009** - 备选端口

---

## 🚀 三种配置方式

### 方式一：命令行参数（推荐）

#### 基本用法
```bash
# 使用默认端口 8090
python app_v2.py

# 指定端口
python app_v2.py --port 8091

# 指定主机和端口
python app_v2.py --host 0.0.0.0 --port 9000

# 启用调试模式
python app_v2.py --port 8091 --debug
```

#### 简化版
```bash
# 使用默认端口 5000
python app_v2_simple.py

# 指定端口
python app_v2_simple.py --port 5001

# 指定主机和端口
python app_v2_simple.py --host 0.0.0.0 --port 9000
```

#### 查看帮助
```bash
python app_v2.py --help
python app_v2_simple.py --help
```

---

### 方式二：环境变量

#### Linux/Mac
```bash
# 临时设置
PORT=8091 python app_v2.py

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
export PORT=8091
export HOST=0.0.0.0
python app_v2.py
```

#### Windows PowerShell
```powershell
# 临时设置
$env:PORT=8091
python app_v2.py

# 或一行命令
$env:PORT=8091; python app_v2.py
```

#### Windows CMD
```cmd
# 临时设置
set PORT=8091
python app_v2.py

# 或一行命令
set PORT=8091 && python app_v2.py
```

---

### 方式三：修改配置文件

编辑 `core/environment.py`，修改默认端口：

```python
configs = {
    self.LOCAL: {
        'host': '0.0.0.0',
        'port': 8091,  # 修改这里
        'debug': True,
        # ...
    },
    # ...
}
```

---

## 🎯 使用场景

### 场景1：NAS 上部署（避免与 DSM 冲突）
```bash
# Synology DSM 占用 5000，使用 8090
python app_v2.py --port 8090

# 或使用 9000
python app_v2.py --port 9000
```

### 场景2：多个实例同时运行
```bash
# 实例1 - 生产环境
python app_v2.py --port 8090

# 实例2 - 测试环境
python app_v2.py --port 8091

# 实例3 - 开发环境
python app_v2.py --port 8092 --debug
```

### 场景3：Docker 容器部署
```bash
# 映射到主机的 9000 端口
docker run -p 9000:8090 media-renamer

# 或使用环境变量
docker run -e PORT=9000 -p 9000:9000 media-renamer
```

### 场景4：反向代理配置
```bash
# 使用非标准端口，通过 Nginx 代理
python app_v2.py --host 127.0.0.1 --port 8090

# Nginx 配置
# location /media-renamer/ {
#     proxy_pass http://127.0.0.1:8090/;
# }
```

---

## 🔍 端口检测

### 检查端口是否被占用

#### Linux/Mac
```bash
# 检查端口 8090
lsof -i :8090

# 或使用 netstat
netstat -tuln | grep 8090
```

#### Windows PowerShell
```powershell
# 检查端口 8090
Get-NetTCPConnection -LocalPort 8090

# 或使用 netstat
netstat -ano | findstr :8090
```

### 查找可用端口
```bash
# 测试端口是否可用（Linux/Mac）
nc -zv 127.0.0.1 8090

# 测试端口是否可用（Windows）
Test-NetConnection -ComputerName 127.0.0.1 -Port 8090
```

---

## ⚙️ 配置优先级

配置的优先级从高到低：

1. **命令行参数** `--port 8091`
2. **环境变量** `PORT=8091`
3. **配置文件** `core/environment.py`
4. **默认值** `8090` (完整版) / `5000` (简化版)

---

## 🛠️ 故障排除

### 问题1：端口被占用
```
错误: OSError: [Errno 48] Address already in use
```

**解决方案：**
```bash
# 方案1: 使用其他端口
python app_v2.py --port 8091

# 方案2: 找到并停止占用进程
# Linux/Mac
lsof -ti:8090 | xargs kill -9

# Windows
netstat -ano | findstr :8090
taskkill /PID <进程ID> /F

# 方案3: 使用自动端口
python app_v2.py --port 0  # 系统自动分配
```

### 问题2：无法访问（防火墙）
```
错误: 浏览器无法连接
```

**解决方案：**
```bash
# Linux - 开放端口
sudo ufw allow 8090/tcp

# Windows - 添加防火墙规则
netsh advfirewall firewall add rule name="Media Renamer" dir=in action=allow protocol=TCP localport=8090
```

### 问题3：局域网无法访问
```
错误: 其他设备无法访问
```

**解决方案：**
```bash
# 确保监听所有接口
python app_v2.py --host 0.0.0.0 --port 8090

# 而不是
python app_v2.py --host 127.0.0.1 --port 8090
```

---

## 📝 配置示例

### 开发环境
```bash
# 本地开发，启用调试
python app_v2.py --host 127.0.0.1 --port 8090 --debug
```

### 生产环境
```bash
# 生产部署，监听所有接口
python app_v2.py --host 0.0.0.0 --port 8090
```

### NAS 环境
```bash
# Synology NAS，避免端口冲突
python app_v2.py --host 0.0.0.0 --port 9000
```

### Docker 环境
```bash
# Docker 容器内
python app_v2.py --host 0.0.0.0 --port 8090

# Docker 运行命令
docker run -p 9000:8090 -e PORT=8090 media-renamer
```

---

## 🔐 安全建议

### 本地开发
```bash
# 只监听本地，更安全
python app_v2.py --host 127.0.0.1 --port 8090
```

### 生产部署
```bash
# 使用反向代理（推荐）
python app_v2.py --host 127.0.0.1 --port 8090

# 配合 Nginx/Apache 使用
# 添加认证、HTTPS 等安全措施
```

### 防火墙配置
```bash
# 只允许特定 IP 访问
# Linux iptables
sudo iptables -A INPUT -p tcp --dport 8090 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8090 -j DROP
```

---

## 📚 相关文档

- [快速启动指南](QUICK-START-v2.5.0.md)
- [部署手册](docs/部署手册.md)
- [使用手册](docs/使用手册.md)

---

## 💡 最佳实践

1. **开发环境**: 使用 `127.0.0.1` + 非标准端口 + 调试模式
2. **测试环境**: 使用 `0.0.0.0` + 非标准端口
3. **生产环境**: 使用反向代理 + 标准端口 (80/443)
4. **NAS 环境**: 避开 5000/8000/8080，使用 8090/9000
5. **多实例**: 每个实例使用不同端口

---

**更新时间**: 2025-10-22  
**版本**: v2.5.0
