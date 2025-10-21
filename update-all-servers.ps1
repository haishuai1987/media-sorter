# 一键更新所有服务器
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  一键更新所有服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$servers = @(
    @{Name="本地服务器"; Url="http://192.168.51.105:8090"},
    @{Name="云服务器"; Url="http://8.134.215.137:8000"}
)

foreach ($server in $servers) {
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "  更新: $($server.Name)" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host ""
    
    # 检查状态
    Write-Host "检查服务器状态..." -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$($server.Url)/api/system/version" -Method Get -TimeoutSec 5
        Write-Host "  当前版本: $($response.version)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ 无法连接，跳过" -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    # 触发更新
    Write-Host "触发更新..." -ForegroundColor Gray
    try {
        $updateBody = @{
            force = $true
            use_proxy = $false
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$($server.Url)/api/system/update" -Method Post -Body $updateBody -ContentType "application/json" -TimeoutSec 60
        
        if ($response.success) {
            Write-Host "  ✓ 更新成功！" -ForegroundColor Green
        } else {
            Write-Host "  ✗ 更新失败: $($response.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ 更新失败: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ 所有服务器更新完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pause
