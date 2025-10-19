# 🔄 需要重启服务器

## 问题

新添加的API端点返回404错误，这是因为服务器还在运行旧代码。

## 解决方案

### 方法1：重启服务器（推荐）

```bash
# 1. 停止当前服务器
# 按 Ctrl+C 停止正在运行的 python app.py

# 2. 重新启动
python app.py
```

### 方法2：使用进程管理器

```bash
# 查找进程
ps aux | grep "python app.py"

# 或者在Windows上
tasklist | findstr python

# 杀死进程
kill -9 <PID>

# 或者在Windows上
taskkill /F /PID <PID>

# 重新启动
python app.py
```

### 方法3：使用systemd（如果配置了服务）

```bash
sudo systemctl restart media-renamer
```

## 验证

重启后，运行测试脚本验证：

```bash
python test_qrcode_api.py
```

应该看到：
```
✅ 成功!
二维码URL: https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid=...
```

## 新功能说明

重启后，以下API端点将可用：

1. **POST /api/qrcode/start** - 开始二维码登录
2. **POST /api/qrcode/check** - 检查扫码状态  
3. **POST /api/qrcode/finish** - 完成登录获取Cookie

这些端点实现了优化的二维码登录功能：
- ✅ 不需要qrcode库
- ✅ 不会卡死
- ✅ 异步轮询
- ✅ 自动保存Cookie

## 下一步

重启服务器后，可以：
1. 测试API端点（运行 `python test_qrcode_api.py`）
2. 实现前端界面（参考 `docs/二维码登录实现总结.md`）
3. 完整测试扫码登录流程
