@echo off
chcp 65001 >nul
REM GitHub快速更新脚本

echo ==========================================
echo   GitHub 快速更新
echo ==========================================
echo.

REM 查看修改
echo 📝 检查修改的文件...
git status
echo.

REM 输入更新说明
set /p commit_msg="请输入更新说明: "

REM 添加所有修改
echo 📦 添加文件...
git add .

REM 提交
echo 💾 提交更改...
git commit -m "%commit_msg%"

REM 推送
echo 🚀 推送到GitHub...
git push

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 更新成功！
    echo ==========================================
    echo.
    echo 访问你的仓库查看更新:
    echo https://github.com/你的用户名/media-renamer
    echo.
) else (
    echo.
    echo ❌ 更新失败
    echo 请检查网络连接和权限
    echo.
)

pause
