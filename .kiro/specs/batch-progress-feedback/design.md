# 设计文档 - 批量处理进度反馈系统

## 概述

本设计为媒体库管理器添加实时进度反馈功能，通过 WebSocket 实现服务器到客户端的实时消息推送。系统采用事件驱动架构，后端在处理文件时发送进度事件，前端实时接收并更新 UI。支持暂停/继续/取消操作，提供详细的处理日志和统计信息。

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Web 前端界面                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  进度条组件  │  │  日志组件    │  │  控制按钮    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      Python 后端服务                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  WebSocket 服务器                                     │   │
│  │  - 连接管理                                           │   │
│  │  - 消息广播                                           │   │
│  │  - 心跳检测                                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  进度管理器 (ProgressManager)                         │   │
│  │  - 进度跟踪                                           │   │
│  │  - 事件发送                                           │   │
│  │  - 状态管理                                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  批量操作处理器                                       │   │
│  │  - 文件扫描                                           │   │
│  │  - 批量重命名                                         │   │
│  │  - 批量移动                                           │   │
│  │  - 批量删除                                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生), WebSocket API
- **后端**: Python 3.x, websockets 库
- **通信协议**: WebSocket (ws://)
- **消息格式**: JSON

## 组件和接口

### 1. WebSocket 服务器

使用 Python `websockets` 库实现 WebSocket 服务器。

```python
import asyncio
import websockets
import json

class WebSocketServer:
    """WebSocket 服务器"""
    
    def __init__(self, host='localhost', port=8091):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
    
    async def register(self, websocket):
        """注册客户端连接"""
        self.clients.add(websocket)
        print(f"[WebSocket] 客户端连接: {websocket.remote_address}")
    
    async def unregister(self, websocket):
        """注销客户端连接"""
        self.clients.discard(websocket)
        print(f"[WebSocket] 客户端断开: {websocket.remote_address}")
    
    async def broadcast(self, message):
        """广播消息到所有客户端"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def handler(self, websocket, path):
        """处理客户端连接"""
        await self.register(websocket)
        try:
            async for message in websocket:
                # 处理客户端消息（如暂停/继续/取消命令）
                data = json.loads(message)
                await self.handle_command(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def handle_command(self, data):
        """处理客户端命令"""
        command = data.get('command')
        if command == 'pause':
            # 暂停批量操作
            pass
        elif command == 'resume':
            # 继续批量操作
            pass
        elif command == 'cancel':
            # 取消批量操作
            pass
    
    async def start(self):
        """启动 WebSocket 服务器"""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        print(f"[WebSocket] 服务器启动: ws://{self.host}:{self.port}")
    
    async def stop(self):
        """停止 WebSocket 服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
```

### 2. 进度管理器

```python
class ProgressManager:
    """批量操作进度管理器"""
    
    def __init__(self, ws_server):
        self.ws_server = ws_server
        self.current_operation = None
        self.is_paused = False
        self.is_cancelled = False
    
    async def start_operation(self, operation_type, total_count):
        """开始批量操作
        
        Args:
            operation_type: 操作类型 (scan|rename|move|delete)
            total_count: 总文件数
        """
        self.current_operation = {
            'type': operation_type,
            'total': total_count,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': time.time(),
            'current_file': None
        }
        self.is_paused = False
        self.is_cancelled = False
        
        await self.send_event('operation_start', {
            'type': operation_type,
            'total': total_count
        })
    
    async def update_progress(self, file_name, status='processing'):
        """更新处理进度
        
        Args:
            file_name: 当前处理的文件名
            status: 状态 (processing|success|failed|skipped)
        """
        if not self.current_operation:
            return
        
        self.current_operation['current_file'] = file_name
        
        if status != 'processing':
            self.current_operation['processed'] += 1
            if status == 'success':
                self.current_operation['success'] += 1
            elif status == 'failed':
                self.current_operation['failed'] += 1
            elif status == 'skipped':
                self.current_operation['skipped'] += 1
        
        # 计算进度百分比
        progress = (self.current_operation['processed'] / 
                   self.current_operation['total'] * 100)
        
        # 计算处理速度和 ETA
        elapsed = time.time() - self.current_operation['start_time']
        speed = self.current_operation['processed'] / elapsed if elapsed > 0 else 0
        remaining = self.current_operation['total'] - self.current_operation['processed']
        eta = remaining / speed if speed > 0 else 0
        
        await self.send_event('progress_update', {
            'file_name': file_name,
            'status': status,
            'processed': self.current_operation['processed'],
            'total': self.current_operation['total'],
            'progress': round(progress, 2),
            'speed': round(speed, 2),
            'eta': round(eta, 0),
            'success': self.current_operation['success'],
            'failed': self.current_operation['failed'],
            'skipped': self.current_operation['skipped']
        })
    
    async def finish_operation(self, summary=None):
        """完成批量操作"""
        if not self.current_operation:
            return
        
        elapsed = time.time() - self.current_operation['start_time']
        
        await self.send_event('operation_complete', {
            'type': self.current_operation['type'],
            'total': self.current_operation['total'],
            'processed': self.current_operation['processed'],
            'success': self.current_operation['success'],
            'failed': self.current_operation['failed'],
            'skipped': self.current_operation['skipped'],
            'elapsed': round(elapsed, 2),
            'summary': summary
        })
        
        self.current_operation = None
    
    async def send_log(self, level, message):
        """发送日志消息
        
        Args:
            level: 日志级别 (info|warning|error)
            message: 日志消息
        """
        await self.send_event('log', {
            'level': level,
            'message': message,
            'timestamp': time.strftime('%H:%M:%S')
        })
    
    async def send_event(self, event_type, data):
        """发送进度事件"""
        message = {
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        }
        await self.ws_server.broadcast(message)
    
    def pause(self):
        """暂停操作"""
        self.is_paused = True
    
    def resume(self):
        """继续操作"""
        self.is_paused = False
    
    def cancel(self):
        """取消操作"""
        self.is_cancelled = True
    
    async def check_pause(self):
        """检查是否暂停"""
        while self.is_paused and not self.is_cancelled:
            await asyncio.sleep(0.1)
    
    def is_cancelled_check(self):
        """检查是否取消"""
        return self.is_cancelled
```

### 3. 前端 WebSocket 客户端

```javascript
class ProgressClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.eventHandlers = {};
    }
    
    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8091');
            
            this.ws.onopen = () => {
                console.log('[WebSocket] 连接成功');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.trigger('connected');
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.ws.onerror = (error) => {
                console.error('[WebSocket] 错误:', error);
                this.trigger('error', error);
            };
            
            this.ws.onclose = () => {
                console.log('[WebSocket] 连接关闭');
                this.isConnected = false;
                this.trigger('disconnected');
                this.reconnect();
            };
        } catch (error) {
            console.error('[WebSocket] 连接失败:', error);
            this.reconnect();
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WebSocket] 超过最大重连次数');
            this.trigger('reconnect_failed');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`[WebSocket] ${this.reconnectDelay}ms 后重连 (尝试 ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
        
        this.reconnectDelay *= 2; // 指数退避
    }
    
    handleMessage(message) {
        const { event, data } = message;
        this.trigger(event, data);
    }
    
    send(command, data = {}) {
        if (this.isConnected && this.ws) {
            this.ws.send(JSON.stringify({
                command,
                data,
                timestamp: Date.now()
            }));
        }
    }
    
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    trigger(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
```

### 4. 前端进度显示组件

```javascript
class ProgressUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.progressBar = null;
        this.logContainer = null;
        this.logs = [];
        this.maxLogs = 500;
    }
    
    show() {
        this.container.style.display = 'block';
        this.render();
    }
    
    hide() {
        this.container.style.display = 'none';
    }
    
    render() {
        this.container.innerHTML = `
            <div class="progress-overlay">
                <div class="progress-modal">
                    <div class="progress-header">
                        <h3>批量处理进度</h3>
                        <button onclick="progressUI.close()">×</button>
                    </div>
                    <div class="progress-body">
                        <div class="progress-stats">
                            <div class="stat-item">
                                <span class="stat-label">当前文件:</span>
                                <span class="stat-value" id="current-file">-</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">进度:</span>
                                <span class="stat-value" id="progress-text">0/0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">速度:</span>
                                <span class="stat-value" id="speed-text">0 文件/秒</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">预计剩余:</span>
                                <span class="stat-value" id="eta-text">-</span>
                            </div>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar" id="progress-bar">
                                <div class="progress-fill" id="progress-fill" style="width: 0%">
                                    <span class="progress-percent" id="progress-percent">0%</span>
                                </div>
                            </div>
                        </div>
                        <div class="progress-summary">
                            <span class="summary-item success">✓ <span id="success-count">0</span></span>
                            <span class="summary-item failed">✗ <span id="failed-count">0</span></span>
                            <span class="summary-item skipped">⊘ <span id="skipped-count">0</span></span>
                        </div>
                        <div class="progress-controls">
                            <button id="pause-btn" onclick="progressUI.pause()">⏸ 暂停</button>
                            <button id="cancel-btn" onclick="progressUI.cancel()">✕ 取消</button>
                        </div>
                        <div class="progress-logs" id="progress-logs">
                            <!-- 日志将动态添加 -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.progressBar = document.getElementById('progress-fill');
        this.logContainer = document.getElementById('progress-logs');
    }
    
    updateProgress(data) {
        document.getElementById('current-file').textContent = data.file_name || '-';
        document.getElementById('progress-text').textContent = `${data.processed}/${data.total}`;
        document.getElementById('speed-text').textContent = `${data.speed} 文件/秒`;
        document.getElementById('eta-text').textContent = this.formatETA(data.eta);
        document.getElementById('progress-percent').textContent = `${data.progress}%`;
        document.getElementById('success-count').textContent = data.success;
        document.getElementById('failed-count').textContent = data.failed;
        document.getElementById('skipped-count').textContent = data.skipped;
        
        this.progressBar.style.width = `${data.progress}%`;
        
        // 根据状态改变颜色
        if (data.status === 'failed') {
            this.progressBar.style.background = '#dc3545';
        } else {
            this.progressBar.style.background = '#667eea';
        }
    }
    
    addLog(level, message, timestamp) {
        const logEntry = { level, message, timestamp };
        this.logs.push(logEntry);
        
        // 限制日志数量
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        const logEl = document.createElement('div');
        logEl.className = `log-entry log-${level}`;
        logEl.innerHTML = `
            <span class="log-time">${timestamp}</span>
            <span class="log-message">${message}</span>
        `;
        
        this.logContainer.appendChild(logEl);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }
    
    formatETA(seconds) {
        if (seconds < 60) {
            return `${Math.round(seconds)} 秒`;
        } else if (seconds < 3600) {
            return `${Math.round(seconds / 60)} 分钟`;
        } else {
            return `${Math.round(seconds / 3600)} 小时`;
        }
    }
    
    pause() {
        progressClient.send('pause');
        document.getElementById('pause-btn').textContent = '▶ 继续';
        document.getElementById('pause-btn').onclick = () => this.resume();
    }
    
    resume() {
        progressClient.send('resume');
        document.getElementById('pause-btn').textContent = '⏸ 暂停';
        document.getElementById('pause-btn').onclick = () => this.pause();
    }
    
    cancel() {
        if (confirm('确定要取消当前操作吗？')) {
            progressClient.send('cancel');
        }
    }
    
    close() {
        this.hide();
    }
}
```

## 数据模型

### 进度事件消息格式

```json
{
  "event": "progress_update",
  "data": {
    "file_name": "电影名称.mkv",
    "status": "processing",
    "processed": 15,
    "total": 100,
    "progress": 15.0,
    "speed": 2.5,
    "eta": 34,
    "success": 14,
    "failed": 1,
    "skipped": 0
  },
  "timestamp": 1698765432.123
}
```

### 日志消息格式

```json
{
  "event": "log",
  "data": {
    "level": "info",
    "message": "正在重命名: 电影名称.mkv -> 新名称.mkv",
    "timestamp": "10:30:45"
  },
  "timestamp": 1698765432.123
}
```

## 错误处理

### WebSocket 连接错误

- 自动重连（最多 3 次）
- 指数退避策略
- 降级为轮询模式

### 消息发送失败

- 消息队列缓冲
- 批量发送
- 丢弃过期消息

## 性能优化

### 消息节流

- 进度更新最多每 100ms 一次
- 日志消息批量发送
- 限制消息大小

### 内存管理

- 限制日志数量（最多 500 条）
- 定期清理过期连接
- 使用消息队列

## 测试策略

### 单元测试

- WebSocket 服务器测试
- 进度管理器测试
- 消息格式验证

### 集成测试

- 端到端进度推送测试
- 暂停/继续/取消测试
- 重连测试

### 性能测试

- 大量文件处理测试
- 高频消息推送测试
- 内存泄漏测试
