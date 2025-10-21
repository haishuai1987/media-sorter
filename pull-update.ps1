# 拉取最新代码
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  拉取最新代码" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

git pull origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  ✅ 更新成功！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "❌ 更新失败" -ForegroundColor Red
}

pause
