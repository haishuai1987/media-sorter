# -*- coding: utf-8 -*-
"""
任务管理路由
v3.0.0 新增
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user

from core.models import db, Task
from core.auth import login_required_api
from core.tasks import process_files_task

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@tasks_bp.route('', methods=['POST'])
@login_required_api
def create_task():
    """创建异步处理任务"""
    try:
        data = request.json
        files = data.get('files', [])
        template = data.get('template', 'movie_default')
        use_queue = data.get('use_queue', True)
        priority = data.get('priority', 'normal')
        
        if not files:
            return jsonify({'success': False, 'error': '文件列表不能为空'}), 400
        
        # 创建异步任务
        task = process_files_task.apply_async(
            args=[current_user.id, files, template, use_queue, priority]
        )
        
        return jsonify({
            'success': True,
            'message': '任务已创建',
            'data': {
                'task_id': task.id,
                'status': 'pending'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tasks_bp.route('/<task_id>', methods=['GET'])
@login_required_api
def get_task(task_id):
    """获取任务状态"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # 检查权限
        if task.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': '无权访问'}), 403
        
        return jsonify({
            'success': True,
            'data': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tasks_bp.route('', methods=['GET'])
@login_required_api
def list_tasks():
    """获取任务列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        # 构建查询
        query = Task.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        # 分页
        pagination = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [task.to_dict() for task in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tasks_bp.route('/<task_id>', methods=['DELETE'])
@login_required_api
def delete_task(task_id):
    """删除任务"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # 检查权限
        if task.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': '无权访问'}), 403
        
        # 只能删除已完成或失败的任务
        if task.status not in ['success', 'failed']:
            return jsonify({'success': False, 'error': '只能删除已完成或失败的任务'}), 400
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '任务已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@tasks_bp.route('/cleanup', methods=['POST'])
@login_required_api
def cleanup_tasks():
    """清理已完成的任务"""
    try:
        # 删除当前用户的已完成任务
        deleted = Task.query.filter_by(
            user_id=current_user.id,
            status='success'
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted} 个任务'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
