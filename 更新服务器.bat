@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo   更新服务器到 v1.2.0
echo ==========================================
echo.
echo 正在连接服务器...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "& {$SERVER_URL = 'http://192.168.51.100:8090'; Write-Host '[1/4] 检查服务器状态...' -ForegroundColor Yellow; try { $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop; Write-Host 'OK 服务器在线' -ForegroundColor Green } catch { Write-Host 'ERROR 服务器离线' -ForegroundColor Red; exit 1 }; Write-Host ''; Write-Host '[2/4] 检查更新...' -ForegroundColor Yellow; $checkBody = '{\"use_proxy\": false}'; $checkResponse = Invoke-RestMethod -Uri \"$SERVER_URL/api/check-update\" -Method Post -ContentType 'application/json' -Body $checkBody; Write-Host \"当前版本: $($checkResponse.current_version)\" -ForegroundColor Cyan; Write-Host \"有更新: $($checkResponse.has_update)\" -ForegroundColor Cyan; if ($checkResponse.has_update) { Write-Host ''; Write-Host '[3/4] 执行更新...' -ForegroundColor Yellow; $updateBody = '{\"use_proxy\": false, \"auto_restart\": true}'; $updateResponse = Invoke-RestMethod -Uri \"$SERVER_URL/api/update\" -Method Post -ContentType 'application/json' -Body $updateBody; if ($updateResponse.updated) { Write-Host 'OK 更新成功' -ForegroundColor Green; Write-Host ''; Write-Host '[4/4] 等待服务重启...' -ForegroundColor Yellow; Start-Sleep -Seconds 10; Write-Host 'OK 完成' -ForegroundColor Green } else { Write-Host \"ERROR: $($updateResponse.error)\" -ForegroundColor Red } } else { Write-Host '已是最新版本' -ForegroundColor Green }; Write-Host ''; Write-Host '=========================================='; Write-Host '  更新完成'; Write-Host '=========================================='; Write-Host ''; Write-Host '访问: http://192.168.51.100:8090'; Write-Host '刷新浏览器 (Ctrl+Shift+R)'; Write-Host ''}"

echo.
pause
