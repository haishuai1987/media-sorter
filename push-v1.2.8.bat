@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.8 - 扩展技术参数列表
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py version.txt

git commit -m "update: v1.2.8 - 扩展TitleParser技术参数列表

问题：
- QueryStrategy查询时标题包含技术参数
- 例如: Love Con Revenge S01 Complete Netflix DDP 5 1 DBTV
- 导致查询效率低下

修复：
✅ 添加更多技术参数到TECHNICAL_PARAMS列表
✅ 添加流媒体平台（Netflix, AMZN, NF等）
✅ 添加音频格式（DDP, DDP5.1, AAC2.0等）
✅ 添加Complete, COMPLETE等标记
✅ 添加季数标记（S01-S10）

效果：
- 查询标题更干净
- TMDB查询成功率更高
- 中文标题获取更准确"

git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ v1.2.8 推送成功！
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
