@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ==========================================
echo   推送 v1.2.0 到 GitHub
echo ==========================================
echo.

echo [1/3] 添加所有文件...
git add .
if %errorlevel% neq 0 (
    echo ❌ 添加文件失败
    pause
    exit /b 1
)
echo ✓ 文件已添加
echo.

echo [2/3] 提交更改...
git commit -m "feat: v1.2.0 - 实时日志推送和元数据查询优化" -m "" -m "新功能：" -m "- 实时日志推送功能 (LogStream + SSE + LogViewer)" -m "- 元数据查询优化 (TitleParser + TitleMapper + QueryStrategy)" -m "- 识别准确率从60%%提升到90%%+" -m "- 支持30+常用作品映射"
if %errorlevel% neq 0 (
    echo ⚠️  提交失败（可能没有新的更改）
)
echo.

echo [3/3] 推送到GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ 推送失败
    echo.
    echo 可能的原因：
    echo 1. 需要输入GitHub用户名和密码
    echo 2. 网络连接问题
    echo 3. 权限问题
    echo.
    pause
    exit /b 1
)
echo.

echo ==========================================
echo   ✅ 推送成功！
echo ==========================================
echo.
echo 版本: v1.2.0
echo 分支: main
echo.
echo 下一步：运行服务器更新脚本
echo   .\远程推送更新.ps1
echo.
pause
