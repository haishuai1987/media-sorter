#!/bin/bash

echo "=========================================="
echo "  部署智能强制更新功能"
echo "=========================================="
echo ""

cd ~/media-sorter

echo "=== 1. 拉取最新代码 ==="
git fetch origin
git reset --hard origin/main
echo ""

echo "=== 2. 检查版本 ==="
cat version.txt
echo ""

echo "=== 3. 验证文件更新 ==="
echo "检查是否包含强制更新功能："
if grep -q "async function forceUpdate" index.html; then
    echo "✅ index.html 已包含强制更新功能"
else
    echo "❌ index.html 未包含强制更新功能"
fi

if grep -q "async function forceUpdate" public/index.html; then
    echo "✅ public/index.html 已包含强制更新功能"
else
    echo "❌ public/index.html 未包含强制更新功能"
fi
echo ""

echo "=== 4. 停止旧服务 ==="
pkill -f "python3 app.py"
sleep 2
echo ""

echo "=== 5. 启动新服务 ==="
nohup python3 app.py > app.log 2>&1 &
sleep 3
echo ""

echo "=== 6. 验证服务状态 ==="
curl -I http://localhost:8090
echo ""

echo "=== 7. 查看最新日志 ==="
tail -10 app.log
echo ""

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo "1. 在浏览器中按 Ctrl+Shift+R 强制刷新页面"
echo "2. 检查'系统更新配置'中的'当前版本'是否正常显示"
echo "3. 测试更新功能是否正常"
echo ""
echo "🧪 测试方法："
echo "   # 模拟本地修改冲突"
echo "   echo 'test' >> ~/media-sorter/README.md"
echo "   # 然后在浏览器中点击'检查更新'按钮"
echo "   # 应该会看到智能强制更新提示"
echo ""
echo "✅ 本次更新内容："
echo "   1. 智能强制更新功能 - 更新失败时自动提示强制更新"
echo "   2. 修复版本号显示问题 - '当前版本'不再显示'获取失败'"
echo ""
