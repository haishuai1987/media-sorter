#!/bin/bash
# 飞牛OS/NAS Web更新诊断脚本

echo "========================================"
echo "飞牛OS - Web更新诊断工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ 错误：请在项目根目录运行此脚本${NC}"
    echo "当前目录: $(pwd)"
    exit 1
fi

echo "1. 检查部署环境"
echo "----------------------------------------"
echo "当前目录: $(pwd)"
echo "用户: $(whoami)"
echo "系统: $(uname -a)"
echo ""

echo "2. 检查Git仓库"
echo "----------------------------------------"
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git仓库存在${NC}"
    
    # 检查远程仓库
    echo ""
    echo "远程仓库配置:"
    git remote -v
    
    # 检查当前分支
    echo ""
    echo "当前分支:"
    git branch
    
    # 检查未提交的修改
    echo ""
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  检测到未提交的修改:${NC}"
        git status --short
    else
        echo -e "${GREEN}✅ 工作目录干净${NC}"
    fi
else
    echo -e "${RED}❌ 不是Git仓库${NC}"
    echo "解决方案: 使用 git clone 重新安装"
    exit 1
fi

echo ""
echo "3. 检查网络连接"
echo "----------------------------------------"

# 测试GitHub连接
echo "测试GitHub连接..."
if timeout 30 git ls-remote --heads origin > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 可以连接到GitHub${NC}"
else
    echo -e "${RED}❌ 无法连接到GitHub${NC}"
    echo "可能原因:"
    echo "  1. 网络问题"
    echo "  2. 需要配置代理"
    echo "  3. 防火墙限制"
fi

echo ""
echo "4. 检查Python环境"
echo "----------------------------------------"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3已安装${NC}"
    python3 --version
else
    echo -e "${RED}❌ Python3未安装${NC}"
fi

# 检查必要的Python包
echo ""
echo "检查Python依赖:"
python3 -c "import requests" 2>/dev/null && echo -e "${GREEN}✅ requests${NC}" || echo -e "${YELLOW}⚠️  requests未安装${NC}"

echo ""
echo "5. 检查服务状态"
echo "----------------------------------------"
if pgrep -f "python.*app.py" > /dev/null; then
    echo -e "${GREEN}✅ 服务正在运行${NC}"
    echo "进程信息:"
    ps aux | grep "[p]ython.*app.py"
else
    echo -e "${YELLOW}⚠️  服务未运行${NC}"
fi

echo ""
echo "6. 检查文件权限"
echo "----------------------------------------"
if [ -w "." ]; then
    echo -e "${GREEN}✅ 当前目录可写${NC}"
else
    echo -e "${RED}❌ 当前目录不可写${NC}"
    echo "当前权限: $(ls -ld .)"
fi

echo ""
echo "7. 测试更新命令"
echo "----------------------------------------"
echo "测试 git fetch (dry-run)..."
if git fetch origin --dry-run 2>&1; then
    echo -e "${GREEN}✅ git fetch 测试成功${NC}"
else
    echo -e "${RED}❌ git fetch 测试失败${NC}"
fi

echo ""
echo "========================================"
echo "诊断完成"
echo "========================================"
echo ""
echo "常见问题解决方案:"
echo ""
echo "1. 如果无法连接GitHub:"
echo "   - 在Web界面设置中配置代理"
echo "   - 或手动执行: git config --global http.proxy http://代理地址:端口"
echo ""
echo "2. 如果有未提交的修改:"
echo "   - 使用Web界面的'强制更新'功能"
echo "   - 或手动执行: git reset --hard HEAD"
echo ""
echo "3. 如果权限不足:"
echo "   - 检查目录所有者: ls -la"
echo "   - 修改权限: sudo chown -R $(whoami) ."
echo ""
echo "4. 手动更新命令:"
echo "   cd $(pwd)"
echo "   git pull origin main"
echo ""
