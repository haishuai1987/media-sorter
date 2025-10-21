# 完整部署流程：推送 + 更新所有服务器
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  v1.2.11 完整部署流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 推送到GitHub
Write-Host "[步骤 1/2] 推送到 GitHub..." -ForegroundColor Yellow
Write-Host ""

git add app.py test_title_cleaning.py DEPLOY-v1.2.11.ps1 update-local-server.ps1 update-cloud-server.ps1 update-all-servers.ps1 HOTFIX-v1.2.11.md

git commit -m "fix: v1.2.11 - 修复TMDB标题清理，只保留中文标题"

"v1.2.11" | Out-File -FilePath version.txt -Encoding utf8 -NoNewline
git add version.txt
git commit -m "chore: bump version to v1.2.11"

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ GitHub 推送成功！" -ForegroundColor Green
} else {
    Write-Host "✗ GitHub 推送失败" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "等待 3 秒后开始更新服务器..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Write-Host ""

# 步骤2: 更新所有服务器
Write-Host "[步骤 2/2] 更新所有服务器..." -ForegroundColor Yellow
Write-Host ""

$servers = @(
    @{Name="本地服务器"; Url="http://192.168.51.105:8090"},
    @{Name="云服务器"; Url="http://8.134.215.137:8000"}
)

foreach ($server in $servers) {
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "  $($server.Name): $($server.Url)" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host ""
    
    # 检查状态
    Write-Host "  [1/3] 检查状态..." -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$($server.Url)/api/system/version" -Method Get -TimeoutSec 5
        Write-Host "    当前版本: $($response.version)" -ForegroundColor White
    } catch {
        Write-Host "    ✗ 无法连接，跳过" -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    # 触发更新
    Write-Host "  [2/3] 触发更新..." -ForegroundColor Gray
    try {
        $updateBody = @{
            force = $true
            use_proxy = $false
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$($server.Url)/api/system/update" -Method Post -Body $updateBody -ContentType "application/json" -TimeoutSec 60
        
        if ($response.success) {
            Write-Host "    ✓ 更新成功" -ForegroundColor Green
        } else {
            Write-Host "    ✗ 更新失败: $($response.error)" -ForegroundColor Red
            Write-Host ""
            continue
        }
    } catch {
        Write-Host "    ✗ 更新失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    # 等待重启
    Write-Host "  [3/3] 等待重启..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    # 验证新版本
    $maxRetries = 6
    $retryCount = 0
    $success = $false

    while ($retryCount -lt $maxRetries -and -not $success) {
        try {
            $response = Invoke-RestMethod -Uri "$($server.Url)/api/system/version" -Method Get -TimeoutSec 5
            Write-Host "    ✓ 新版本: $($response.version)" -ForegroundColor Green
            $success = $true
        } catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Host "    等待... ($retryCount/$maxRetries)" -ForegroundColor Gray
                Start-Sleep -Seconds 5
            }
        }
    }
    
    if (-not $success) {
        Write-Host "    ⚠️  无法验证新版本" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ v1.2.11 部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "修复内容：" -ForegroundColor White
Write-Host "  • 自动清理TMDB标题中的英文部分" -ForegroundColor White
Write-Host "  • 只保留纯中文标题" -ForegroundColor White
Write-Host "  • 保留版本标识（如'大神版'）" -ForegroundColor White
Write-Host ""
Write-Host "服务器地址：" -ForegroundColor White
Write-Host "  • 本地: http://192.168.51.105:8090" -ForegroundColor Cyan
Write-Host "  • 云端: http://8.134.215.137:8000" -ForegroundColor Cyan
Write-Host ""

pause
