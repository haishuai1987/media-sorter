#!/bin/bash
# 通过SSH更新服务器到v1.2.4

SERVER="192.168.51.105"
USER="root"  # 根据实际情况修改用户名

echo "=========================================="
echo "  更新服务器到 v1.2.4"
echo "=========================================="
echo ""

echo "🔗 连接到服务器 $SERVER..."
echo ""

# SSH到服务器并执行更新命令
ssh $USER@$SERVER << 'ENDSSH'
    echo "📂 进入项目目录..."
    cd /root/media-renamer || exit 1
    
    echo "🔄 拉取最新代码..."
    git pull origin main
    
    echo "📋 检查版本..."
    cat version.txt
    
    echo ""
    echo "🔄 重启服务..."
    pkill -f "python.*app.py" || true
    sleep 2
    
    echo "🚀 启动新版本..."
    nohup python3 app.py > /dev/null 2>&1 &
    
    echo ""
    echo "✅ 更新完成！"
    echo ""
    echo "验证服务状态："
    sleep 3
    ps aux | grep "python.*app.py" | grep -v grep
    
    echo ""
    echo "查看最新日志："
    tail -20 nohup.out
ENDSSH

echo ""
echo "=========================================="
echo "  ✅ 服务器更新完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 访问 http://192.168.51.105:5000"
echo "2. 重新运行文件整理"
echo "3. 验证Release Group已被移除"
echo ""
