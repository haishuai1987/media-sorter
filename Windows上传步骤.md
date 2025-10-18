# Windows系统GitHub上传步骤

## 📋 准备工作

### 1. 安装Git

如果还没有安装Git：

1. 访问 https://git-scm.com/download/win
2. 下载Git for Windows
3. 运行安装程序
4. 使用默认设置安装即可

**验证安装**：
```cmd
git --version
```
应该显示类似：`git version 2.x.x`

### 2. 创建GitHub账号

如果还没有GitHub账号：

1. 访问 https://github.com/
2. 点击 "Sign up"
3. 按照步骤注册

---

## 🚀 使用自动脚本上传

### 步骤1: 打开命令提示符

**方法1**：
1. 按 `Win + R`
2. 输入 `cmd`
3. 按回车

**方法2**：
1. 在文件资源管理器中打开项目文件夹（E:\media-renamer）
2. 在地址栏输入 `cmd`
3. 按回车

### 步骤2: 运行上传脚本

在命令提示符中输入：
```cmd
upload-to-github.bat
```

### 步骤3: 按照提示操作

脚本会引导你完成以下步骤：

#### 1. 检查Git安装
```
✅ Git已安装
```

#### 2. 初始化Git仓库
```
📦 初始化Git仓库...
✅ Git仓库已初始化
```

#### 3. 配置用户信息
```
⚙️  配置Git用户信息
请输入你的GitHub用户名: 
```
**输入你的GitHub用户名**，例如：`zhangsan`

```
请输入你的GitHub邮箱: 
```
**输入你的GitHub邮箱**，例如：`zhangsan@example.com`

#### 4. 添加和提交文件
```
📝 添加文件到Git...
✅ 文件已添加

💾 提交更改...
✅ 更改已提交
```

#### 5. 创建GitHub仓库

脚本会提示你：
```
🔗 添加远程仓库

请先在GitHub上创建一个新仓库：
1. 访问 https://github.com/new
2. Repository name: media-renamer
3. Description: 智能媒体文件整理工具
4. 选择 Public 或 Private
5. 不要勾选 'Initialize this repository with a README'
6. 点击 'Create repository'
```

**操作步骤**：

a. 打开浏览器，访问 https://github.com/new

b. 填写仓库信息：
   - **Repository name**: `media-renamer`
   - **Description**: `智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别`
   - **Public** 或 **Private**: 选择公开或私有
   - **不要勾选** "Add a README file"
   - **不要勾选** "Add .gitignore"
   - **不要勾选** "Choose a license"

c. 点击 **"Create repository"** 按钮

d. 创建后，GitHub会显示仓库URL，例如：
   ```
   https://github.com/zhangsan/media-renamer.git
   ```

e. **复制这个URL**

#### 6. 输入仓库URL

回到命令提示符，输入刚才复制的URL：
```
创建完成后，请输入仓库URL: https://github.com/zhangsan/media-renamer.git
```

#### 7. 推送到GitHub

```
🚀 推送到GitHub...
```

如果是第一次推送，可能会弹出登录窗口：
- 输入你的GitHub用户名
- 输入你的GitHub密码或Personal Access Token

#### 8. 完成

如果成功，会显示：
```
==========================================
  ✅ 上传成功！
==========================================

你的仓库地址：
https://github.com/zhangsan/media-renamer.git

下一步：
1. 访问你的GitHub仓库
2. 添加仓库描述和Topics
3. 创建第一个Release（可选）
```

---

## 🔑 GitHub身份验证

### 方法1: Personal Access Token（推荐）

如果Git要求输入密码，使用Personal Access Token：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写信息：
   - Note: `media-renamer`
   - Expiration: 选择有效期
   - 勾选 `repo` 权限
4. 点击 "Generate token"
5. **复制生成的token**（只显示一次！）
6. 在Git提示输入密码时，粘贴这个token

### 方法2: GitHub CLI

```cmd
# 安装GitHub CLI
winget install GitHub.cli

# 登录
gh auth login
```

---

## ❌ 常见错误处理

### 错误1: "git不是内部或外部命令"

**原因**: Git未安装或未添加到PATH

**解决**:
1. 安装Git for Windows
2. 重启命令提示符
3. 验证：`git --version`

### 错误2: "Permission denied"

**原因**: 没有权限访问仓库

