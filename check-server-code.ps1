# 检查服务器代码并重启服务
$SERVER = "192.168.51.105"

Write-Host "检查服务器代码..." -ForegroundColor Cyan

# 检查关键代码行
Write-Host "`n1. 检查 get_category_dir 方法是否有修复..."
ssh root@$SERVER "grep -A 3 'def get_category_dir' /root/media-sorter/app.py | grep -A 2 '修复：处理None值'"

Write-Host "`n2. 检查 generate_output_path 调用是否修复..."
ssh root@$SERVER "grep -A 5 'self.generate_output_path' /root/media-sorter/app.py | grep '总是传递' | head -3"

Write-Host "`n3. 停止当前服务..."
ssh root@$SERVER "pkill -f 'python.*app.py' || true"

Write-Host "`n4. 等待3秒..."
Start-Sleep -Seconds 3

Write-Host "`n5. 启动服务..."
ssh root@$SERVER "cd /root/media-sorter && nohup python3 app.py > /dev/null 2>&1 &"

Write-Host "`n6. 等待5秒让服务启动..."
Start-Sleep -Seconds 5

Write-Host "`n7. 检查服务状态..."
try {
    $response = Invoke-WebRequest -Uri "http://$SERVER:8090" -Method Head -TimeoutSec 5
    Write-Host "[OK] 服务已启动" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 服务启动失败" -ForegroundColor Red
}

Write-Host "`n完成！" -ForegroundColor Green
