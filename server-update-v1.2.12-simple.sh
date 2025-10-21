#!/bin/bash
# v1.2.12 简化更新脚本（一键更新）

echo "🚀 开始更新到 v1.2.12..."

# 停止服务
pkill -f "python.*app.py"

# 拉取代码
git pull origin main

# 启动服务
nohup python3 app.py > media-renamer.log 2>&1 &

echo "✅ 更新完成！"
echo "📝 查看日志: tail -f media-renamer.log"
