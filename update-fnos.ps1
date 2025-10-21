# 通过SSH更新飞牛OS服务器
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  更新飞牛OS服务器 (192.168.51.105)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$server = "192.168.51.105"
$user = "root"  # 根据实际情况修改用户名

Write-Host "连接到服务器..." -ForegroundColor Yellow
Write-Host ""

# SSH命令
$commands = @"
cd /root/media-sorter && \
echo '当前目录: ' && pwd && \
echo '' && \
echo '[1/3] 拉取最新代码...' && \
git pull origin main && \
echo '✓ 拉取成功' && \
echo '' && \
echo '[2/3] 停止旧服务...' && \
pkill -f 'python.*app.py' && \
sleep 2 && \
echo '✓ 服务已停止' && \
echo '' && \
echo '[3/3] 启动新服务...' && \
nohup python3 app.py > app.log 2>&1 & && \
echo '✓ 服务已启动' && \
echo '' && \
echo '==========================================' && \
echo '  ✅ 更新完成！' && \
echo '==========================================' && \
echo '' && \
echo '访问地址: http://192.168.51.105:8090'
"@

ssh ${user}@${server} $commands

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  ✅ 更新成功！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "访问地址: http://192.168.51.105:8090" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ 更新失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动SSH连接后执行：" -ForegroundColor Yellow
    Write-Host "  ssh ${user}@${server}" -ForegroundColor White
    Write-Host "  cd /root/media-sorter" -ForegroundColor White
    Write-Host "  git pull origin main" -ForegroundColor White
    Write-Host "  pkill -f 'python.*app.py'" -ForegroundColor White
    Write-Host "  nohup python3 app.py > app.log 2>&1 &" -ForegroundColor White
    Write-Host ""
}

pause
