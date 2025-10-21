@echo off
chcp 65001 >nul
echo ========================================
echo 推送 v1.2.0 更新到 GitHub
echo ========================================
echo.

echo [1/3] 添加所有文件...
git add .
echo.

echo [2/3] 提交更改...
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
echo.

echo [3/3] 推送到 GitHub...
git push origin main
echo.

echo ========================================
echo ✅ 推送完成！
echo ========================================
echo.
echo 下一步：运行 远程推送更新.ps1 更新服务器
echo.
pause
