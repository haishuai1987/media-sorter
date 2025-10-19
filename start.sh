#!/bin/bash
cd ~/media-sorter
nohup python3 app.py > media-renamer.log 2>&1 &
echo $! > media-renamer.pid
echo "服务已启动"
