# -*- coding: utf-8 -*-
"""
异步任务定义
v3.0.0 新增
"""

from celery import current_task
from datetime import datetime
import uuid

from core.celery_app import celery_app
from core.models import db, Task, ProcessHistory
from core.smart_batch_processor import SmartBatchProcessor
from core.template_engine import get_template_engine


@celery_app.task(bind=True, name='tasks.process_files')
def process_files_task(self, user_id, files, template='movie_default', use_queue=True, priority='normal'):
    """
    异步处理文件任务
    
    Args:
        user_id: 用户 ID
        files: 文件列表
        template: 模板名称
        use_queue: 是否使用队列
        priority: 优先级
    """
    task_id = self.request.id
    total = len(files)
    
    try:
        # 更新任务状态
        update_task_status(task_id, user_id, 'running', 0, total)
        
        # 初始化处理器
        processor = SmartBatchProcessor(
            use_queue=use_queue,
            use_rate_limit=True,
            max_workers=4,
            rate_limit=10
        )
        
        results = []
        
        # 处理每个文件
        for i, filename in enumerate(files, 1):
            try:
                # 更新进度
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total,
                        'percentage': int((i / total) * 100),
                        'current_file': filename
                    }
                )
                
                # 处理文件
                result = processor.process_single(filename, template_name=template)
                
                # 保存到历史记录
                save_history(user_id, filename, result, template)
                
                results.append({
                    'original': filename,
                    'new_name': result.get('new_name', ''),
                    'status': 'success' if result.get('success') else 'failed',
                    'error': result.get('error')
                })
                
                # 更新任务进度
                update_task_status(task_id, user_id, 'running', i, total, results)
                
            except Exception as e:
                results.append({
                    'original': filename,
                    'new_name': '',
                    'status': 'failed',
                    'error': str(e)
                })
        
        # 任务完成
        update_task_status(task_id, user_id, 'success', total, total, results)
        
        return {
            'success': True,
            'total': total,
            'results': results
        }
        
    except Exception as e:
        # 任务失败
        update_task_status(task_id, user_id, 'failed', 0, total, error_message=str(e))
        raise


@celery_app.task(name='tasks.cleanup_old_tasks')
def cleanup_old_tasks():
    """清理旧任务（定时任务）"""
    from datetime import timedelta
    
    # 删除 30 天前的已完成任务
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    Task.query.filter(
        Task.status.in_(['success', 'failed']),
        Task.completed_at < cutoff_date
    ).delete()
    
    db.session.commit()


@celery_app.task(name='tasks.cleanup_old_history')
def cleanup_old_history():
    """清理旧历史记录（定时任务）"""
    from datetime import timedelta
    
    # 删除 90 天前的历史记录
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    
    ProcessHistory.query.filter(
        ProcessHistory.created_at < cutoff_date
    ).delete()
    
    db.session.commit()


def update_task_status(task_id, user_id, status, progress=0, total=0, result=None, error_message=None):
    """更新任务状态"""
    task = Task.query.get(task_id)
    
    if not task:
        task = Task(
            id=task_id,
            user_id=user_id,
            task_type='process_files',
            status=status,
            progress=progress,
            total=total
        )
        db.session.add(task)
    else:
        task.status = status
        task.progress = progress
        task.total = total
    
    if status == 'running' and not task.started_at:
        task.started_at = datetime.utcnow()
    
    if status in ['success', 'failed']:
        task.completed_at = datetime.utcnow()
    
    if result:
        task.result = result
    
    if error_message:
        task.error_message = error_message
    
    db.session.commit()


def save_history(user_id, original_name, result, template):
    """保存处理历史"""
    history = ProcessHistory(
        user_id=user_id,
        original_name=original_name,
        new_name=result.get('new_name', ''),
        status='success' if result.get('success') else 'failed',
        error_message=result.get('error'),
        template_used=template,
        metadata=result.get('info', {})
    )
    
    db.session.add(history)
    db.session.commit()


# 配置定时任务
celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'tasks.cleanup_old_tasks',
        'schedule': 86400.0,  # 每天执行一次
    },
    'cleanup-old-history': {
        'task': 'tasks.cleanup_old_history',
        'schedule': 86400.0,  # 每天执行一次
    },
}
