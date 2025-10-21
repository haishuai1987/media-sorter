# PowerShell版本 - 通过SSH更新服务器到v1.2.4

$SERVER = "192.168.51.105"
$USER = "root"  # 根据实际情况修改用户名

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  更新服务器到 v1.2.4" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔗 连接到服务器 $SERVER..." -ForegroundColor Yellow
Write-Host ""

# 创建SSH命令
$sshCommand = @"
cd /root/media-renamer && \
echo '📂 当前目录:' && pwd && \
echo '' && \
echo '🔄 拉取最新代码...' && \
git pull origin main && \
echo '' && \
echo '📋 当前版本:' && \
cat version.txt && \
echo '' && \
echo '🔄 重启服务...' && \
pkill -f 'python.*app.py' || true && \
sleep 2 && \
echo '🚀 启动新版本...' && \
nohup python3 app.py > /dev/null 2>&1 & && \
sleep 3 && \
echo '' && \
echo '✅ 更新完成！' && \
echo '' && \
echo '验证服务状态:' && \
ps aux | grep 'python.*app.py' | grep -v grep && \
echo '' && \
echo '查看最新日志:' && \
tail -20 nohup.out
"@

# 执行SSH命令
ssh "$USER@$SERVER" $sshCommand

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  ✅ 服务器更新完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "1. 访问 http://192.168.51.105:5000"
Write-Host "2. 重新运行文件整理"
Write-Host "3. 验证Release Group已被移除"
Write-Host ""
