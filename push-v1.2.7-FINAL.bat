@echo off
chcp 65001 >nul

echo ==========================================
echo   推送 v1.2.7 到GitHub
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

echo 📝 添加所有文件...
git add -A

echo 💾 提交 v1.2.7...
git commit -m "release: v1.2.7 - 修复Release Group和技术参数问题

修复内容：
✅ 在parse_folder_name中使用TitleParser清理文件夹名
✅ 移除Release Group（-CHDWEB, -ADWeb等）
✅ 移除技术参数（1080p, WEB-DL, H.264等）
✅ 修复Autofix破坏的代码
✅ 包含fix-autofix-damage.py修复脚本

测试状态：
- 服务器运行正常
- 语法检查通过
- TitleParser工作正常
- QueryStrategy已配置

下一步：
- 测试文件整理功能
- 验证中文标题查询"

echo 🚀 推送到GitHub...
git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ v1.2.7 推送成功！
    echo ==========================================
    echo.
    echo 📦 版本: v1.2.7
    echo 🔗 仓库: https://github.com/haishuai1987/media-sorter
    echo.
    echo 🚨 现在更新服务器：
    echo.
    echo   cd /root/media-sorter
    echo   git pull origin main
    echo   python3 fix-autofix-damage.py
    echo   pkill -f "python.*app.py"
    echo   nohup python3 app.py ^> app.log 2^>^&1 ^&
    echo.
) else (
    echo.
    echo ❌ 推送失败
    echo.
)

pause
