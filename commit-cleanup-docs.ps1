# 提交整理文档
Write-Host "提交项目整理文档..." -ForegroundColor Cyan

git add PROJECT_CLEANUP.md
git add cleanup-temp-files.ps1
git add CLEANUP_SUMMARY.md
git add .gitignore
git add .kiro/specs/realtime-log-streaming/tasks.md

git commit -m "docs: 添加项目整理文档和清理脚本

- 创建PROJECT_CLEANUP.md详细说明需要清理的文件
- 创建cleanup-temp-files.ps1自动清理脚本  
- 创建CLEANUP_SUMMARY.md整理总结
- 更新.gitignore防止临时文件被提交
- 更新tasks.md标记已完成任务"

git push origin main

Write-Host "完成！" -ForegroundColor Green
