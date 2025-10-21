#!/bin/bash
# 飞牛OS服务器更新脚本 (192.168.51.105)

echo "=========================================="
echo "  更新飞牛OS服务器 (192.168.51.105)"
echo "=========================================="
echo ""

# 进入项目目录
cd /root/media-sorter || cd /home/media-sorter || cd ~/media-sorter

if [ $? -ne 0 ]; then
    echo "❌ 找不到项目目录"
    exit 1
fi

echo "当前目录: $(pwd)"
echo ""

# 1. 拉取最新代码
echo "[1/3] 拉取最新代码..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ 拉取失败"
    exit 1
fi
echo "✓ 拉取成功"
echo ""

# 2. 停止旧服务
echo "[2/3] 停止旧服务..."
pkill -f "python.*app.py"
sleep 2
echo "✓ 服务已停止"
echo ""

# 3. 启动新服务
echo "[3/3] 启动新服务..."
nohup python3 app.py > app.log 2>&1 &

if [ $? -eq 0 ]; then
    echo "✓ 服务已启动"
    echo ""
    echo "=========================================="
    echo "  ✅ 更新完成！"
    echo "=========================================="
    echo ""
    echo "访问地址: http://192.168.51.105:8090"
    echo "查看日志: tail -f app.log"
    echo ""
else
    echo "❌ 启动失败"
    exit 1
fi
