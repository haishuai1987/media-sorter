#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理增强模块 (v1.7.0)

提供统一的错误处理、重试机制和用户友好的错误消息
"""

import time
import functools
import traceback
from typing import Callable, Any, Optional, Tuple
from enum import Enum


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK = "network"
    API = "api"
    FILE = "file"
    PERMISSION = "permission"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 可忽略的错误
    MEDIUM = "medium"    # 需要注意的错误
    HIGH = "high"        # 严重错误
    CRITICAL = "critical"  # 致命错误


class ErrorHandler:
    """统一错误处理器"""
    
    # 错误消息映射
    ERROR_MESSAGES = {
        # 网络错误
        'timeout': '网络连接超时，请检查网络后重试',
        'connection': '无法连接到服务器，请检查网络设置',
        'dns': 'DNS解析失败，请检查网络或DNS设置',
        
        # API错误
        'unauthorized': 'Cookie已过期或无效，请重新登录',
        '401': 'Cookie已过期或无效，请重新登录',
        '403': '没有权限执行此操作',
        '404': '文件或资源不存在',
        '429': '请求过于频繁，请稍后再试',
        '500': '服务器内部错误，请稍后重试',
        '502': '服务器网关错误，请稍后重试',
        '503': '服务暂时不可用，请稍后重试',
        
        # 文件错误
        'permission denied': '没有权限访问文件或目录',
        'file not found': '文件不存在',
        'disk full': '磁盘空间不足',
        'read-only': '文件系统为只读',
        
        # 验证错误
        'invalid cookie': 'Cookie格式不正确',
        'invalid path': '路径格式不正确',
        'invalid filename': '文件名包含非法字符',
    }
    
    @staticmethod
    def classify_error(error: Exception) -> Tuple[ErrorType, ErrorSeverity]:
        """分类错误
        
        Args:
            error: 异常对象
            
        Returns:
            (错误类型, 严重程度)
        """
        error_str = str(error).lower()
        
        # 网络错误
        if any(kw in error_str for kw in ['timeout', 'connection', 'network', 'dns']):
            return ErrorType.NETWORK, ErrorSeverity.MEDIUM
        
        # API错误
        if any(kw in error_str for kw in ['401', '403', '429', 'unauthorized', 'forbidden']):
            return ErrorType.API, ErrorSeverity.HIGH
        
        if any(kw in error_str for kw in ['500', '502', '503', 'server error']):
            return ErrorType.API, ErrorSeverity.MEDIUM
        
        # 文件错误
        if any(kw in error_str for kw in ['permission', 'access denied', 'read-only']):
            return ErrorType.PERMISSION, ErrorSeverity.HIGH
        
        if any(kw in error_str for kw in ['file not found', 'no such file', 'disk full']):
            return ErrorType.FILE, ErrorSeverity.MEDIUM
        
        # 超时错误
        if 'timeout' in error_str:
            return ErrorType.TIMEOUT, ErrorSeverity.MEDIUM
        
        # 验证错误
        if any(kw in error_str for kw in ['invalid', 'illegal', 'malformed']):
            return ErrorType.VALIDATION, ErrorSeverity.LOW
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    @staticmethod
    def get_friendly_message(error: Exception, operation: str = '操作') -> str:
        """获取用户友好的错误消息
        
        Args:
            error: 异常对象
            operation: 操作名称
            
        Returns:
            用户友好的错误消息
        """
        error_str = str(error).lower()
        
        # 查找匹配的错误消息
        for keyword, message in ErrorHandler.ERROR_MESSAGES.items():
            if keyword in error_str:
                return message
        
        # 默认消息
        error_type, severity = ErrorHandler.classify_error(error)
        
        if severity == ErrorSeverity.CRITICAL:
            return f'{operation}失败（严重错误）: {str(error)}'
        elif severity == ErrorSeverity.HIGH:
            return f'{operation}失败: {str(error)}'
        else:
            return f'{operation}遇到问题: {str(error)}'
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """判断是否应该重试
        
        Args:
            error: 异常对象
            
        Returns:
            是否应该重试
        """
        error_type, _ = ErrorHandler.classify_error(error)
        
        # 网络错误和超时错误可以重试
        if error_type in [ErrorType.NETWORK, ErrorType.TIMEOUT]:
            return True
        
        # 某些API错误可以重试（如500, 502, 503）
        error_str = str(error).lower()
        if any(code in error_str for code in ['500', '502', '503']):
            return True
        
        return False
    
    @staticmethod
    def log_error(error: Exception, operation: str = '操作', 
                  context: Optional[dict] = None, verbose: bool = False):
        """记录错误日志
        
        Args:
            error: 异常对象
            operation: 操作名称
            context: 上下文信息
            verbose: 是否输出详细信息
        """
        error_type, severity = ErrorHandler.classify_error(error)
        friendly_msg = ErrorHandler.get_friendly_message(error, operation)
        
        # 基本日志
        print(f"[错误] {operation}: {friendly_msg}")
        print(f"  类型: {error_type.value}, 严重程度: {severity.value}")
        
        # 上下文信息
        if context:
            print(f"  上下文: {context}")
        
        # 详细信息（调试模式）
        if verbose:
            print(f"  原始错误: {str(error)}")
            print(f"  堆栈跟踪:")
            traceback.print_exc()


def retry_on_error(max_retries: int = 3, 
                   delay: float = 1.0, 
                   backoff: float = 2.0,
                   exceptions: tuple = (Exception,)):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避系数（每次重试延迟翻倍）
        exceptions: 需要重试的异常类型
        
    Example:
        @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
        def network_request():
            # 网络请求代码
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    # 最后一次尝试，不再重试
                    if attempt == max_retries:
                        break
                    
                    # 检查是否应该重试
                    if not ErrorHandler.should_retry(e):
                        break
                    
                    # 记录重试信息
                    print(f"[重试] {func.__name__} 第 {attempt + 1}/{max_retries} 次重试...")
                    print(f"  原因: {ErrorHandler.get_friendly_message(e)}")
                    print(f"  等待 {current_delay:.1f} 秒后重试...")
                    
                    # 等待后重试
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # 所有重试都失败
            if last_error:
                ErrorHandler.log_error(last_error, func.__name__)
                raise last_error
        
        return wrapper
    return decorator


def safe_execute(func: Callable, 
                 default_value: Any = None,
                 operation: str = '操作',
                 log_error: bool = True) -> Tuple[bool, Any, Optional[str]]:
    """安全执行函数（捕获所有异常）
    
    Args:
        func: 要执行的函数
        default_value: 失败时的默认返回值
        operation: 操作名称
        log_error: 是否记录错误
        
    Returns:
        (成功标志, 返回值, 错误消息)
        
    Example:
        success, result, error = safe_execute(
            lambda: risky_operation(),
            default_value=None,
            operation='风险操作'
        )
    """
    try:
        result = func()
        return True, result, None
    except Exception as e:
        if log_error:
            ErrorHandler.log_error(e, operation)
        
        error_msg = ErrorHandler.get_friendly_message(e, operation)
        return False, default_value, error_msg


class ErrorRecovery:
    """错误恢复策略"""
    
    @staticmethod
    def recover_from_network_error(func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """从网络错误中恢复
        
        Args:
            func: 网络操作函数
            *args, **kwargs: 函数参数
            
        Returns:
            (成功标志, 结果)
        """
        @retry_on_error(max_retries=3, delay=2.0, backoff=2.0)
        def wrapped():
            return func(*args, **kwargs)
        
        try:
            result = wrapped()
            return True, result
        except Exception as e:
            ErrorHandler.log_error(e, '网络操作')
            return False, None
    
    @staticmethod
    def recover_from_file_error(func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """从文件错误中恢复
        
        Args:
            func: 文件操作函数
            *args, **kwargs: 函数参数
            
        Returns:
            (成功标志, 结果)
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except PermissionError as e:
            print(f"[文件错误] 权限不足: {str(e)}")
            return False, None
        except FileNotFoundError as e:
            print(f"[文件错误] 文件不存在: {str(e)}")
            return False, None
        except OSError as e:
            print(f"[文件错误] 系统错误: {str(e)}")
            return False, None
        except Exception as e:
            ErrorHandler.log_error(e, '文件操作')
            return False, None


# 导出的公共接口
__all__ = [
    'ErrorHandler',
    'ErrorType',
    'ErrorSeverity',
    'retry_on_error',
    'safe_execute',
    'ErrorRecovery',
]
