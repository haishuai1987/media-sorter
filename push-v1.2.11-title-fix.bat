@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.11 - 标题清理修复
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py test_title_cleaning.py push-v1.2.11-title-fix.bat version.txt

git commit -m "fix: v1.2.11 - 修复TMDB标题清理逻辑

问题：
- TMDB返回的标题包含英文部分
- 例如：'密室大逃脱 Great Escape'
- 导致重命名后的文件名包含英文

修复：
- 添加 extract_chinese_title() 方法
- 自动提取纯中文标题，移除英文部分
- 保留版本标识（如'大神版'）

测试用例：
✓ '密室大逃脱 Great Escape' → '密室大逃脱'
✓ '密室大逃脱大神版 Great Escape Super' → '密室大逃脱大神版'
✓ '花牌情缘：巡 Chihayafuru Full Circle' → '花牌情缘：巡'

影响范围：
- TMDBHelper.search_tv()
- TMDBHelper.search_movie()
- 所有通过TMDB查询的标题都会被清理"

echo v1.2.11 > version.txt
git add version.txt
git commit -m "chore: 更新版本号到 v1.2.11"

git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！
    echo ==========================================
    echo.
    echo 下一步：在服务器上执行更新
    echo   ssh root@8.134.215.137
    echo   cd /root/media-sorter
    echo   git pull origin main
    echo   pkill -f "python.*app.py"
    echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
    echo.
) else (
    echo ❌ 推送失败
)

pause
