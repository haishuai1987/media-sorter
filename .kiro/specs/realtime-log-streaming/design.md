# 实时日志推送设计文档

## Overview

使用Server-Sent Events (SSE)实现实时日志推送，在Web界面显示后端处理进度和日志。

## Architecture

```
后端处理 → LogStream → SSE端点 → 前端EventSource → 日志显示组件
```

## Components

### 1. LogStream (后端)
```python
class LogStream:
    def __init__(self, stream_id: str):
        self.stream_id = stream_id
        self.queue = Queue()
        
    def push(self, level: str, message: str):
        """推送日志到队列"""
        
    def get_events(self):
        """生成SSE事件流"""
```

### 2. SSE API端点
```python
@app.route('/api/logs/stream/<stream_id>')
def stream_logs(stream_id):
    """SSE日志流端点"""
    def generate():
        stream = get_log_stream(stream_id)
        for event in stream.get_events():
            yield f"data: {json.dumps(event)}\n\n"
    return Response(generate(), mimetype='text/event-stream')
```

### 3. 前端LogViewer组件
```javascript
class LogViewer {
    constructor(streamId) {
        this.eventSource = new EventSource(`/api/logs/stream/${streamId}`);
        this.eventSource.onmessage = (e) => this.handleLog(JSON.parse(e.data));
    }
    
    handleLog(log) {
        // 显示日志
    }
}
```

## Data Models

### LogEvent
```json
{
  "timestamp": "2025-10-21T03:40:00Z",
  "level": "INFO",
  "message": "处理文件: example.mkv",
  "progress": 50,
  "total": 100
}
```

## Implementation Notes

1. 使用Python的Queue实现线程安全的日志队列
2. SSE连接超时设置为30分钟
3. 前端自动重连机制
4. 日志缓冲区限制为1000条
