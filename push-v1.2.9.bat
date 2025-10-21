@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.9 - 修复续集标记重复问题
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py version.txt

git commit -m "fix: v1.2.9 - 修复续集标记重复问题

问题：
- 文件名中已有续集标记（如 II, III）
- 代码又根据Season文件夹添加续集标记
- 导致重复：快乐的大人 II II

修复：
- 在添加续集标记前，先移除标题中已有的续集标记
- 提取基础标题，然后根据Season文件夹添加正确的标记
- 支持多种续集标记格式：II/III/IV/V、第X季、Season X、数字

效果：
- 快乐的大人 Joyful Grown-ups II -> 快乐的大人
- 无限超越班3 -> 无限超越班
- 然后根据Season文件夹添加正确的续集标记"

git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ v1.2.9 推送成功！
    echo ==========================================
    echo.
    echo 立即更新服务器：
    echo   cd /root/media-sorter
    echo   git pull origin main
    echo   python3 fix-autofix-damage.py
    echo   pkill -f "python.*app.py"
    echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
    echo.
) else (
    echo ❌ 推送失败
)

pause
