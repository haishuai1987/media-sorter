#!/bin/bash
# GitHub上传脚本

echo "=========================================="
echo "  媒体库文件管理器 - GitHub上传助手"
echo "=========================================="
echo ""

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo "❌ 错误: 未安装Git"
    echo "请先安装Git: https://git-scm.com/"
    exit 1
fi

echo "✅ Git已安装"
echo ""

# 检查是否已初始化
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
    echo "✅ Git仓库已初始化"
else
    echo "✅ Git仓库已存在"
fi
echo ""

# 配置Git用户信息
echo "⚙️  配置Git用户信息"
read -p "请输入你的GitHub用户名: " username
read -p "请输入你的GitHub邮箱: " email

git config user.name "$username"
git config user.email "$email"
echo "✅ Git用户信息已配置"
echo ""

# 添加文件
echo "📝 添加文件到Git..."
git add .
echo "✅ 文件已添加"
echo ""

# 提交
echo "💾 提交更改..."
git commit -m "Initial commit: 媒体库文件管理器 v1.4

- 智能重命名功能
- 中文标题识别（豆瓣+TMDB）
- 智能去重
- 智能分类
- 冲突处理
- 自动清理
- 实时进度监控
- 独立配置管理
- 完整文档
- Linux/NAS优化"

echo "✅ 更改已提交"
echo ""

# 添加远程仓库
echo "🔗 添加远程仓库"
echo ""
echo "请先在GitHub上创建一个新仓库："
echo "1. 访问 https://github.com/new"
echo "2. Repository name: media-renamer"
echo "3. Description: 智能媒体文件整理工具"
echo "4. 选择 Public 或 Private"
echo "5. 不要勾选 'Initialize this repository with a README'"
echo "6. 点击 'Create repository'"
echo ""
read -p "创建完成后，请输入仓库URL (例如: https://github.com/username/media-renamer.git): " repo_url

git remote add origin "$repo_url"
echo "✅ 远程仓库已添加"
echo ""

# 推送到GitHub
echo "🚀 推送到GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ 上传成功！"
    echo "=========================================="
    echo ""
    echo "你的仓库地址："
    echo "$repo_url"
    echo ""
    echo "下一步："
    echo "1. 访问你的GitHub仓库"
    echo "2. 添加仓库描述和Topics"
    echo "3. 创建第一个Release（可选）"
    echo ""
else
    echo ""
    echo "❌ 上传失败"
    echo "请检查："
    echo "1. 仓库URL是否正确"
    echo "2. 是否有权限访问该仓库"
    echo "3. 网络连接是否正常"
    echo ""
    echo "你也可以手动推送："
    echo "git push -u origin main"
fi
