#!/bin/bash
# 更新服务器到v1.2.4
# 服务器: 192.168.51.105
# 用户: haishuai -> sudo -i -> root

SERVER="192.168.51.105"
USER="haishuai"
PASSWORD="China1987"

echo "=========================================="
echo "  更新服务器到 v1.2.4"
echo "=========================================="
echo ""

echo "🔗 连接到服务器 $SERVER..."
echo "用户: $USER"
echo ""

# 使用sshpass（如果可用）
if command -v sshpass &> /dev/null; then
    echo "使用sshpass自动登录..."
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" << 'ENDSSH'
        echo "🔐 切换到root用户..."
        echo "China1987" | sudo -S -i bash << 'ENDROOT'
            echo "📂 进入项目目录..."
            cd /root/media-renamer || exit 1
            
            echo "🔄 拉取最新代码..."
            git pull origin main
            
            echo ""
            echo "📋 当前版本:"
            cat version.txt
            
            echo ""
            echo "🔄 停止旧服务..."
            pkill -f "python.*app.py" || echo "没有运行的服务"
            sleep 2
            
            echo "🚀 启动新版本..."
            nohup python3 app.py > app.log 2>&1 &
            sleep 3
            
            echo ""
            echo "✅ 更新完成！"
            
            echo ""
            echo "📊 验证服务状态:"
            ps aux | grep "python.*app.py" | grep -v grep || echo "⚠️ 服务未启动"
            
            echo ""
            echo "📝 最新日志:"
            tail -20 app.log
ENDROOT
ENDSSH
else
    echo "⚠️ 未找到sshpass工具"
    echo ""
    echo "请手动执行以下步骤："
    echo ""
    echo "1. SSH连接到服务器:"
    echo "   ssh $USER@$SERVER"
    echo "   密码: $PASSWORD"
    echo ""
    echo "2. 切换到root:"
    echo "   sudo -i"
    echo "   密码: $PASSWORD"
    echo ""
    echo "3. 进入项目目录:"
    echo "   cd /root/media-renamer"
    echo ""
    echo "4. 拉取最新代码:"
    echo "   git pull origin main"
    echo ""
    echo "5. 检查版本:"
    echo "   cat version.txt"
    echo ""
    echo "6. 重启服务:"
    echo "   pkill -f \"python.*app.py\""
    echo "   sleep 2"
    echo "   nohup python3 app.py > app.log 2>&1 &"
    echo ""
    echo "7. 验证服务:"
    echo "   ps aux | grep \"python.*app.py\" | grep -v grep"
    echo "   tail -20 app.log"
    echo ""
fi

echo ""
echo "=========================================="
echo "  ✅ 更新流程完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 访问 http://192.168.51.105:5000"
echo "2. 重新运行文件整理"
echo "3. 验证Release Group已被移除"
echo ""
