# 服务器更新命令 - v1.2.12

## 🚀 快速更新（推荐）

### 方式 1: 使用更新脚本（最简单）

```bash
# 1. 下载更新脚本
wget https://raw.githubusercontent.com/你的用户名/media-renamer/main/server-update-v1.2.12.sh

# 2. 添加执行权限
chmod +x server-update-v1.2.12.sh

# 3. 运行更新
./server-update-v1.2.12.sh
```

**完成！** 🎉

---

### 方式 2: 一键命令（超简单）

```bash
# 复制粘贴这一行命令即可
curl -fsSL https://raw.githubusercontent.com/你的用户名/media-renamer/main/server-update-v1.2.12-simple.sh | bash
```

**完成！** 🎉

---

## 📋 手动更新步骤

### 步骤 1: 停止服务
```bash
# 查找进程
ps aux | grep "python.*app.py"

# 停止进程（替换 PID）
kill <PID>

# 或者一键停止
pkill -f "python.*app.py"
```

### 步骤 2: 备份当前版本
```bash
# 创建备份目录
mkdir -p backup_$(date +%Y%m%d_%H%M%S)

# 备份文件
cp app.py backup_*/app.py.backup
cp version.txt backup_*/version.txt.backup
```

### 步骤 3: 拉取最新代码
```bash
# 进入项目目录
cd /path/to/media-renamer

# 拉取代码
git pull origin main
```

### 步骤 4: 检查版本
```bash
# 查看版本号
cat version.txt

# 应该显示: v1.2.12
```

### 步骤 5: 运行测试（可选）
```bash
# 运行测试
python3 test_release_groups_v1.2.12.py

# 预期结果: 通过率 > 90%
```

### 步骤 6: 启动服务
```bash
# 后台启动
nohup python3 app.py > media-renamer.log 2>&1 &

# 记录 PID
echo $! > media-renamer.pid

# 查看日志
tail -f media-renamer.log
```

### 步骤 7: 验证更新
```bash
# 访问 Web 界面
curl http://localhost:8090

# 或在浏览器访问
# http://你的服务器IP:8090
```

---

## 🔧 常用命令

### 查看服务状态
```bash
# 查看进程
ps aux | grep "python.*app.py"

# 查看日志
tail -f media-renamer.log

# 查看最后 100 行日志
tail -n 100 media-renamer.log
```

### 重启服务
```bash
# 停止服务
pkill -f "python.*app.py"

# 启动服务
nohup python3 app.py > media-renamer.log 2>&1 &
```

### 回滚版本
```bash
# 回滚到上一版本
git reset --hard HEAD~1

# 或恢复备份
cp backup_*/app.py.backup app.py
cp backup_*/version.txt.backup version.txt

# 重启服务
pkill -f "python.*app.py"
nohup python3 app.py > media-renamer.log 2>&1 &
```

---

## 🐳 Docker 更新

### 使用 Docker Compose
```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 重启容器
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

### 使用 Docker 命令
```bash
# 1. 停止容器
docker stop media-renamer

# 2. 删除容器
docker rm media-renamer

# 3. 拉取最新镜像
docker pull your-registry/media-renamer:v1.2.12

# 4. 启动新容器
docker run -d \
  --name media-renamer \
  -p 8090:8090 \
  -v /path/to/media:/media \
  your-registry/media-renamer:v1.2.12

# 5. 查看日志
docker logs -f media-renamer
```

---

## 🔍 故障排除

### 问题 1: Git 拉取失败
```bash
# 检查 Git 状态
git status

# 如果有本地修改，先暂存
git stash

# 拉取代码
git pull origin main

# 恢复暂存
git stash pop
```

### 问题 2: 服务启动失败
```bash
# 查看错误日志
tail -n 50 media-renamer.log

# 检查端口占用
netstat -tlnp | grep 8090

# 修改端口（如果需要）
export PORT=8091
python3 app.py
```

### 问题 3: 权限问题
```bash
# 添加执行权限
chmod +x server-update-v1.2.12.sh

# 使用 sudo（如果需要）
sudo ./server-update-v1.2.12.sh
```

### 问题 4: Python 版本问题
```bash
# 检查 Python 版本
python3 --version

# 需要 Python 3.7+
# 如果版本过低，升级 Python
```

---

## 📊 更新验证

### 1. 检查版本号
```bash
cat version.txt
# 应该显示: v1.2.12
```

### 2. 检查服务状态
```bash
ps aux | grep "python.*app.py"
# 应该看到运行中的进程
```

### 3. 检查 Web 界面
```bash
curl http://localhost:8090
# 应该返回 HTML 内容
```

### 4. 测试功能
- 访问 http://服务器IP:8090
- 检查页面底部版本号
- 测试整理功能

---

## 🎯 更新内容

### v1.2.12 核心改进
- ✅ Release Group: 13 → 100+
- ✅ 测试通过率: 92.6%
- ✅ 支持格式: 4 种
- ✅ 性能影响: < 10ms/文件

### 新增支持
- CHD 系列（12个）
- HDChina 系列（6个）
- LemonHD 系列（9个）
- MTeam 系列（4个）
- OurBits 系列（8个）
- PTer 系列（6个）
- PTHome 系列（7个）
- PTsbao 系列（11个）
- 动漫字幕组（20+个）
- 国际组（20+个）

---

## 📞 需要帮助？

### 查看文档
- [CHANGELOG-v1.2.12.md](CHANGELOG-v1.2.12.md) - 详细更新日志
- [QUICK-START-v1.2.12.md](QUICK-START-v1.2.12.md) - 快速开始
- [docs/云服务器部署指南.md](docs/云服务器部署指南.md) - 部署指南

### 常见问题
- [docs/常见问题.md](docs/常见问题.md)

### 提交 Issue
- GitHub Issues: https://github.com/你的用户名/media-renamer/issues

---

## ✅ 更新完成检查清单

更新后请确认：

- [ ] 服务正常运行
- [ ] 版本号显示 v1.2.12
- [ ] Web 界面可访问
- [ ] 整理功能正常
- [ ] Release Group 正确移除
- [ ] 日志无错误

---

**祝更新顺利！** 🚀
