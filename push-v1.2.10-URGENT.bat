@echo off
chcp 65001 >nul

echo ==========================================
echo   紧急推送 v1.2.10 - 修复卡死问题
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py version.txt

git commit -m "urgent: v1.2.10 - 修复QueryStrategy卡死问题

问题：
- 处理Gen.V文件时卡死近2小时
- QueryStrategy关键词查询无限制
- TMDB请求可能永久挂起

修复：
- 添加最大尝试次数限制（3次）
- 减少超时时间（10秒 -> 5秒）
- 防止无限循环查询

紧急修复！"

git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！立即更新服务器！
    echo ==========================================
    echo.
) else (
    echo ❌ 推送失败
)

pause
