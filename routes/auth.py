# -*- coding: utf-8 -*-
"""
认证路由
v3.0.0 新增
"""

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from datetime import datetime

from core.models import db, User
from core.auth import create_tokens, login_required_api, admin_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # 验证参数
        if not username or not email or not password:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 检查用户名是否存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        
        # 检查邮箱是否存在
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': '邮箱已被注册'}), 400
        
        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
        
        # 验证参数
        if not username or not password:
            return jsonify({'success': False, 'error': '缺少用户名或密码'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'error': '账户已被禁用'}), 403
        
        # 登录用户
        login_user(user, remember=remember)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 创建 Token
        tokens = create_tokens(user)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user': user.to_dict(),
                **tokens
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required_api
def logout():
    """用户登出"""
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required_api
def get_current_user():
    """获取当前用户信息"""
    try:
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/me', methods=['PUT'])
@login_required_api
def update_current_user():
    """更新当前用户信息"""
    try:
        data = request.json
        
        # 更新邮箱
        if 'email' in data:
            email = data['email']
            # 检查邮箱是否被其他用户使用
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != current_user.id:
                return jsonify({'success': False, 'error': '邮箱已被使用'}), 400
            current_user.email = email
        
        # 更新密码
        if 'password' in data:
            old_password = data.get('old_password')
            new_password = data['password']
            
            if not old_password or not current_user.check_password(old_password):
                return jsonify({'success': False, 'error': '原密码错误'}), 400
            
            current_user.set_password(new_password)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """获取用户列表（管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [user.to_dict() for user in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户（管理员）"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        # 更新角色
        if 'role' in data:
            user.role = data['role']
        
        # 更新状态
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（管理员）"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 不能删除自己
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': '不能删除自己'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
