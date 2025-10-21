# 项目文件整理建议

## 📁 当前状态

### Git状态
- ✅ 本地与GitHub同步
- ⚠️ 有一个未提交的小改动（tasks.md的空行）

### 临时文件清理建议

#### 🗑️ 可以删除的临时测试文件
这些是调试过程中创建的临时文件，可以安全删除：

```
check-server-code.ps1          # 临时检查脚本
fix-category-none.sh           # 临时修复脚本
fix-server.ps1                 # 临时修复脚本
force-clean-restart.ps1        # 临时重启脚本
force-restart-clean.ps1        # 临时重启脚本（重复）
restart-server.ps1             # 临时重启脚本
test-server.ps1                # 临时测试脚本
test-folder-access.py          # 临时测试脚本
test-smart-rename-error.py     # 临时测试脚本
diagnose-update.py             # 临时诊断脚本
diagnose-nas-update.sh         # 临时诊断脚本
```

#### 📦 应该保留的重要文件

**部署脚本（保留）：**
```
deploy-cloud.sh                # 云服务器部署
install.sh                     # 安装脚本
start.sh                       # 启动脚本
stop.sh                        # 停止脚本
force-push-update.ps1          # 强制更新脚本（重要）
push-update.ps1                # 普通更新脚本
ssh-update.ps1                 # SSH更新脚本
远程推送更新.ps1               # 中文更新脚本
远程推送更新.sh                # 中文更新脚本
部署智能强制更新.sh            # 中文部署脚本
```

**核心文件（保留）：**
```
app.py                         # 主程序
requirements.txt               # Python依赖
version.txt                    # 版本号
increment_version.py           # 版本管理
Dockerfile                     # Docker配置
docker-compose.yml             # Docker Compose配置
.env.example                   # 环境变量示例
README.md                      # 项目说明
LICENSE                        # 许可证
IMPLEMENTATION_STATUS.md       # 实施状态（新）
```

**前端文件（保留）：**
```
index.html                     # 旧版入口（考虑删除）
public/index.html              # 新版入口
public/style.css               # 样式
```

**文档（保留）：**
```
docs/                          # 所有文档
.kiro/specs/                   # 所有spec文档
```

## 🧹 清理步骤

### 1. 删除临时文件
```powershell
# 删除临时测试脚本
Remove-Item check-server-code.ps1
Remove-Item fix-category-none.sh
Remove-Item fix-server.ps1
Remove-Item force-clean-restart.ps1
Remove-Item force-restart-clean.ps1
Remove-Item restart-server.ps1
Remove-Item test-server.ps1
Remove-Item test-folder-access.py
Remove-Item test-smart-rename-error.py
Remove-Item diagnose-update.py
Remove-Item diagnose-nas-update.sh
```

### 2. 删除根目录的旧index.html
```powershell
# 如果public/index.html是主要使用的版本
Remove-Item index.html
```

### 3. 提交清理后的代码
```powershell
git add -A
git commit -m "chore: 清理临时测试文件"
git push origin main
```

### 4. 更新.gitignore
建议添加以下规则避免临时文件被提交：
```
# 临时测试文件
test-*.py
test-*.ps1
fix-*.sh
fix-*.ps1
diagnose-*.py
diagnose-*.sh
check-*.ps1
restart-*.ps1
force-*-restart.ps1
```

## 📊 文件统计

### 当前项目结构
```
media-sorter/
├── app.py                    # 主程序 (5000+ 行)
├── public/                   # 前端资源
│   ├── index.html
│   ├── style.css
│   └── logo.svg
├── docs/                     # 文档 (10+ 文件)
├── .kiro/specs/             # Spec文档 (6个spec)
├── scripts/                  # 部署脚本 (10+ 个)
└── 临时文件                  # 11个临时文件 ⚠️
```

### 清理后的结构
```
media-sorter/
├── app.py                    # 主程序
├── public/                   # 前端资源
├── docs/                     # 文档
├── .kiro/specs/             # Spec文档
└── scripts/                  # 部署脚本（整理后）
```

## ✅ 建议的下一步

1. **立即清理** - 删除临时文件
2. **更新.gitignore** - 防止未来提交临时文件
3. **整理scripts目录** - 将部署脚本移到scripts/目录
4. **提交清理** - 提交整理后的代码

这样项目会更整洁，更容易维护！
