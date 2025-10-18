#!/bin/bash
if [ -f ~/media-sorter/media-renamer.pid ]; then
    PID=$(cat ~/media-sorter/media-renamer.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "服务已停止"
    else
        echo "服务未运行"
    fi
    rm -f ~/media-sorter/media-renamer.pid
else
    pkill -f "python3 app.py"
    echo "服务已停止"
fi
