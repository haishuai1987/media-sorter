@echo off
echo Committing cleanup docs...
git add .
git commit -m "docs: 添加项目整理文档和清理脚本"
git push origin main
echo Done!
pause
