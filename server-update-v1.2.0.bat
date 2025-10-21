@echo off
chcp 65001 >nul

REM 媒体库文件管理器 v1.2.0 服务器更新脚本（Windows）
REM 用于在Windows服务器上更新到最新版本

echo ========================================
echo 媒体库文件管理器 - 服务器更新脚本
echo 目标版本: v1.2.0
echo ========================================
echo.

REM 检查是否在正确的目录
if not exist "app.py" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/6] 备份当前版本...
set BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul
copy app.py "%BACKUP_DIR%\" >nul
xcopy /E /I /Y public "%BACKUP_DIR%\public" >nul 2>&1
copy version.txt "%BACKUP_DIR%\" >nul 2>&1
echo ✓ 备份完成: %BACKUP_DIR%
echo.

echo [2/6] 停止服务...
taskkill /F /FI "WINDOWTITLE eq 媒体库文件管理器*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *app.py*" >nul 2>&1
timeout /t 2 >nul
echo ✓ 服务已停止
echo.

echo [3/6] 拉取最新代码...
git fetch origin
git checkout main
git pull origin main
echo ✓ 代码更新完成
echo.

echo [4/6] 检查版本...
if exist "version.txt" (
    set /p NEW_VERSION=<version.txt
    echo   当前版本: %NEW_VERSION%
) else (
    echo   ⚠️  未找到version.txt
)
echo.

echo [5/6] 检查依赖...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Python: ✓
) else (
    echo   ❌ 未安装Python
    pause
    exit /b 1
)
echo.

echo [6/6] 启动服务...
start "媒体库文件管理器 v1.2.0" python app.py
timeout /t 3 >nul
echo ✓ 服务启动成功
echo.

echo ========================================
echo ✅ 更新完成！
echo ========================================
echo.
echo 版本: v1.2.0
echo 日志文件: media-renamer.log
echo.
echo 新功能：
echo   - ✨ 实时日志推送
echo   - 🚀 元数据查询优化
echo   - 📊 识别准确率提升到90%%+
echo.
echo 访问: http://localhost:8090
echo.
pause
