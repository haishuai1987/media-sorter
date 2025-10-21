@echo off
chcp 65001 >nul

echo ==========================================
echo   紧急推送 v1.2.5 - 修复语法错误
echo ==========================================
echo.

REM 配置Git用户信息
git config user.name "haishuai1987"
git config user.email "2887256@163.com"
echo ✅ Git用户信息已配置
echo.

REM 检查远程仓库
git remote -v | findstr "origin" >nul
if errorlevel 1 (
    echo 🔗 添加远程仓库...
    git remote add origin https://github.com/haishuai1987/media-sorter
    echo ✅ 远程仓库已添加
) else (
    echo ✅ 远程仓库已存在
)
echo.

REM 添加文件
echo 📝 添加修复的文件...
git add app.py version.txt HOTFIX-v1.2.5.md COMMIT-v1.2.5.txt
echo ✅ 文件已添加
echo.

REM 提交
echo 💾 提交修复...
git commit -m "hotfix: v1.2.5 - 修复正则表达式语法错误

问题：
- 第3967行正则表达式字符串被截断
- 导致SyntaxError: unterminated string literal

修复：
- 修复正则表达式完整性
- 添加缺失的结束引号和参数

紧急修复，立即部署！"

if errorlevel 1 (
    echo ⚠️  没有新的更改需要提交
) else (
    echo ✅ 更改已提交
)
echo.

REM 推送到GitHub
echo 🚀 推送到GitHub...
git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！
    echo ==========================================
    echo.
    echo 📦 版本: v1.2.5
    echo 🔗 仓库: https://github.com/haishuai1987/media-sorter
    echo.
    echo 🚨 现在立即更新服务器：
    echo.
    echo 在服务器上执行：
    echo   cd /root/media-sorter
    echo   git pull origin main
    echo   cat version.txt
    echo   pkill -f "python.*app.py"
    echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
    echo   sleep 3
    echo   ps aux ^| grep "python.*app.py" ^| grep -v grep
    echo   tail -20 app.log
    echo.
) else (
    echo.
    echo ❌ 推送失败
    echo 请检查网络连接和权限
    echo.
)

pause
