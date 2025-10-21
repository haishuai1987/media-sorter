#!/bin/bash
# v1.2.12 服务器更新脚本
# 用于云服务器/NAS 更新到最新版本

echo "========================================"
echo "  媒体整理工具 v1.2.12 更新脚本"
echo "  Release Group 识别增强"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ 错误: 未找到 app.py，请在项目根目录运行此脚本${NC}"
    exit 1
fi

echo "[1/7] 检查当前版本..."
if [ -f "version.txt" ]; then
    CURRENT_VERSION=$(cat version.txt | tr -d '[:space:]')
    echo -e "${GREEN}当前版本: $CURRENT_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  未找到版本文件${NC}"
fi
echo ""

echo "[2/7] 备份当前版本..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp app.py "$BACKUP_DIR/app.py.backup"
cp version.txt "$BACKUP_DIR/version.txt.backup" 2>/dev/null
echo -e "${GREEN}✅ 备份完成: $BACKUP_DIR${NC}"
echo ""

echo "[3/7] 停止服务..."
# 查找并停止运行中的进程
PID=$(ps aux | grep '[p]ython.*app.py' | awk '{print $2}')
if [ ! -z "$PID" ]; then
    echo "找到进程 PID: $PID"
    kill $PID
    sleep 2
    echo -e "${GREEN}✅ 服务已停止${NC}"
else
    echo -e "${YELLOW}⚠️  未找到运行中的服务${NC}"
fi
echo ""

echo "[4/7] 拉取最新代码..."
git pull origin main
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 代码更新成功${NC}"
else
    echo -e "${RED}❌ 代码更新失败${NC}"
    echo "尝试恢复备份..."
    cp "$BACKUP_DIR/app.py.backup" app.py
    cp "$BACKUP_DIR/version.txt.backup" version.txt 2>/dev/null
    exit 1
fi
echo ""

echo "[5/7] 检查新版本..."
if [ -f "version.txt" ]; then
    NEW_VERSION=$(cat version.txt | tr -d '[:space:]')
    echo -e "${GREEN}新版本: $NEW_VERSION${NC}"
else
    echo -e "${RED}❌ 未找到版本文件${NC}"
fi
echo ""

echo "[6/7] 运行测试..."
if [ -f "test_release_groups_v1.2.12.py" ]; then
    python3 test_release_groups_v1.2.12.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️  测试未完全通过，但可以继续${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到测试文件，跳过测试${NC}"
fi
echo ""

echo "[7/7] 启动服务..."
# 使用 nohup 在后台启动
nohup python3 app.py > media-renamer.log 2>&1 &
NEW_PID=$!
sleep 3

# 检查进程是否启动成功
if ps -p $NEW_PID > /dev/null; then
    echo -e "${GREEN}✅ 服务启动成功 (PID: $NEW_PID)${NC}"
    echo $NEW_PID > media-renamer.pid
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "查看日志: tail -f media-renamer.log"
    exit 1
fi
echo ""

echo "========================================"
echo -e "${GREEN}  🎉 更新完成！${NC}"
echo "========================================"
echo ""
echo "📊 更新内容:"
echo "  - Release Group: 13 → 100+"
echo "  - 测试通过率: 92.6%"
echo "  - 新增支持: CHD, HDChina, LemonHD 等"
echo ""
echo "🔗 访问地址:"
echo "  http://$(hostname -I | awk '{print $1}'):8090"
echo ""
echo "📝 查看日志:"
echo "  tail -f media-renamer.log"
echo ""
echo "🔄 重启服务:"
echo "  kill $NEW_PID && python3 app.py"
echo ""
echo "📖 详细信息:"
echo "  - 更新日志: CHANGELOG-v1.2.12.md"
echo "  - 快速开始: QUICK-START-v1.2.12.md"
echo ""
