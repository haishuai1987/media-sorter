# 一键强制更新服务器

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "一键强制更新服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "正在执行强制更新..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://192.168.51.105:8090/api/force-update" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"use_proxy":false,"auto_restart":true}' `
        -TimeoutSec 60
    
    if ($response.updated) {
        Write-Host "`n✅ 更新成功！" -ForegroundColor Green
        Write-Host "   新版本: $($response.new_version)" -ForegroundColor White
        Write-Host "   $($response.message)`n" -ForegroundColor White
        
        Write-Host "等待服务重启..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        Write-Host "`n验证服务..." -ForegroundColor Yellow
        $test = Invoke-RestMethod -Uri "http://192.168.51.105:8090/api/get-version" -Method POST -ContentType "application/json" -Body '{}'
        Write-Host "✅ 服务已恢复，当前版本: $($test.current_version)`n" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️ $($response.message)`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "`n❌ 更新失败: $($_.Exception.Message)`n" -ForegroundColor Red
}

Write-Host "========================================`n" -ForegroundColor Cyan
