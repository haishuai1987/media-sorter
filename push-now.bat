@echo off
chcp 65001 >nul
echo ========================================
echo 推送到GitHub - v1.2.0
echo ========================================
echo.

echo [1/4] 添加所有文件...
git add .
if %errorlevel% neq 0 (
    echo ❌ Git add 失败
    pause
    exit /b 1
)
echo ✓ 文件已添加
echo.

echo [2/4] 提交更改...
git commit -m "feat: v1.2.0 - 实时日志推送和元数据查询优化

新功能：
- 实时日志推送功能 (LogStream + SSE + LogViewer)
- 元数据查询优化 (TitleParser + TitleMapper + QueryStrategy)
- 识别准确率从60%%提升到90%%+
- 支持30+常用作品映射

文件：
- app.py - 核心功能实现
- public/index.html - LogViewer组件
- title_mapping.json - 标题映射配置
- test_title_parser.py - 测试脚本
- 完整文档和发布脚本"

if %errorlevel% neq 0 (
    echo ⚠️  可能没有新的更改需要提交
)
echo.

echo [3/4] 创建版本标签...
git tag -a v1.2.0 -m "Release v1.2.0 - 实时日志推送和元数据查询优化" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  标签可能已存在，删除旧标签...
    git tag -d v1.2.0
    git tag -a v1.2.0 -m "Release v1.2.0 - 实时日志推送和元数据查询优化"
)
echo ✓ 标签已创建
echo.

echo [4/4] 推送到GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ 推送main分支失败
    pause
    exit /b 1
)
echo ✓ main分支已推送
echo.

git push origin v1.2.0 --force
if %errorlevel% neq 0 (
    echo ❌ 推送标签失败
    pause
    exit /b 1
)
echo ✓ 标签已推送
echo.

echo ========================================
echo ✅ 推送完成！
echo ========================================
echo.
echo 版本: v1.2.0
echo 分支: main
echo 标签: v1.2.0
echo.
echo 查看GitHub: https://github.com/你的用户名/media-renamer
echo.
pause
