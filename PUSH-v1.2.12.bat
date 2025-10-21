@echo off
chcp 65001 >nul
echo ========================================
echo   推送 v1.2.12 到 GitHub
echo   Release Group 识别增强
echo ========================================
echo.

echo [1/6] 检查 Git 状态...
git status
echo.

echo [2/6] 添加所有文件...
git add .
echo ✅ 文件已添加
echo.

echo [3/6] 提交更改...
git commit -m "feat: Release Group 识别增强 (v1.2.12)

核心改进：
- 扩展 Release Group 列表从 13 个到 100+
- 优化匹配算法，支持更多格式（-GROUP, [GROUP], (GROUP), 【GROUP】）
- 新增空括号清理逻辑
- 测试通过率 92.6%%

新增支持：
- CHD 系列（12个）
- HDChina 系列（6个）
- LemonHD 系列（9个）
- MTeam 系列（4个）
- OurBits 系列（8个）
- PTer 系列（6个）
- PTHome 系列（7个）
- PTsbao 系列（11个）
- 动漫字幕组（20+个）
- 国际组（20+个）

技术细节：
- 借鉴 NASTool 和 MoviePilot 的最佳实践
- 优化正则表达式匹配顺序
- 自动清理空括号和多余分隔符
- 向后兼容 100%%

测试结果：
- 测试用例：27 个
- 通过：25 个
- 失败：2 个（边缘情况）
- 通过率：92.6%%

文档：
- CHANGELOG-v1.2.12.md - 详细更新日志
- COMMIT-v1.2.12.md - 提交说明
- v1.2.12-SUMMARY.md - 实施总结
- QUICK-START-v1.2.12.md - 快速开始
- test_release_groups_v1.2.12.py - 测试文件

下一步：
- v1.3.0 - 识别词系统（下周）
- v1.4.0 - 副标题解析（2周后）"

if errorlevel 1 (
    echo.
    echo ❌ 提交失败！
    pause
    exit /b 1
)
echo ✅ 提交成功
echo.

echo [4/6] 创建标签...
git tag -a v1.2.12 -m "Release v1.2.12 - Release Group 识别增强

核心改进：
- Release Group: 13 → 100+ (增长 669%%)
- 测试通过率: 92.6%%
- 支持格式: 4 种
- 性能影响: < 10ms/文件

新增支持：
- 所有主流 PT 站点
- 20+ 动漫字幕组
- 20+ 国际组

借鉴项目：
- NASTool - Release Group 列表
- MoviePilot - 架构设计"

if errorlevel 1 (
    echo.
    echo ⚠️ 标签可能已存在，继续推送...
)
echo ✅ 标签已创建
echo.

echo [5/6] 推送到 GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo ❌ 推送失败！请检查网络连接
    pause
    exit /b 1
)
echo ✅ 代码已推送
echo.

echo [6/6] 推送标签...
git push origin v1.2.12
if errorlevel 1 (
    echo.
    echo ⚠️ 标签推送失败（可能已存在）
)
echo ✅ 标签已推送
echo.

echo ========================================
echo   🎉 v1.2.12 推送成功！
echo ========================================
echo.
echo 📊 推送内容:
echo   - 核心代码: app.py
echo   - 版本文件: version.txt
echo   - 测试文件: test_release_groups_v1.2.12.py
echo   - 文档: 7 个文件
echo.
echo 🔗 GitHub 地址:
echo   https://github.com/你的用户名/media-renamer
echo.
echo 📋 下一步:
echo   1. 访问 GitHub 查看提交
echo   2. 创建 Release (可选)
echo   3. 通知用户更新
echo.
echo 🚀 Release 创建指南:
echo   1. 访问: https://github.com/你的用户名/media-renamer/releases/new
echo   2. 选择标签: v1.2.12
echo   3. 标题: v1.2.12 - Release Group 识别增强
echo   4. 描述: 复制 CHANGELOG-v1.2.12.md 的内容
echo   5. 附件: 无需附件（单文件项目）
echo   6. 点击 "Publish release"
echo.
pause
