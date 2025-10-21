@echo off
chcp 65001 >nul

echo ==========================================
echo   拉取最新代码
echo ==========================================
echo.

git pull origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 更新成功！
    echo ==========================================
    echo.
) else (
    echo ❌ 更新失败
)

pause
