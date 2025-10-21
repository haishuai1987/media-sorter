@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.11 - 标题清理改进版
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

git add app.py test_title_cleaning.py MOVIEPILOT-ANALYSIS.md HOTFIX-v1.2.11-IMPROVED.md PUSH-v1.2.11-FINAL.bat reference/

git commit -m "feat: v1.2.11 - 标题清理改进（借鉴 MoviePilot）

改进内容：
- 借鉴 MoviePilot 的标题清理实现
- 自动移除 Release Group（CHDWEB、ADWeb 等）
- 自动移除技术参数（1080p、H.264 等）
- 自动移除流媒体标识（AMZN、NF 等）
- 只保留纯中文标题

测试结果：
✓ 12/12 测试用例全部通过
✓ '密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB' → '密室大逃脱'
✓ '花牌情缘：巡.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-CHDWEB' → '花牌情缘：巡'
✓ '间谍过家家.S03.2025.1080p.CR.WEB-DL.x264.AAC-ADWeb' → '间谍过家家'

参考：
- MoviePilot: https://github.com/jxxghp/MoviePilot
- 分析文档: MOVIEPILOT-ANALYSIS.md"

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
    echo 改进内容：
    echo   • 借鉴 MoviePilot 实现
    echo   • 移除 Release Group
    echo   • 移除技术参数
    echo   • 只保留纯中文标题
    echo.
    echo 测试结果：12/12 通过
    echo.
    echo 下一步：更新服务器
    echo   飞牛OS: ssh root@192.168.51.105
    echo   云服务器: ssh root@8.134.215.137
    echo.
) else (
    echo ❌ 推送失败
)

pause
