# -*- coding: utf-8 -*-
"""
认证微服务主应用
v4.0.0
"""

from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.auth.models import db, User, init_db
from services.auth.jwt_manager import create_tokens, refresh_access_token, get_jwt_config
from core.service_discovery import register_service, deregister_service
from core.health_check import HealthCheck, create_health_check_endpoint

# 创建应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'auth-service-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT 配置
jwt_config = get_jwt_config()
for key, value in jwt_config.items():
    app.config[key] = value

# 初始化扩展
CORS(app)
jwt = JWTManager(app)

# 初始化 API 文档
api = Api(
    app,
    version='4.0.0',
    title='Media Renamer Auth Service',
    description='认证微服务 API',
    doc='/docs/'
)

# 初始化数据库
init_db(app)

# 健康检查
health_check = HealthCheck('auth-service', '4.0.0')
health_check.add_check('database', lambda: health_check.check_database(db))

# API 命名空间
auth_ns = api.namespace('auth', description='认证操作')

# API 模型定义
login_model = api.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码'),
    'remember': fields.Boolean(description='记住登录')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
    'password': fields.String(required=True, description='密码')
})

user_model = api.model('User', {
    'id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'role': fields.String(description='角色'),
    'is_active': fields.Boolean(description='是否激活'),
    'created_at': fields.String(description='创建时间'),
    'last_login': fields.String(description='最后登录时间')
})

# API 路由
@auth_ns.route('/login')
class Login(Resource):
    @api.expect(login_model)
    @api.doc(responses={200: 'Success', 401: 'Unauthorized', 400: 'Bad Request'})
    def post(self):
        """用户登录"""
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'success': False, 'error': '缺少用户名或密码'}, 400
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                return {'success': False, 'error': '用户名或密码错误'}, 401
            
            if not user.is_active:
                return {'success': False, 'error': '账户已被禁用'}, 403
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 创建 Token
            tokens = create_tokens(user)
            
            return {
                'success': True,
                'message': '登录成功',
                'data': {
                    'user': user.to_dict(),
                    **tokens
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500


@auth_ns.route('/register')
class Register(Resource):
    @api.expect(register_model)
    @api.doc(responses={200: 'Success', 400: 'Bad Request'})
    def post(self):
        """用户注册"""
        try:
            data = request.json
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if not username or not email or not password:
                return {'success': False, 'error': '缺少必要参数'}, 400
            
            if User.query.filter_by(username=username).first():
                return {'success': False, 'error': '用户名已存在'}, 400
            
            if User.query.filter_by(email=email).first():
                return {'success': False, 'error': '邮箱已被注册'}, 400
            
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': '注册成功',
                'data': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}, 500


@auth_ns.route('/verify')
class VerifyToken(Resource):
    @jwt_required()
    @api.doc(responses={200: 'Success', 401: 'Unauthorized'}, security='Bearer')
    def post(self):
        """验证 Token"""
        try:
            user_id = get_jwt_identity()
            
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}, 404
            
            if not user.is_active:
                return {'success': False, 'error': '账户已被禁用'}, 403
            
            return {
                'success': True,
                'data': user.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 401


@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    @api.doc(responses={200: 'Success', 401: 'Unauthorized'}, security='Bearer')
    def post(self):
        """刷新 Token"""
        try:
            tokens = refresh_access_token()
            
            return {
                'success': True,
                'message': 'Token 刷新成功',
                'data': tokens
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 401


@auth_ns.route('/me')
class CurrentUser(Resource):
    @jwt_required()
    @api.doc(responses={200: 'Success', 401: 'Unauthorized'}, security='Bearer')
    def get(self):
        """获取当前用户信息"""
        try:
            user_id = get_jwt_identity()
            
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': '用户不存在'}, 404
            
            return {
                'success': True,
                'data': user.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 401


# 健康检查端点
@app.route('/health')
def health():
    """健康检查"""
    return create_health_check_endpoint(health_check)()


# 服务注册
def register():
    """注册服务到 Consul"""
    service_name = 'auth-service'
    host = os.getenv('AUTH_SERVICE_HOST', 'localhost')
    port = int(os.getenv('AUTH_SERVICE_PORT', 8001))
    
    return register_service(service_name, host=host, port=port)


def deregister():
    """注销服务"""
    service_name = 'auth-service'
    host = os.getenv('AUTH_SERVICE_HOST', 'localhost')
    port = int(os.getenv('AUTH_SERVICE_PORT', 8001))
    
    return deregister_service(service_name, host=host, port=port)


if __name__ == '__main__':
    port = int(os.getenv('AUTH_SERVICE_PORT', 8001))
    
    # 注册服务
    register()
    
    try:
        print(f"🚀 认证服务启动在端口 {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        deregister()
