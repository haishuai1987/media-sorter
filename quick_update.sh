#!/bin/bash
# 快速更新脚本 - 在服务器上运行

echo "================================"
echo "媒体库管理器 - 快速更新"
echo "================================"
echo ""

# 1. 进入项目目录
cd ~/media-sorter || cd /root/media-sorter || {
    echo "❌ 找不到项目目录"
    echo "请手动进入项目目录后运行此脚本"
    exit 1
}

echo "📁 当前目录: $(pwd)"
echo ""

# 2. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull 失败"
    echo "尝试解决冲突..."
    git stash
    git pull origin main
    git stash pop
fi

echo ""

# 3. 停止旧服务
echo "🛑 停止旧服务..."
pkill -f "python.*app.py" 2>/dev/null
sleep 2

echo ""

# 4. 启动新服务
echo "🚀 启动新服务..."
nohup python3 app.py > app.log 2>&1 &

sleep 3

echo ""

# 5. 检查服务状态
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ 服务启动成功"
    echo ""
    echo "📊 进程信息:"
    ps aux | grep "python.*app.py" | grep -v grep
else
    echo "❌ 服务启动失败"
    echo "查看日志: tail -f app.log"
    exit 1
fi

echo ""

# 6. 测试API
echo "🧪 测试新API端点..."
if [ -f "test_qrcode_api.py" ]; then
    python3 test_qrcode_api.py
else
    echo "⚠️  测试脚本不存在，跳过测试"
fi

echo ""
echo "================================"
echo "✅ 更新完成！"
echo "================================"
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}'):8090"
echo "查看日志: tail -f app.log"
echo ""
