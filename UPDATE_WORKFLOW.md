# 🚀 更新工作流程

## 步骤1：提交到GitHub

### 1.1 检查修改的文件

```bash
git status
```

应该看到：
- `app.py` (修改)
- `docs/` (新增文档)
- `test_qrcode_api.py` (新增)
- 其他新增的文件

### 1.2 添加文件

```bash
# 添加所有修改
git add .

# 或者只添加关键文件
git add app.py
git add docs/优化二维码登录方案.md
git add docs/二维码登录实现总结.md
git add test_qrcode_api.py
git add RESTART_SERVER.md
git add COMMIT_MESSAGE.md
git add UPDATE_WORKFLOW.md
```

### 1.3 提交

```bash
git commit -m "feat: 优化二维码登录，移除qrcode库依赖

- 新增三个API端点：/api/qrcode/start, /api/qrcode/check, /api/qrcode/finish
- 直接使用115官方二维码图片URL，不需要qrcode库
- 异步轮询检查扫码状态，避免阻塞
- 自动保存Cookie到配置文件
- 添加API测试脚本和完整文档

解决问题：
- 移除qrcode库依赖
- 避免后端生成图片阻塞
- 优化用户体验"
```

### 1.4 推送到GitHub

```bash
git push origin main
```

## 步骤2：在服务器上更新

### 2.1 SSH连接到服务器

```bash
ssh root@你的NAS_IP
```

### 2.2 进入项目目录

```bash
cd ~/media-sorter
# 或者你的实际路径
```

### 2.3 拉取最新代码

```bash
git pull origin main
```

### 2.4 重启服务

#### 方法A：手动重启

```bash
# 1. 停止当前服务（如果在前台运行，按 Ctrl+C）

# 2. 重新启动
python3 app.py

# 或者后台运行
nohup python3 app.py > app.log 2>&1 &
```

#### 方法B：使用systemd（如果配置了）

```bash
sudo systemctl restart media-renamer
```

#### 方法C：使用进程管理

```bash
# 查找进程
ps aux | grep "python.*app.py"

# 杀死进程
kill -9 <PID>

# 重新启动
nohup python3 app.py > app.log 2>&1 &
```

### 2.5 验证更新

```bash
# 测试新的API端点
python3 test_qrcode_api.py
```

应该看到：
```
✅ 成功!
二维码URL: https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid=...
```

## 步骤3：测试功能

### 3.1 访问Web界面

```
http://你的NAS_IP:8090
```

### 3.2 测试API（可选）

```bash
# 在服务器上或本地测试
curl -X POST http://localhost:8090/api/qrcode/start \
  -H "Content-Type: application/json" \
  -d '{"app":"wechatmini"}'
```

应该返回JSON响应，包含：
- `success: true`
- `qr_url: https://qrcodeapi.115.com/...`
- `uid, time, sign` 等参数

## 常见问题

### Q1: git pull 失败

```bash
# 如果有本地修改冲突
git stash
git pull origin main
git stash pop
```

### Q2: 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8090
# 或
netstat -tulpn | grep 8090

# 杀死进程
kill -9 <PID>
```

### Q3: Python依赖问题

```bash
# 确保requests库已安装
pip3 install requests

# 或使用requirements.txt
pip3 install -r requirements.txt
```

### Q4: 权限问题

```bash
# 给脚本执行权限
chmod +x app.py
chmod +x test_qrcode_api.py
```

## 快速命令（复制粘贴）

### 本地提交

```bash
git add .
git commit -m "feat: 优化二维码登录，移除qrcode库依赖"
git push origin main
```

### 服务器更新

```bash
cd ~/media-sorter
git pull origin main
pkill -f "python.*app.py"
nohup python3 app.py > app.log 2>&1 &
python3 test_qrcode_api.py
```

## 下一步

更新成功后：
1. ✅ 后端API已可用
2. ⏳ 实现前端界面（参考 `docs/二维码登录实现总结.md`）
3. ⏳ 完整测试扫码登录流程

---

**提示**: 如果遇到问题，查看日志：
```bash
tail -f app.log
```
