@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.11 - 标题清理修复
echo ==========================================
echo.

git add app.py test_title_cleaning.py

git commit -m "fix: v1.2.11 - 修复TMDB标题清理，只保留中文标题"

echo v1.2.11 > version.txt
git add version.txt
git commit -m "chore: bump version to v1.2.11"

git push origin main

echo.
echo ==========================================
echo   ✅ 完成！请双击运行：更新服务器.ps1
echo ==========================================
echo.

pause
