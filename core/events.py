#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件系统
提供简单的事件驱动架构，无需外部依赖
"""

from typing import Callable, Dict, List, Any, Optional
from collections import defaultdict
import time
from datetime import datetime


class Event:
    """事件对象"""
    
    def __init__(self, event_type: str, data: Any = None, source: str = None):
        self.type = event_type
        self.data = data
        self.source = source or 'unknown'
        self.timestamp = time.time()
        self.datetime = datetime.now()
    
    def __repr__(self):
        return f"Event(type='{self.type}', source='{self.source}', timestamp={self.timestamp})"


class EventBus:
    """事件总线 - 简单的发布/订阅系统"""
    
    def __init__(self):
        # 事件处理器: {event_type: [handler1, handler2, ...]}
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 一次性处理器
        self._once_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 事件历史（可选，用于调试）
        self._history: List[Event] = []
        self._max_history = 100  # 最多保留100条历史
        
        # 统计信息
        self._stats = {
            'total_events': 0,
            'events_by_type': defaultdict(int),
        }
    
    def on(self, event_type: str, handler: Callable, priority: int = 0):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级（数字越大优先级越高）
        """
        # 添加处理器
        self._handlers[event_type].append((priority, handler))
        
        # 按优先级排序
        self._handlers[event_type].sort(key=lambda x: x[0], reverse=True)
    
    def once(self, event_type: str, handler: Callable):
        """
        订阅事件（只触发一次）
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._once_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable = None):
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            handler: 处理函数（如果为None，则移除该类型的所有处理器）
        """
        if handler is None:
            # 移除所有处理器
            if event_type in self._handlers:
                del self._handlers[event_type]
            if event_type in self._once_handlers:
                del self._once_handlers[event_type]
        else:
            # 移除特定处理器
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    (p, h) for p, h in self._handlers[event_type] if h != handler
                ]
            if event_type in self._once_handlers:
                self._once_handlers[event_type] = [
                    h for h in self._once_handlers[event_type] if h != handler
                ]
    
    def emit(self, event_type: str, data: Any = None, source: str = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
        """
        # 创建事件对象
        event = Event(event_type, data, source)
        
        # 记录历史
        self._add_to_history(event)
        
        # 更新统计
        self._stats['total_events'] += 1
        self._stats['events_by_type'][event_type] += 1
        
        # 调用普通处理器
        if event_type in self._handlers:
            for priority, handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"事件处理器错误 [{event_type}]: {e}")
        
        # 调用一次性处理器
        if event_type in self._once_handlers:
            handlers = self._once_handlers[event_type].copy()
            self._once_handlers[event_type].clear()
            
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    print(f"一次性事件处理器错误 [{event_type}]: {e}")
    
    def wait_for(self, event_type: str, timeout: float = None) -> Optional[Event]:
        """
        等待特定事件（阻塞）
        
        Args:
            event_type: 事件类型
            timeout: 超时时间（秒）
            
        Returns:
            事件对象，如果超时则返回None
        """
        import threading
        
        result = {'event': None}
        event_received = threading.Event()
        
        def handler(event):
            result['event'] = event
            event_received.set()
        
        self.once(event_type, handler)
        
        # 等待事件
        event_received.wait(timeout)
        
        return result['event']
    
    def _add_to_history(self, event: Event):
        """添加到历史记录"""
        self._history.append(event)
        
        # 限制历史记录数量
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def get_history(self, event_type: str = None, limit: int = None) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_type: 事件类型（可选，过滤特定类型）
            limit: 限制数量
            
        Returns:
            事件列表
        """
        history = self._history
        
        # 过滤类型
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        # 限制数量
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_events': self._stats['total_events'],
            'events_by_type': dict(self._stats['events_by_type']),
            'active_handlers': {
                event_type: len(handlers)
                for event_type, handlers in self._handlers.items()
            },
            'history_size': len(self._history),
        }
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()
    
    def clear_all(self):
        """清空所有处理器和历史"""
        self._handlers.clear()
        self._once_handlers.clear()
        self._history.clear()


# 预定义的事件类型
class EventTypes:
    """预定义的事件类型常量"""
    
    # 文件处理事件
    FILE_SCAN_START = 'file.scan.start'
    FILE_SCAN_COMPLETE = 'file.scan.complete'
    FILE_SCAN_ERROR = 'file.scan.error'
    
    FILE_PROCESS_START = 'file.process.start'
    FILE_PROCESS_COMPLETE = 'file.process.complete'
    FILE_PROCESS_ERROR = 'file.process.error'
    
    FILE_RENAME_START = 'file.rename.start'
    FILE_RENAME_COMPLETE = 'file.rename.complete'
    FILE_RENAME_ERROR = 'file.rename.error'
    
    FILE_MOVE_START = 'file.move.start'
    FILE_MOVE_COMPLETE = 'file.move.complete'
    FILE_MOVE_ERROR = 'file.move.error'
    
    # 元数据事件
    METADATA_QUERY_START = 'metadata.query.start'
    METADATA_QUERY_COMPLETE = 'metadata.query.complete'
    METADATA_QUERY_ERROR = 'metadata.query.error'
    
    # 去重事件
    DEDUPE_START = 'dedupe.start'
    DEDUPE_COMPLETE = 'dedupe.complete'
    DEDUPE_FOUND = 'dedupe.found'
    
    # 冲突事件
    CONFLICT_DETECTED = 'conflict.detected'
    CONFLICT_RESOLVED = 'conflict.resolved'
    
    # 清理事件
    CLEANUP_START = 'cleanup.start'
    CLEANUP_COMPLETE = 'cleanup.complete'
    
    # 进度事件
    PROGRESS_UPDATE = 'progress.update'
    
    # 系统事件
    SYSTEM_START = 'system.start'
    SYSTEM_STOP = 'system.stop'
    SYSTEM_ERROR = 'system.error'


# 全局事件总线实例
_event_bus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例（单例）"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# 便捷函数
def emit(event_type: str, data: Any = None, source: str = None):
    """发布事件的便捷函数"""
    bus = get_event_bus()
    bus.emit(event_type, data, source)


def on(event_type: str, handler: Callable, priority: int = 0):
    """订阅事件的便捷函数"""
    bus = get_event_bus()
    bus.on(event_type, handler, priority)


def once(event_type: str, handler: Callable):
    """订阅事件（一次）的便捷函数"""
    bus = get_event_bus()
    bus.once(event_type, handler)


def off(event_type: str, handler: Callable = None):
    """取消订阅的便捷函数"""
    bus = get_event_bus()
    bus.off(event_type, handler)


# 装饰器
def event_handler(event_type: str, priority: int = 0):
    """事件处理器装饰器"""
    def decorator(func: Callable):
        on(event_type, func, priority)
        return func
    return decorator
