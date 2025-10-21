@echo off
chcp 65001 >nul

echo ==========================================
echo   紧急推送 v1.2.6 - 修复Autofix破坏的代码
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py version.txt
git commit -m "hotfix: v1.2.6 - 修复Autofix插入的XML标签

Kiro IDE的Autofix错误地在代码中插入了XML标签：
- 第3968行: </file>, '', name)

已移除所有XML标签，代码现在应该能正常运行！"

git push origin main

echo.
echo ==========================================
echo   ✅ 推送完成！
echo ==========================================
echo.
echo 立即在服务器执行：
echo   cd /root/media-sorter
echo   git pull origin main
echo   pkill -f "python.*app.py"
echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
echo.

pause
