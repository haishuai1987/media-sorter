# 远程服务器信息
$SERVER_URL = "http://192.168.51.100:8090"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  通过 API 推送更新到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== 1. 检查服务器状态 ===" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ 服务器在线" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器离线或无法访问" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "=== 2. 检查是否有更新 ===" -ForegroundColor Yellow
try {
    $checkBody = @{
        use_proxy = $false
    } | ConvertTo-Json

    $checkResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/check-update" `
        -Method Post `
        -ContentType "application/json" `
        -Body $checkBody

    Write-Host ($checkResponse | ConvertTo-Json -Depth 10)
    Write-Host ""

    if ($checkResponse.has_update -eq $true) {
        Write-Host "✅ 发现新版本！" -ForegroundColor Green
        Write-Host "   当前版本: $($checkResponse.current_version)" -ForegroundColor Cyan
        Write-Host "   落后提交: $($checkResponse.commits_behind) 个" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "=== 3. 执行更新 ===" -ForegroundColor Yellow
        $updateBody = @{
            use_proxy = $false
            auto_restart = $true
        } | ConvertTo-Json

        $updateResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/update" `
            -Method Post `
            -ContentType "application/json" `
            -Body $updateBody

        Write-Host ($updateResponse | ConvertTo-Json -Depth 10)
        Write-Host ""

        if ($updateResponse.updated -eq $true) {
            Write-Host "✅ 更新成功！" -ForegroundColor Green
            Write-Host ""
            Write-Host "⏳ 等待服务重启..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10

            Write-Host "=== 4. 验证服务状态 ===" -ForegroundColor Yellow
            $retries = 5
            $serviceUp = $false
            
            for ($i = 1; $i -le $retries; $i++) {
                try {
                    $testResponse = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
                    Write-Host "✅ 服务已恢复正常" -ForegroundColor Green
                    $serviceUp = $true
                    break
                } catch {
                    Write-Host "⏳ 等待服务启动... ($i/$retries)" -ForegroundColor Yellow
                    Start-Sleep -Seconds 3
                }
            }

            if (-not $serviceUp) {
                Write-Host "⚠️  服务可能需要更长时间启动，请稍后手动检查" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ 更新失败: $($updateResponse.error)" -ForegroundColor Red
            Write-Host ""
            
            $forceUpdate = Read-Host "💡 是否尝试强制更新？(y/n)"
            
            if ($forceUpdate -eq "y" -or $forceUpdate -eq "Y") {
                Write-Host ""
                Write-Host "=== 执行强制更新 ===" -ForegroundColor Yellow
                
                $forceBody = @{
                    use_proxy = $false
                    auto_restart = $true
                } | ConvertTo-Json

                $forceResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" `
                    -Method Post `
                    -ContentType "application/json" `
                    -Body $forceBody

                Write-Host ($forceResponse | ConvertTo-Json -Depth 10)
                Write-Host ""

                if ($forceResponse.updated -eq $true) {
                    Write-Host "✅ 强制更新成功！" -ForegroundColor Green
                    Write-Host ""
                    Write-Host "⏳ 等待服务重启..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 10

                    Write-Host "=== 验证服务状态 ===" -ForegroundColor Yellow
                    for ($i = 1; $i -le 5; $i++) {
                        try {
                            $testResponse = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
                            Write-Host "✅ 服务已恢复正常" -ForegroundColor Green
                            break
                        } catch {
                            Write-Host "⏳ 等待服务启动... ($i/5)" -ForegroundColor Yellow
                            Start-Sleep -Seconds 3
                        }
                    }
                } else {
                    Write-Host "❌ 强制更新失败: $($forceResponse.error)" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "ℹ️  已是最新版本，无需更新" -ForegroundColor Cyan
        Write-Host "   当前版本: $($checkResponse.current_version)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ 操作失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  操作完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 提示：" -ForegroundColor Yellow
Write-Host "   - 请在浏览器中按 Ctrl+Shift+R 强制刷新页面" -ForegroundColor White
Write-Host "   - 检查'系统更新配置'中的'当前版本'是否正常显示" -ForegroundColor White
Write-Host ""
