@echo off
chcp 65001 >nul

echo ==========================================
echo   推送当前版本到GitHub
echo ==========================================
echo.

git config user.name "haishuai1987"
git config user.email "2887256@163.com"

echo 📝 添加所有文件...
git add -A

echo 💾 提交...
git commit -m "update: 当前版本包含所有修复

修复内容：
- v1.2.4: 在parse_folder_name中添加TitleParser清理
- v1.2.5-v1.2.7: 修复Autofix破坏的代码
- 包含fix-autofix-damage.py修复脚本

当前状态：
- TitleParser正常工作
- parse_folder_name使用TitleParser清理
- QueryStrategy已配置
- 服务器运行正常"

echo 🚀 推送到GitHub...
git push origin main

if errorlevel 0 (
    echo.
    echo ==========================================
    echo   ✅ 推送成功！
    echo ==========================================
    echo.
) else (
    echo.
    echo ❌ 推送失败
    echo.
)

pause
