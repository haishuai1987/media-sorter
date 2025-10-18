# NAS系统部署指南

本指南针对主流NAS系统提供详细的部署说明。

---

## 目录
- [Synology DSM](#synology-dsm)
- [QNAP QTS](#qnap-qts)
- [TrueNAS/FreeNAS](#truenasfreenas)
- [Unraid](#unraid)
- [通用Linux NAS](#通用linux-nas)

---

## Synology DSM

### 方法1: Docker部署（推荐）

#### 1. 安装Docker
1. 打开 **套件中心**
2. 搜索并安装 **Container Manager**（旧版本为Docker）

#### 2. 部署应用
```bash
# SSH登录到Synology
ssh admin@your-nas-ip

# 创建工作目录
mkdir -p /volume1/docker/media-renamer
cd /volume1/docker/media-renamer

# 上传文件（app.py, index.html, Dockerfile, docker-compose.yml）

# 修改docker-compose.yml中的路径
# 例如: /volume1/media:/data

# 启动容器
docker-compose up -d
```

#### 3. 访问应用
- 本地: http://nas-ip:8090
- 配置路径使用 `/data/` 开头

### 方法2: Python直接运行

#### 1. 安装Python
1. 打开 **套件中心**
2. 搜索并安装 **Python 3.9** 或更高版本

#### 2. 部署应用
```bash
# SSH登录
ssh admin@your-nas-ip

# 创建应用目录
mkdir -p /volume1/apps/media-renamer
cd /volume1/apps/media-renamer

# 上传文件（app.py, index.html）

# 设置权限
chmod +x app.py

# 运行应用
python3 app.py
```

#### 3. 设置开机自启
1. 打开 **控制面板** > **任务计划**
2. 新增 > **触发的任务** > **用户定义的脚本**
3. 任务名称: `Media Renamer`
4. 用户账号: `root`
5. 事件: **开机**
6. 脚本内容:
```bash
#!/bin/bash
cd /volume1/apps/media-renamer
python3 app.py &
```

### 路径说明
- 共享文件夹路径: `/volume1/共享文件夹名/`
- 例如: `/volume1/media/待整理`

---

## QNAP QTS

### 方法1: Container Station（推荐）

#### 1. 安装Container Station
1. 打开 **App Center**
2. 搜索并安装 **Container Station**

#### 2. 部署应用
```bash
# SSH登录到QNAP
ssh admin@your-nas-ip

# 创建工作目录
mkdir -p /share/Container/media-renamer
cd /share/Container/media-renamer

# 上传文件

# 修改docker-compose.yml中的路径
# 例如: /share/media:/data

# 启动容器
docker-compose up -d
```

### 方法2: Python直接运行

#### 1. 安装Python
1. 打开 **App Center**
2. 搜索并安装 **Python 3**

#### 2. 部署应用
```bash
# SSH登录
ssh admin@your-nas-ip

# 创建应用目录
mkdir -p /share/apps/media-renamer
cd /share/apps/media-renamer

# 上传文件
# 设置权限
chmod +x app.py

# 运行
python3 app.py
```

#### 3. 设置开机自启
创建 `/etc/config/autorun.sh`:
```bash
#!/bin/bash
cd /share/apps/media-renamer
python3 app.py &
```

### 路径说明
- 共享文件夹路径: `/share/共享文件夹名/`
- 例如: `/share/media/待整理`

---

## TrueNAS/FreeNAS

### 方法1: Jail（推荐）

#### 1. 创建Jail
1. 打开 **Jails** 页面
2. 点击 **ADD**
3. 名称: `media-renamer`
4. 选择 **Release**: 最新版本
5. 创建

#### 2. 配置Jail
```bash
# 进入Jail
iocage console media-renamer

# 安装Python
pkg install python39

# 创建应用目录
mkdir -p /usr/local/media-renamer
cd /usr/local/media-renamer

# 上传文件
# 设置权限
chmod +x app.py

# 运行
python3.9 app.py
```

#### 3. 挂载存储
1. 在Jail设置中添加 **Mount Points**
2. 源: `/mnt/pool/media`
3. 目标: `/media`

### 方法2: Docker（TrueNAS SCALE）

TrueNAS SCALE原生支持Docker，参考通用Docker部署方法。

### 路径说明
- 存储池路径: `/mnt/pool名称/数据集名称/`
- Jail内路径: 根据Mount Point配置

---

## Unraid

### 方法1: Docker（推荐）

#### 1. 通过Community Applications安装

1. 打开 **Apps** 标签
2. 搜索 `media-renamer`（如果已发布）
3. 点击安装

#### 2. 手动Docker部署

1. 打开 **Docker** 标签
2. 点击 **Add Container**
3. 配置:
   - Name: `media-renamer`
   - Repository: `your-image` 或本地构建
   - Port: `8090:8090`
   - Path: `/mnt/user/media:/data`

#### 3. 使用docker-compose

```bash
# SSH登录
ssh root@tower

# 创建目录
mkdir -p /mnt/user/appdata/media-renamer
cd /mnt/user/appdata/media-renamer

# 上传文件
# 修改docker-compose.yml
# 启动
docker-compose up -d
```

### 路径说明
- 用户共享路径: `/mnt/user/共享名称/`
- 磁盘路径: `/mnt/disk1/`, `/mnt/disk2/` 等
- 推荐使用用户共享路径

---

## 通用Linux NAS

### 自动安装

```bash
# 下载安装脚本
chmod +x install.sh

# 运行安装
./install.sh
```

### 手动安装

#### 1. 检查Python
```bash
python3 --version
# 需要 >= 3.6
```

#### 2. 部署应用
```bash
# 创建目录
mkdir -p /opt/media-renamer
cd /opt/media-renamer

# 上传文件
# 设置权限
chmod +x app.py

# 运行
python3 app.py
```

#### 3. 创建systemd服务
```bash
sudo nano /etc/systemd/system/media-renamer.service
```

内容:
```ini
[Unit]
Description=Media Renamer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/media-renamer
ExecStart=/usr/bin/python3 /opt/media-renamer/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable media-renamer
sudo systemctl start media-renamer
```

---

## 网络文件系统注意事项

### NFS挂载
```bash
# 挂载选项建议
mount -t nfs -o rw,sync,hard,intr nas-ip:/export/path /mnt/nas
```

### SMB/CIFS挂载
```bash
# 挂载选项建议
mount -t cifs //nas-ip/share /mnt/nas -o username=user,password=pass,iocharset=utf8
```

### 权限问题
```bash
# 检查权限
ls -la /path/to/media

# 修改所有者
sudo chown -R your-user:your-group /path/to/media

# 修改权限
sudo chmod -R 755 /path/to/media
```

---

## 性能优化建议

### 1. 网络延迟配置
编辑 `app.py`:
```python
NETWORK_OP_DELAY = 1.0   # 网络文件系统操作延迟（秒）
NETWORK_RETRY_COUNT = 3  # 重试次数
```

### 2. 批量处理
- 建议每次处理不超过100个文件
- 大文件（>10GB）单独处理

### 3. 缓存优化
- 使用SSD作为缓存盘（如Synology SSD Cache）
- 启用文件系统缓存

---

## 故障排查

### 问题1: 权限被拒绝
```bash
# 检查文件权限
ls -la /path/to/file

# 检查用户权限
id your-user

# 添加用户到组
sudo usermod -aG group-name your-user
```

### 问题2: 端口被占用
```bash
# 检查端口占用
netstat -tuln | grep 8090

# 修改端口
# 编辑 app.py 中的 PORT 变量
```

### 问题3: 网络超时
```bash
# 增加重试次数和延迟
# 编辑 app.py:
NETWORK_RETRY_COUNT = 5
NETWORK_OP_DELAY = 2.0
```

### 问题4: 文件名非法字符
- 系统已自动清理非法字符
- 如遇问题，检查文件系统类型
- 建议使用 ext4 或 btrfs

---

## 安全建议

### 1. 防火墙配置
```bash
# 仅允许局域网访问
sudo ufw allow from 192.168.1.0/24 to any port 8090
```

### 2. 反向代理（可选）
使用Nginx添加认证:
```nginx
location /media-renamer/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8090/;
}
```

### 3. HTTPS（可选）
使用Let's Encrypt证书

---

## 支持的文件系统

| 文件系统 | 支持 | 备注 |
|---------|------|------|
| ext4 | ✅ | 推荐 |
| btrfs | ✅ | 推荐（支持快照） |
| ZFS | ✅ | 推荐（TrueNAS） |
| XFS | ✅ | 适合大文件 |
| NTFS | ✅ | 需要ntfs-3g |
| FAT32 | ⚠️ | 文件名限制多 |
| exFAT | ✅ | 适合移动硬盘 |
| NFS | ✅ | 网络文件系统 |
| SMB/CIFS | ✅ | 网络文件系统 |

---

## 联系支持

如遇问题，请提供:
1. NAS系统和版本
2. Python版本
3. 错误日志
4. 文件系统类型
5. 网络配置（NFS/SMB等）
