# 立即更新服务器到v1.2.4
# 服务器: 192.168.51.105
# 用户: haishuai

$SERVER = "192.168.51.105"
$USER = "haishuai"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  更新服务器到 v1.2.4" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔗 连接到服务器 $SERVER..." -ForegroundColor Yellow
Write-Host "用户: $USER" -ForegroundColor Yellow
Write-Host ""

# SSH命令
$commands = @"
cd /root/media-renamer
echo '📂 当前目录:'
pwd
echo ''
echo '🔄 拉取最新代码...'
git pull origin main
echo ''
echo '📋 当前版本:'
cat version.txt
echo ''
echo '🔄 停止旧服务...'
pkill -f 'python.*app.py' || echo '没有运行的服务'
sleep 2
echo '🚀 启动新版本...'
nohup python3 app.py > app.log 2>&1 &
sleep 3
echo ''
echo '✅ 更新完成！'
echo ''
echo '📊 验证服务状态:'
ps aux | grep 'python.*app.py' | grep -v grep || echo '⚠️ 服务未启动'
echo ''
echo '📝 最新日志:'
tail -20 app.log
"@

# 执行SSH命令
ssh "$USER@$SERVER" $commands

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  ✅ 更新完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "1. 访问 http://192.168.51.105:5000"
Write-Host "2. 重新运行文件整理"
Write-Host "3. 验证Release Group已被移除"
Write-Host ""

pause
