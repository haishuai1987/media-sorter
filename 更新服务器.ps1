# 更新服务器到 v1.2.0
$SERVER_URL = "http://192.168.51.100:8090"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  更新服务器到 v1.2.0" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查服务器状态
Write-Host "[1/4] 检查服务器状态..." -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "OK 服务器在线" -ForegroundColor Green
} catch {
    Write-Host "ERROR 服务器离线" -ForegroundColor Red
    Read-Host "按Enter退出"
    exit 1
}
Write-Host ""

# 2. 检查更新
Write-Host "[2/4] 检查是否有更新..." -ForegroundColor Yellow
$checkBody = '{"use_proxy": false}'
try {
    $checkResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/check-update" -Method Post -ContentType "application/json" -Body $checkBody -ErrorAction Stop
    
    Write-Host "当前版本: $($checkResponse.current_version)" -ForegroundColor Cyan
    Write-Host "有更新: $($checkResponse.has_update)" -ForegroundColor Cyan
    
    if ($checkResponse.has_update) {
        Write-Host "落后提交: $($checkResponse.commits_behind)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR 检查更新失败: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "按Enter退出"
    exit 1
}
Write-Host ""

if (-not $checkResponse.has_update) {
    Write-Host "已是最新版本，无需更新" -ForegroundColor Green
    Read-Host "按Enter退出"
    exit 0
}

# 3. 执行更新
Write-Host "[3/4] 执行更新..." -ForegroundColor Yellow
$updateBody = '{"use_proxy": false, "auto_restart": true}'
try {
    $updateResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/update" -Method Post -ContentType "application/json" -Body $updateBody -ErrorAction Stop
    
    if ($updateResponse.updated) {
        Write-Host "OK 更新成功" -ForegroundColor Green
        Write-Host "消息: $($updateResponse.message)" -ForegroundColor Cyan
    } else {
        Write-Host "WARN 更新失败: $($updateResponse.error)" -ForegroundColor Yellow
        Write-Host ""
        $forceUpdate = Read-Host "是否尝试强制更新? (y/n)"
        
        if ($forceUpdate -eq "y") {
            Write-Host ""
            Write-Host "执行强制更新..." -ForegroundColor Yellow
            $forceBody = '{"use_proxy": false, "auto_restart": true}'
            $forceResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $forceBody -ErrorAction Stop
            
            if ($forceResponse.updated) {
                Write-Host "OK 强制更新成功" -ForegroundColor Green
            } else {
                Write-Host "ERROR 强制更新失败: $($forceResponse.error)" -ForegroundColor Red
                Read-Host "按Enter退出"
                exit 1
            }
        } else {
            Read-Host "按Enter退出"
            exit 1
        }
    }
} catch {
    Write-Host "ERROR 更新请求失败: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "按Enter退出"
    exit 1
}
Write-Host ""

# 4. 等待服务重启
Write-Host "[4/4] 等待服务重启..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 验证服务
Write-Host "验证服务状态..." -ForegroundColor Yellow
$serviceUp = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
        Write-Host "OK 服务已恢复" -ForegroundColor Green
        $serviceUp = $true
        break
    } catch {
        Write-Host "等待服务启动... ($i/5)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $serviceUp) {
    Write-Host "WARN 服务可能需要更长时间启动" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  更新完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 访问 http://192.168.51.100:8090" -ForegroundColor White
Write-Host "2. 刷新浏览器 (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "3. 检查版本号是否为 v1.2.0" -ForegroundColor White
Write-Host "4. 测试实时日志推送功能" -ForegroundColor White
Write-Host ""
Read-Host "按Enter退出"
