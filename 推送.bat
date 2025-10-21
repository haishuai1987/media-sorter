@echo off
echo 正在推送 v1.2.0...
echo.

git add .
git commit -m "feat: v1.2.0 - 实时日志推送和元数据查询优化"
git push origin main

echo.
echo 完成！
pause
