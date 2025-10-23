# -*- coding: utf-8 -*-
"""
认证服务数据模型
v4.0.0 - 复用 core.models 中的 User 模型
"""

from core.models import db, User, init_db

__all__ = ['db', 'User', 'init_db']
