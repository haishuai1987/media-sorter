# GitHub上传指南

## 📋 准备工作

### 1. 检查文件

确保以下文件已准备好：

- ✅ `.gitignore` - 忽略不需要上传的文件
- ✅ `LICENSE` - MIT许可证
- ✅ `README.md` - 项目说明
- ✅ `CONTRIBUTING.md` - 贡献指南
- ✅ 核心代码文件（app.py, index.html等）
- ✅ 文档文件（docs/目录）

### 2. 清理敏感信息

**重要**：确保删除或替换敏感信息！

编辑 `app.py`，替换默认配置：

```python
# 默认配置
DEFAULT_CONFIG = {
    'tmdb_api_key': '',  # 留空，让用户自己配置
    'tmdb_proxy': '',
    'tmdb_proxy_type': 'http',
    'douban_cookie': ''  # 留空，让用户自己配置
}
```

---

## 🚀 上传步骤

### 方法1: 使用GitHub Desktop（推荐新手）

#### 1. 安装GitHub Desktop
- 下载：https://desktop.github.com/
- 安装并登录GitHub账号

#### 2. 创建GitHub仓库
1. 访问 https://github.com/
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - Repository name: `media-renamer`
   - Description: `智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别`
   - Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

#### 3. 使用GitHub Desktop上传
1. 打开GitHub Desktop
2. File → Add Local Repository
3. 选择你的项目文件夹
4. 点击 "Publish repository"
5. 选择刚创建的仓库
6. 点击 "Publish"

### 方法2: 使用Git命令行

#### 1. 安装Git
```bash
# Windows
# 下载安装：https://git-scm.com/download/win

# Linux
sudo apt install git  # Ubuntu/Debian
sudo yum install git  # CentOS/RHEL
```

#### 2. 配置Git
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

#### 3. 创建GitHub仓库
1. 访问 https://github.com/
2. 点击右上角 "+" → "New repository"
3. 填写信息（同上）
4. 点击 "Create repository"
5. **复制仓库URL**（例如：https://github.com/username/media-renamer.git）

#### 4. 初始化本地仓库
```bash
# 进入项目目录
cd E:\media-renamer

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 媒体库文件管理器 v1.4"
```

#### 5. 连接远程仓库并推送
```bash
# 添加远程仓库（替换为你的仓库URL）
git remote add origin https://github.com/你的用户名/media-renamer.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

---

## 📝 上传后的配置

### 1. 添加仓库描述

在GitHub仓库页面：
1. 点击右上角的 "⚙️ Settings"
2. 在 "About" 部分添加：
   - Description: `智能媒体文件整理工具 - 自动重命名、智能分类、去重、中文标题识别`
   - Website: 你的网站（如果有）
   - Topics: `python`, `media`, `renamer`, `nas`, `tmdb`, `douban`

### 2. 设置GitHub Pages（可选）

如果想要项目主页：
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main → /docs
4. Save

### 3. 添加徽章（可选）

在 `README.md` 顶部添加：

```markdown
[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/你的用户名/media-renamer.svg)](https://github.com/你的用户名/media-renamer/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/你的用户名/media-renamer.svg)](https://github.com/你的用户名/media-renamer/issues)
```

---

## 🔒 安全检查清单

上传前务必检查：

- [ ] 删除或替换了默认的TMDB API Key
- [ ] 删除或替换了默认的豆瓣Cookie
- [ ] 删除了个人配置文件（~/.media-renamer/config.json）
- [ ] 删除了测试文件和临时文件
- [ ] 检查了 `.gitignore` 是否正确
- [ ] 没有包含任何密码或敏感信息

---

## 📦 发布Release（可选）

### 创建第一个Release

1. 在GitHub仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写信息：
   - Tag version: `v1.4.0`
   - Release title: `v1.4.0 - 首次发布`
   - Description: 
     ```markdown
     ## 🎉 首次发布
     
     ### 核心功能
     - ✅ 智能重命名
     - ✅ 中文标题识别（豆瓣+TMDB）
     - ✅ 智能去重
     - ✅ 智能分类
     - ✅ 冲突处理
     - ✅ 自动清理
     - ✅ 实时进度监控
     - ✅ 独立配置管理
     
     ### 系统支持
     - Ubuntu, Debian, CentOS
     - Synology DSM, QNAP QTS
     - TrueNAS, Unraid
     - Docker支持
     
     ### 安装
     ```bash
     git clone https://github.com/你的用户名/media-renamer.git
     cd media-renamer
     chmod +x install.sh
     ./install.sh
     ```
     
     查看 [快速开始](docs/快速开始.md) 了解更多。
     ```
4. 点击 "Publish release"

---

## 🔄 后续更新

### 更新代码

```bash
# 修改代码后

# 查看修改
git status

# 添加修改
git add .

# 提交
git commit -m "描述你的修改"

# 推送到GitHub
git push
```

### 创建新版本

```bash
# 创建标签
git tag -a v1.4.1 -m "版本 1.4.1"

# 推送标签
git push origin v1.4.1
```

然后在GitHub上创建对应的Release。

---

## 📊 仓库维护

### 定期任务

1. **回复Issue**：及时回复用户问题
2. **审查PR**：审查并合并Pull Request
3. **更新文档**：保持文档最新
4. **发布更新**：定期发布新版本

### 推荐设置

1. **启用Issue模板**
   - Settings → Features → Issues → Set up templates

2. **启用PR模板**
   - 创建 `.github/pull_request_template.md`

3. **添加CI/CD**（可选）
   - 使用GitHub Actions自动测试

---

## 🎯 推广建议

### 1. 完善README
- 添加截图
- 添加演示视频
- 添加使用示例

### 2. 社交媒体
- 在相关社区分享
- 写博客介绍
- 制作教程视频

### 3. 标签优化
添加相关标签：
- `python`
- `media-management`
- `file-renamer`
- `nas`
- `plex`
- `jellyfin`
- `emby`
- `tmdb`
- `douban`

---

## ❓ 常见问题

### Q: 如何删除已上传的敏感信息？

**A**: 如果不小心上传了敏感信息：

1. **立即更改密码/密钥**
2. **删除文件并提交**：
   ```bash
   git rm --cached 敏感文件
   git commit -m "Remove sensitive file"
   git push
   ```
3. **清理历史记录**（如果需要）：
   ```bash
   # 使用 BFG Repo-Cleaner 或 git filter-branch
   ```

### Q: 如何设置为私有仓库？

**A**: 
1. Settings → Danger Zone
2. Change repository visibility
3. Make private

### Q: 如何允许他人贡献？

**A**: 
1. 确保仓库是公开的
2. 添加 `CONTRIBUTING.md`
3. 在README中说明如何贡献
4. 及时回复Issue和PR

---

## 📞 获取帮助

- **GitHub文档**: https://docs.github.com/
- **Git教程**: https://git-scm.com/book/zh/v2
- **GitHub Desktop**: https://docs.github.com/en/desktop

---

## ✅ 完成检查清单

上传完成后检查：

- [ ] 仓库已创建
- [ ] 代码已上传
- [ ] README显示正常
- [ ] 文档链接正常
- [ ] 没有敏感信息
- [ ] License已添加
- [ ] .gitignore正常工作
- [ ] 仓库描述已添加
- [ ] Topics已添加
- [ ] 第一个Release已创建（可选）

---

**恭喜！你的项目已成功上传到GitHub！** 🎉

现在可以分享给朋友了：
```
https://github.com/你的用户名/media-renamer
```
