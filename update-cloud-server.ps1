# 更新云服务器 8.134.215.137
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  更新云服务器 (8.134.215.137)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$serverUrl = "http://8.134.215.137:8000"

# 1. 检查服务器状态
Write-Host "[1/3] 检查服务器状态..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$serverUrl/api/system/version" -Method Get -TimeoutSec 5
    Write-Host "  当前版本: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  无法连接到服务器" -ForegroundColor Red
    Write-Host "  请确认服务器是否运行在 $serverUrl" -ForegroundColor Red
    pause
    exit 1
}

# 2. 触发强制更新
Write-Host ""
Write-Host "[2/3] 触发强制更新..." -ForegroundColor Yellow
try {
    $updateBody = @{
        force = $true
        use_proxy = $false
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$serverUrl/api/system/update" -Method Post -Body $updateBody -ContentType "application/json" -TimeoutSec 60
    
    if ($response.success) {
        Write-Host "  ✓ 更新成功！" -ForegroundColor Green
        Write-Host "  消息: $($response.message)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 更新失败: $($response.error)" -ForegroundColor Red
        pause
        exit 1
    }
} catch {
    Write-Host "  ✗ 更新请求失败: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

# 3. 等待服务重启
Write-Host ""
Write-Host "[3/3] 等待服务重启..." -ForegroundColor Yellow
Write-Host "  等待 5 秒..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 验证新版本
$maxRetries = 6
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries -and -not $success) {
    try {
        $response = Invoke-RestMethod -Uri "$serverUrl/api/system/version" -Method Get -TimeoutSec 5
        Write-Host "  ✓ 服务已重启，新版本: $($response.version)" -ForegroundColor Green
        $success = $true
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "  等待服务重启... ($retryCount/$maxRetries)" -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $success) {
    Write-Host "  ⚠️  无法验证新版本，请手动检查" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ 云服务器更新完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址: $serverUrl" -ForegroundColor Cyan
Write-Host ""

pause
