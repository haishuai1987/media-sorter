@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.11 - 标题清理修复
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py test_title_cleaning.py update-fnos.ps1 update-fnos-server.sh 飞牛OS更新命令.txt HOTFIX-v1.2.11.md PUSH-v1.2.11.bat

git commit -m "fix: v1.2.11 - 修复TMDB标题清理逻辑

问题：
- TMDB返回标题包含英文（如'密室大逃脱 Great Escape'）
- 导致重命名后文件名不纯净

修复：
- 添加 extract_chinese_title() 方法
- 自动提取纯中文标题
- 保留版本标识（如'大神版'）

测试：
✓ '密室大逃脱 Great Escape' → '密室大逃脱'
✓ '密室大逃脱大神版 Great Escape Super' → '密室大逃脱大神版'
✓ '花牌情缘：巡 Chihayafuru Full Circle' → '花牌情缘：巡'"

echo v1.2.11 > version.txt
git add version.txt
git commit -m "chore: bump version to v1.2.11"

git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！
    echo ==========================================
    echo.
    echo 现在可以更新服务器了：
    echo   飞牛OS: ssh root@192.168.51.105
    echo   云服务器: ssh root@8.134.215.137
    echo.
) else (
    echo ❌ 推送失败
)

pause
