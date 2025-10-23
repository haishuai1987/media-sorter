# -*- coding: utf-8 -*-
"""
认证和授权
v3.0.0 新增
"""

from functools import wraps
from flask import jsonify, request
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, get_jwt_identity
from datetime import timedelta

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

# 初始化 JWT
jwt = JWTManager()


@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    from core.models import User
    return User.query.get(int(user_id))


def init_auth(app):
    """初始化认证系统"""
    # 配置 JWT
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'your-secret-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # 初始化
    login_manager.init_app(app)
    jwt.init_app(app)


def create_tokens(user):
    """创建访问令牌和刷新令牌"""
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'username': user.username,
            'role': user.role
        }
    )
    refresh_token = create_refresh_token(identity=user.id)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer'
    }


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def login_required_api(f):
    """API 登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """获取当前用户 ID"""
    if current_user.is_authenticated:
        return current_user.id
    return None


def check_user_permission(user_id, resource_user_id):
    """检查用户权限"""
    if not current_user.is_authenticated:
        return False
    
    # 管理员可以访问所有资源
    if current_user.role == 'admin':
        return True
    
    # 用户只能访问自己的资源
    return current_user.id == resource_user_id
