#!/bin/bash
# GitHub上传脚本 (Linux/NAS)

echo "=========================================="
echo "  媒体库文件管理器 - GitHub上传助手"
echo "=========================================="
echo ""

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo "❌ 错误: 未安装Git"
    echo "请先安装Git: sudo apt-get install git"
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

# 配置Git用户信息（如果未配置）
if [ -z "$(git config user.name)" ]; then
    echo "⚙️  配置Git用户信息"
    read -p "请输入你的GitHub用户名: " username
    read -p "请输入你的GitHub邮箱: " email
    
    git config user.name "$username"
    git config user.email "$email"
    echo "✅ Git用户信息已配置"
    echo ""
fi

# 递增版本号
echo "🔢 递增版本号..."
if python3 increment_version.py; then
    NEW_VERSION=$(cat version.txt)
    echo "✅ 版本号已更新: $NEW_VERSION"
else
    echo "⚠️  版本号递增失败，继续上传..."
    NEW_VERSION="v1.0.0"
fi
echo ""

# 添加文件
echo "📝 添加文件到Git..."
git add .
echo "✅ 文件已添加"
echo ""

# 提交
echo "💾 提交更改..."
git commit -m "Update to $NEW_VERSION"
if [ $? -eq 0 ]; then
    echo "✅ 更改已提交"
else
    echo "⚠️  没有需要提交的更改"
fi
echo ""

# 检查远程仓库
if ! git remote | grep -q "origin"; then
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
    read -p "创建完成后，请输入仓库URL: " repo_url
    
    git remote add origin "$repo_url"
    echo "✅ 远程仓库已添加"
    echo ""
fi

# 推送到GitHub
echo "🚀 推送到GitHub..."
git branch -M main

# 尝试直连推送
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "  ✅ 上传成功！"
    echo "=========================================="
    echo ""
    echo "当前版本: $NEW_VERSION"
    echo ""
    echo "下一步："
    echo "1. 在飞牛NAS上测试Web更新功能"
    echo "2. 打开Web界面，点击'更新'按钮"
    echo "3. 系统会自动拉取最新代码"
    echo ""
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因："
    echo "1. 网络连接问题"
    echo "2. 需要配置GitHub访问令牌"
    echo "3. 仓库权限问题"
    echo ""
    echo "解决方案："
    echo "1. 配置代理: git config --global http.proxy http://proxy:port"
    echo "2. 或使用SSH: git remote set-url origin git@github.com:username/repo.git"
    echo "3. 或手动推送: git push -u origin main"
    echo ""
fi
