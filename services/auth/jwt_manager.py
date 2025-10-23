# -*- coding: utf-8 -*-
"""
JWT Token 管理
v4.0.0 新增
"""

from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
import os


# JWT 配置
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)


def create_tokens(user):
    """
    创建访问令牌和刷新令牌
    
    Args:
        user: 用户对象
    
    Returns:
        dict: 包含 access_token 和 refresh_token
    """
    # 创建访问令牌
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'username': user.username,
            'role': user.role
        },
        expires_delta=JWT_ACCESS_TOKEN_EXPIRES
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        identity=user.id,
        expires_delta=JWT_REFRESH_TOKEN_EXPIRES
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': int(JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }


def refresh_access_token():
    """
    刷新访问令牌
    
    Returns:
        dict: 新的访问令牌
    """
    current_user_id = get_jwt_identity()
    
    # 创建新的访问令牌
    access_token = create_access_token(
        identity=current_user_id,
        expires_delta=JWT_ACCESS_TOKEN_EXPIRES
    )
    
    return {
        'access_token': access_token,
        'expires_in': int(JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    }


def get_jwt_config():
    """
    获取 JWT 配置
    
    Returns:
        dict: JWT 配置字典
    """
    return {
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'),
        'JWT_ACCESS_TOKEN_EXPIRES': JWT_ACCESS_TOKEN_EXPIRES,
        'JWT_REFRESH_TOKEN_EXPIRES': JWT_REFRESH_TOKEN_EXPIRES,
        'JWT_ALGORITHM': 'HS256',
        'JWT_TOKEN_LOCATION': ['headers'],
        'JWT_HEADER_NAME': 'Authorization',
        'JWT_HEADER_TYPE': 'Bearer'
    }
