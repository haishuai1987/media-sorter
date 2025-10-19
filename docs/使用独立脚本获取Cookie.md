# 使用独立脚本获取115网盘Cookie

## 简介

`get_115_cookie.py` 是一个独立的Python脚本，可以直接在命令行中扫码获取115网盘Cookie，无需启动Web服务。

这个脚本来自 [py115](https://github.com/ChenyangGao/p115client) 项目。

## 安装依赖

```bash
# 安装qrcode库（用于在终端显示二维码）
pip3 install qrcode

# 或者使用-o参数生成图片，不需要安装qrcode
```

## 使用方法

### 方法1：终端显示二维码（默认）

```bash
# 使用微信小程序（推荐）
python3 get_115_cookie.py wechatmini

# 使用支付宝小程序
python3 get_115_cookie.py alipaymini

# 使用安卓APP
python3 get_115_cookie.py android

# 使用iOS APP
python3 get_115_cookie.py ios

# 使用TV版
python3 get_115_cookie.py tv
```

终端会显示ASCII二维码，使用115手机客户端扫码即可。

### 方法2：生成图片二维码（推荐）

```bash
# 使用-o参数，会自动打开图片
python3 get_115_cookie.py wechatmini -o
```

这种方式会：
1. 生成二维码图片
2. 自动打开图片查看器
3. 等待扫码

### 方法3：不指定设备（默认web）

```bash
# 默认使用web端
python3 get_115_cookie.py
```

## 支持的设备类型

| 设备类型 | 参数 | Cookie有效期 | 推荐度 |
|---------|------|-------------|--------|
| 微信小程序 | wechatmini | 几个月 | ⭐⭐⭐⭐⭐ |
| 支付宝小程序 | alipaymini | 几个月 | ⭐⭐⭐⭐ |
| 安卓APP | android | 几周 | ⭐⭐⭐ |
| iOS APP | ios | 几周 | ⭐⭐⭐ |
| TV版 | tv | 几周 | ⭐⭐⭐ |
| 网页版 | web | 几天 | ⭐⭐ |
| Linux | linux | 几周 | ⭐⭐ |
| Mac | mac | 几周 | ⭐⭐ |
| Windows | windows | 几周 | ⭐⭐ |
| 安卓TV | qandroid | 几周 | ⭐⭐ |

## 完整示例

### Linux服务器上使用

```bash
cd /root/media-sorter

# 使用微信小程序，生成图片
python3 get_115_cookie.py wechatmini -o

# 等待扫码...
# [status=0] qrcode: waiting
# [status=1] qrcode: scanned
# [status=2] qrcode: signed in

# 输出Cookie
# UID=123456_A1B2C3D4E5; CID=ABCDEFGHIJK123456; SEID=a1b2c3d4e5f6g7h8
```

### Windows上使用

```powershell
cd E:\media-renamer

# 使用微信小程序，生成图片
python get_115_cookie.py wechatmini -o

# 会自动打开图片，扫码即可
```

## 扫码流程

1. **运行脚本**
   ```bash
   python3 get_115_cookie.py wechatmini -o
   ```

2. **查看二维码**
   - 终端模式：直接在终端显示ASCII二维码
   - 图片模式：自动打开图片查看器

3. **扫码**
   - 打开115手机客户端
   - 扫描二维码
   - 点击"确认登录"

4. **等待状态**
   ```
   [status=0] qrcode: waiting      # 等待扫码
   [status=1] qrcode: scanned      # 已扫码，等待确认
   [status=2] qrcode: signed in    # 登录成功
   ```

5. **获取Cookie**
   ```
   UID=123456_A1B2C3D4E5; CID=ABCDEFGHIJK123456; SEID=a1b2c3d4e5f6g7h8
   ```

6. **复制Cookie**
   - 复制输出的Cookie字符串
   - 粘贴到系统设置中

## 常见问题

### Q: 提示"ModuleNotFoundError: No module named 'qrcode'"
A: 安装qrcode库：
```bash
pip3 install qrcode
```
或者使用 `-o` 参数生成图片，不需要qrcode库。

### Q: 二维码在终端显示不正常
A: 使用 `-o` 参数生成图片：
```bash
python3 get_115_cookie.py wechatmini -o
```

### Q: 扫码后提示"expired"
A: 二维码已过期（5分钟），重新运行脚本。

### Q: 扫码后提示"canceled"
A: 用户在手机上取消了登录，重新扫码并点击确认。

### Q: 选择哪个设备类型最好？
A: 推荐使用 `wechatmini`（微信小程序），Cookie有效期最长。

### Q: 会踢掉其他设备吗？
A: 会踢掉相同设备类型的登录。例如，扫码"微信小程序"会踢掉之前用微信小程序登录的设备，但不会影响APP登录。

## 高级用法

### 查看版本
```bash
python3 get_115_cookie.py -v
```

### 查看帮助
```bash
python3 get_115_cookie.py -h
```

### 在脚本中使用

```python
from get_115_cookie import login_with_qrcode

# 获取Cookie
result = login_with_qrcode(app='wechatmini', scan_in_console=False)
cookie_dict = result['data']['cookie']

# 构建Cookie字符串
cookie = '; '.join(f"{k}={v}" for k, v in cookie_dict.items())
print(cookie)
```

## 与Web界面的区别

| 特性 | 独立脚本 | Web界面 |
|-----|---------|---------|
| 使用场景 | 命令行 | 浏览器 |
| 依赖 | Python | Web服务 |
| 二维码显示 | 终端/图片 | 网页 |
| Cookie保存 | 手动复制 | 自动保存 |
| 适合人群 | 开发者 | 普通用户 |

## 故障排除

### 1. 网络问题
如果无法连接到115 API，检查网络连接：
```bash
curl https://qrcodeapi.115.com/api/1.0/web/1.0/token/
```

### 2. Python版本
确保使用Python 3.6+：
```bash
python3 --version
```

### 3. 权限问题
如果无法创建临时文件，检查权限：
```bash
ls -la /tmp
```

## 参考资料

- [py115 - 115网盘Python SDK](https://github.com/ChenyangGao/p115client)
- [115网盘API文档](https://github.com/ChenyangGao/p115client/blob/main/API.md)

## 贡献

这个脚本来自开源项目 py115，感谢作者 ChenyangGao 的贡献。

如果发现问题或有改进建议，欢迎提交Issue或PR。
