@echo off
chcp 65001 >nul
echo ========================================
echo 媒体库文件管理器 v1.2.0 - 发布脚本
echo ========================================
echo.
echo 本脚本将执行以下操作：
echo   1. 提交代码到Git
echo   2. 创建版本标签
echo   3. 推送到GitHub
echo   4. 生成服务器更新说明
echo.
pause
echo.

echo [步骤 1/3] 执行Git推送...
call git-push-v1.2.0.bat
echo.

echo [步骤 2/3] 生成服务器更新说明...
echo.
echo ========================================
echo 服务器更新说明
echo ========================================
echo.
echo 在服务器上执行以下命令更新到 v1.2.0：
echo.
echo Linux/Mac:
echo   chmod +x server-update-v1.2.0.sh
echo   ./server-update-v1.2.0.sh
echo.
echo Windows:
echo   server-update-v1.2.0.bat
echo.
echo 或者手动更新：
echo   git pull origin main
echo   python app.py
echo.
echo ========================================
echo.

echo [步骤 3/3] 生成更新说明文件...
(
echo 媒体库文件管理器 v1.2.0 更新说明
echo.
echo 更新时间: %date% %time%
echo.
echo 新功能：
echo - ✨ 实时日志推送功能
echo - 🚀 元数据查询优化
echo - 📊 识别准确率提升到90%%+
echo.
echo 服务器更新命令：
echo.
echo Linux/Mac:
echo   cd /path/to/media-renamer
echo   chmod +x server-update-v1.2.0.sh
echo   ./server-update-v1.2.0.sh
echo.
echo Windows:
echo   cd C:\path\to\media-renamer
echo   server-update-v1.2.0.bat
echo.
echo 详细说明：
echo - docs/v1.2.0功能更新说明.md
echo - docs/发布总结-v1.2.0.md
echo - QUICKSTART.md
) > 服务器更新说明-v1.2.0.txt

echo ✓ 更新说明已生成: 服务器更新说明-v1.2.0.txt
echo.

echo ========================================
echo ✅ 发布完成！
echo ========================================
echo.
echo 下一步：
echo   1. 检查GitHub是否推送成功
echo   2. 将"服务器更新说明-v1.2.0.txt"发送给服务器管理员
echo   3. 在服务器上执行更新脚本
echo.
pause
