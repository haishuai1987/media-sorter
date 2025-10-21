@echo off
chcp 65001 >nul

echo ==========================================
echo   克隆 MoviePilot 参考项目
echo ==========================================
echo.

cd E:\

git clone https://github.com/jxxghp/MoviePilot.git MoviePilot-reference

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 克隆成功！
    echo ==========================================
    echo.
    echo 项目位置: E:\MoviePilot-reference
    echo.
) else (
    echo ❌ 克隆失败
)

pause
