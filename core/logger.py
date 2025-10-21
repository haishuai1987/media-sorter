#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 (v2.0.0)

提供统一的日志记录接口
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class Logger:
    """日志记录器"""
    
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, name: str = 'media-renamer', level: str = 'INFO'):
        """初始化
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LEVELS.get(level, logging.INFO))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """异常日志（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str):
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        self.logger.setLevel(self.LEVELS.get(level, logging.INFO))


# 全局日志实例
_global_logger = None


def get_logger(name: Optional[str] = None) -> Logger:
    """获取全局日志实例
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name or 'media-renamer')
    return _global_logger