**解决**:
1. 检查仓库URL是否正确
2. 检查是否已登录GitHub
3. 使用Personal Access Token

### 错误3: "remote origin already exists"

**原因**: 已经添加过远程仓库

**解决**:
```cmd
# 删除旧的远程仓库
git remote remove origin

# 重新添加
git remote add origin https://github.com/你的用户名/media-renamer.git
```

### 错误4: "failed to push"

**原因**: 网络问题或权限问题

**解决**:
1. 检查网络连接
2. 检查GitHub是否可访问
3. 使用代理（如果需要）：
```cmd
git config --global http.proxy http://proxy:port
```

---

## 🎯 完整操作示例

### 示例演示

```cmd
E:\media-renamer> upload-to-github.bat

==========================================
  媒体库文件管理器 - GitHub上传助手
==========================================

✅ Git已安装

✅ Git仓库已存在

⚙️  配置Git用户信息
请输入你的GitHub用户名: zhangsan
请输入你的GitHub邮箱: zhangsan@example.com
✅ Git用户信息已配置

📝 添加文件到Git...
✅ 文件已添加

💾 提交更改...
✅ 更改已提交

🔗 添加远程仓库

请先在GitHub上创建一个新仓库：
1. 访问 https://github.com/new
2. Repository name: media-renamer
3. Description: 智能媒体文件整理工具
4. 选择 Public 或 Private
5. 不要勾选 'Initialize this repository with a README'
6. 点击 'Create repository'

创建完成后，请输入仓库URL: https://github.com/zhangsan/media-renamer.git
✅ 远程仓库已添加

🚀 推送到GitHub...
Enumerating objects: 25, done.
Counting objects: 100% (25/25), done.
Delta compression using up to 8 threads
Compressing objects: 100% (20/20), done.
Writing objects: 100% (25/25), 150.00 KiB | 5.00 MiB/s, done.
Total 25 (delta 5), reused 0 (delta 0)
To https://github.com/zhangsan/media-renamer.git
 * [new branch]      main -> main

==========================================
  ✅ 上传成功！
==========================================

你的仓库地址：
https://github.com/zhangsan/media-renamer.git

下一步：
1. 访问你的GitHub仓库
2. 添加仓库描述和Topics
3. 创建第一个Release（可选）

请按任意键继续. . .
```

---

## 📱 上传后的操作

### 1. 访问你的仓库

在浏览器中打开：
```
https://github.com/你的用户名/media-renamer
```

### 2. 添加Topics

1. 点击仓库页面右侧的 "⚙️" 图标（About旁边）
2. 在Topics中添加：
   - `python`
   - `media`
   - `renamer`
   - `nas`
   - `tmdb`
   - `douban`
   - `plex`
   - `jellyfin`
3. 点击 "Save changes"

### 3. 创建Release（可选）

1. 点击右侧的 "Releases"
2. 点击 "Create a new release"
3. 填写：
   - Tag: `v1.4.0`
   - Title: `v1.4.0 - 首次发布`
   - Description: 复制更新日志内容
4. 点击 "Publish release"

### 4. 分享给朋友

现在可以把仓库链接分享给朋友了：
```
https://github.com/你的用户名/media-renamer
```

他们可以：
```bash
git clone https://github.com/你的用户名/media-renamer.git
cd media-renamer
python3 app.py
```

---

## 💡 使用技巧

### 快速克隆

创建一个克隆命令，方便分享：
```cmd
git clone https://github.com/你的用户名/media-renamer.git && cd media-renamer && python app.py
```

### 添加README徽章

在README.md顶部添加：
```markdown
[![GitHub stars](https://img.shields.io/github/stars/你的用户名/media-renamer.svg)](https://github.com/你的用户名/media-renamer/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/你的用户名/media-renamer.svg)](https://github.com/你的用户名/media-renamer/network)
[![GitHub issues](https://img.shields.io/github/issues/你的用户名/media-renamer.svg)](https://github.com/你的用户名/media-renamer/issues)
```

---

## 🆘 需要帮助？

如果遇到问题：

1. 查看 `GitHub上传指南.md` 的详细说明
2. 检查Git是否正确安装
3. 检查网络连接
4. 查看错误信息并搜索解决方案

---

**准备好了吗？双击 `upload-to-github.bat` 开始上传！** 🚀
