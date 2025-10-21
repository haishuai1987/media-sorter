@echo off
chcp 65001 >nul

echo ==========================================
echo   紧急修复 v1.2.5 - 语法错误
echo ==========================================
echo.

echo 📝 添加文件...
git add app.py version.txt HOTFIX-v1.2.5.md

echo 💾 提交修复...
git commit -m "hotfix: v1.2.5 - 修复正则表达式语法错误

问题：
- 第3967行正则表达式字符串被截断
- 导致SyntaxError: unterminated string literal

修复：
- 修复正则表达式: r'[-\[\(][A-Z0-9]+[\]\)]$'
- 添加缺失的结束引号和参数

紧急修复，立即部署！"

echo 🚀 推送到GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！
    echo ==========================================
    echo.
    echo 现在立即更新服务器：
    echo.
    echo 在服务器上执行：
    echo   cd /root/media-sorter
    echo   git pull origin main
    echo   pkill -f "python.*app.py"
    echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
    echo.
) else (
    echo.
    echo ❌ 推送失败
    echo.
)

pause
