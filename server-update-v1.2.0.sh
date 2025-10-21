#!/bin/bash

# 媒体库文件管理器 v1.2.0 服务器更新脚本
# 用于在服务器上更新到最新版本

echo "========================================"
echo "媒体库文件管理器 - 服务器更新脚本"
echo "目标版本: v1.2.0"
echo "========================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "[1/6] 备份当前版本..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp app.py "$BACKUP_DIR/"
cp -r public "$BACKUP_DIR/" 2>/dev/null || true
cp version.txt "$BACKUP_DIR/" 2>/dev/null || true
echo "✓ 备份完成: $BACKUP_DIR"
echo ""

echo "[2/6] 停止服务..."
# 查找并停止运行中的服务
PID=$(ps aux | grep '[p]ython.*app.py' | awk '{print $2}')
if [ ! -z "$PID" ]; then
    echo "  发现运行中的进程: $PID"
    kill $PID
    sleep 2
    echo "✓ 服务已停止"
else
    echo "  没有运行中的服务"
fi
echo ""

echo "[3/6] 拉取最新代码..."
git fetch origin
git checkout main
git pull origin main
echo "✓ 代码更新完成"
echo ""

echo "[4/6] 检查版本..."
if [ -f "version.txt" ]; then
    NEW_VERSION=$(cat version.txt | tr -d '\n\r')
    echo "  当前版本: $NEW_VERSION"
else
    echo "  ⚠️  未找到version.txt"
fi
echo ""

echo "[5/6] 检查依赖..."
if command -v python3 &> /dev/null; then
    echo "  Python3: ✓"
else
    echo "  ❌ 未安装Python3"
    exit 1
fi
echo ""

echo "[6/6] 启动服务..."
nohup python3 app.py > media-renamer.log 2>&1 &
NEW_PID=$!
echo "  新进程ID: $NEW_PID"
sleep 3

# 检查服务是否启动成功
if ps -p $NEW_PID > /dev/null; then
    echo "✓ 服务启动成功"
else
    echo "❌ 服务启动失败，请检查日志: media-renamer.log"
    exit 1
fi
echo ""

echo "========================================"
echo "✅ 更新完成！"
echo "========================================"
echo ""
echo "版本: v1.2.0"
echo "进程ID: $NEW_PID"
echo "日志文件: media-renamer.log"
echo ""
echo "新功能："
echo "  - ✨ 实时日志推送"
echo "  - 🚀 元数据查询优化"
echo "  - 📊 识别准确率提升到90%+"
echo ""
echo "查看日志: tail -f media-renamer.log"
echo "停止服务: kill $NEW_PID"
echo ""
