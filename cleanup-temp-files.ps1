# 清理临时文件脚本
# 自动删除调试过程中创建的临时文件

Write-Host "=== 项目文件清理 ===" -ForegroundColor Cyan
Write-Host ""

# 临时文件列表
$tempFiles = @(
    "check-server-code.ps1",
    "fix-category-none.sh",
    "fix-server.ps1",
    "force-clean-restart.ps1",
    "force-restart-clean.ps1",
    "restart-server.ps1",
    "test-server.ps1",
    "test-folder-access.py",
    "test-smart-rename-error.py",
    "diagnose-update.py",
    "diagnose-nas-update.sh"
)

Write-Host "将要删除以下临时文件:" -ForegroundColor Yellow
foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        Write-Host "  - $file" -ForegroundColor Gray
    }
}

Write-Host ""
$confirm = Read-Host "确认删除这些文件吗? (y/N)"

if ($confirm -eq 'y' -or $confirm -eq 'Y') {
    Write-Host ""
    Write-Host "开始清理..." -ForegroundColor Green
    
    $deleted = 0
    $notFound = 0
    
    foreach ($file in $tempFiles) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "  ✓ 已删除: $file" -ForegroundColor Green
            $deleted++
        } else {
            $notFound++
        }
    }
    
    Write-Host ""
    Write-Host "清理完成!" -ForegroundColor Green
    Write-Host "  删除文件: $deleted 个" -ForegroundColor Cyan
    Write-Host "  未找到: $notFound 个" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "建议下一步:" -ForegroundColor Yellow
    Write-Host "  1. 运行: git add -A" -ForegroundColor Gray
    Write-Host "  2. 运行: git commit -m 'chore: 清理临时测试文件'" -ForegroundColor Gray
    Write-Host "  3. 运行: git push origin main" -ForegroundColor Gray
    
} else {
    Write-Host ""
    Write-Host "已取消清理" -ForegroundColor Yellow
}

Write-Host ""
