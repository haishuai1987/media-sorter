#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理增强模块 (v1.9.0)

提供并发处理、进度追踪、断点续传和批量回滚功能
"""

import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime
from typing import List, Dict, Callable, Any, Optional


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, total: int, operation_id: str = None):
        self.total = total
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()
        self.operation_id = operation_id or self._generate_id()
        self.lock = Lock()
        self.failed_items = []
    
    def _generate_id(self) -> str:
        """生成操作ID"""
        return f"op_{int(time.time() * 1000)}"
    
    def update(self, success: bool = True, item: Any = None, error: str = None):
        """更新进度
        
        Args:
            success: 是否成功
            item: 处理的项目
            error: 错误信息
        """
        with self.lock:
            if success:
                self.completed += 1
            else:
                self.failed += 1
                if item is not None:
                    self.failed_items.append({
                        'item': item,
                        'error': error,
                        'timestamp': datetime.now().isoformat()
                    })
    
    def get_progress(self) -> float:
        """获取进度百分比 (0.0 - 1.0)"""
        if self.total == 0:
            return 1.0
        return (self.completed + self.failed) / self.total
    
    def get_eta(self) -> Optional[float]:
        """获取预计剩余时间（秒）"""
        if self.completed == 0:
            return None
        
        elapsed = time.time() - self.start_time
        avg_time = elapsed / self.completed
        remaining = self.total - self.completed - self.failed
        
        if remaining <= 0:
            return 0.0
        
        return remaining * avg_time
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        elapsed = time.time() - self.start_time
        progress = self.get_progress()
        eta = self.get_eta()
        
        return {
            'operation_id': self.operation_id,
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'progress': progress,
            'elapsed': elapsed,
            'eta': eta,
            'success_rate': self.completed / max(self.completed + self.failed, 1),
            'failed_items': self.failed_items
        }
    
    def is_complete(self) -> bool:
        """是否完成"""
        return (self.completed + self.failed) >= self.total


class ConcurrentProcessor:
    """并发处理器"""
    
    def __init__(self, max_workers: int = 4):
        """初始化
        
        Args:
            max_workers: 最大并发数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batch(self, 
                     items: List[Any], 
                     handler: Callable[[Any], Any],
                     progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        """批量处理
        
        Args:
            items: 要处理的项目列表
            handler: 处理函数
            progress_callback: 进度回调函数
            
        Returns:
            处理结果统计
        """
        tracker = ProgressTracker(len(items))
        results = []
        
        # 提交所有任务
        future_to_item = {}
        for item in items:
            future = self.executor.submit(self._safe_handler, handler, item)
            future_to_item[future] = item
        
        # 等待完成并更新进度
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                tracker.update(success=True)
                results.append({
                    'item': item,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                tracker.update(success=False, item=item, error=str(e))
                results.append({
                    'item': item,
                    'success': False,
                    'error': str(e)
                })
            
            # 调用进度回调
            if progress_callback:
                progress_callback(tracker.get_stats())
        
        return {
            'stats': tracker.get_stats(),
            'results': results
        }
    
    def _safe_handler(self, handler: Callable, item: Any) -> Any:
        """安全的处理函数包装
        
        Args:
            handler: 原始处理函数
            item: 要处理的项目
            
        Returns:
            处理结果
        """
        try:
            return handler(item)
        except Exception as e:
            # 重新抛出异常，让外层捕获
            raise e
    
    def shutdown(self, wait: bool = True):
        """关闭执行器
        
        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)


class CheckpointManager:
    """断点管理器"""
    
    def __init__(self, checkpoint_dir: str = '.checkpoints'):
        """初始化
        
        Args:
            checkpoint_dir: 检查点目录
        """
        self.checkpoint_dir = checkpoint_dir
        if not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, operation_id: str, state: Dict):
        """保存检查点
        
        Args:
            operation_id: 操作ID
            state: 状态数据
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f'{operation_id}.json')
        
        checkpoint_data = {
            'operation_id': operation_id,
            'timestamp': datetime.now().isoformat(),
            'state': state
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    def load_checkpoint(self, operation_id: str) -> Optional[Dict]:
        """加载检查点
        
        Args:
            operation_id: 操作ID
            
        Returns:
            状态数据，如果不存在返回None
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f'{operation_id}.json')
        
        if not os.path.exists(checkpoint_file):
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                return checkpoint_data.get('state')
        except Exception as e:
            print(f"加载检查点失败: {e}")
            return None
    
    def delete_checkpoint(self, operation_id: str):
        """删除检查点
        
        Args:
            operation_id: 操作ID
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f'{operation_id}.json')
        
        if os.path.exists(checkpoint_file):
            try:
                os.remove(checkpoint_file)
            except Exception as e:
                print(f"删除检查点失败: {e}")
    
    def list_checkpoints(self) -> List[Dict]:
        """列出所有检查点
        
        Returns:
            检查点列表
        """
        checkpoints = []
        
        try:
            for filename in os.listdir(self.checkpoint_dir):
                if filename.endswith('.json'):
                    operation_id = filename[:-5]
                    checkpoint_file = os.path.join(self.checkpoint_dir, filename)
                    
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        checkpoints.append({
                            'operation_id': operation_id,
                            'timestamp': data.get('timestamp'),
                            'state': data.get('state')
                        })
        except Exception as e:
            print(f"列出检查点失败: {e}")
        
        return checkpoints


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, history_dir: str = '.rollback_history'):
        """初始化
        
        Args:
            history_dir: 历史记录目录
        """
        self.history_dir = history_dir
        if not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)
    
    def record_operation(self, operation_id: str, operation: Dict):
        """记录操作
        
        Args:
            operation_id: 操作ID
            operation: 操作数据
        """
        history_file = os.path.join(self.history_dir, f'{operation_id}.json')
        
        record = {
            'operation_id': operation_id,
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'rollback_available': True
        }
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
    
    def rollback(self, operation_id: str, rollback_handler: Callable[[Dict], bool]) -> bool:
        """回滚操作
        
        Args:
            operation_id: 操作ID
            rollback_handler: 回滚处理函数
            
        Returns:
            是否成功
        """
        history_file = os.path.join(self.history_dir, f'{operation_id}.json')
        
        if not os.path.exists(history_file):
            print(f"操作记录不存在: {operation_id}")
            return False
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                record = json.load(f)
            
            if not record.get('rollback_available'):
                print(f"操作不支持回滚: {operation_id}")
                return False
            
            # 执行回滚
            success = rollback_handler(record['operation'])
            
            if success:
                # 标记为已回滚
                record['rollback_available'] = False
                record['rollback_timestamp'] = datetime.now().isoformat()
                
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
            
            return success
        except Exception as e:
            print(f"回滚失败: {e}")
            return False
    
    def list_operations(self, rollback_available_only: bool = False) -> List[Dict]:
        """列出操作历史
        
        Args:
            rollback_available_only: 只列出可回滚的操作
            
        Returns:
            操作列表
        """
        operations = []
        
        try:
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    history_file = os.path.join(self.history_dir, filename)
                    
                    with open(history_file, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        
                        if rollback_available_only and not record.get('rollback_available'):
                            continue
                        
                        operations.append(record)
        except Exception as e:
            print(f"列出操作历史失败: {e}")
        
        # 按时间倒序排序
        operations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return operations


# 导出的公共接口
__all__ = [
    'ProgressTracker',
    'ConcurrentProcessor',
    'CheckpointManager',
    'RollbackManager',
]
