#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络工具模块
提供网络操作重试、超时处理等功能
"""

import time
import functools
from typing import Callable, Any, Optional, Tuple
import requests


class NetworkConfig:
    """网络配置"""
    
    # 重试配置
    MAX_RETRIES = 3          # 最大重试次数
    RETRY_DELAY = 2          # 重试延迟（秒）
    RETRY_BACKOFF = 1.5      # 退避系数（每次重试延迟增加）
    
    # 超时配置
    CONNECT_TIMEOUT = 10     # 连接超时（秒）
    READ_TIMEOUT = 30        # 读取超时（秒）
    
    # NAS/网络文件系统配置
    NFS_OPERATION_DELAY = 1.0  # 操作延迟（秒）


def retry_on_error(
    max_retries: int = NetworkConfig.MAX_RETRIES,
    delay: float = NetworkConfig.RETRY_DELAY,
    backoff: float = NetworkConfig.RETRY_BACKOFF,
    exceptions: Tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    网络操作重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始重试延迟（秒）
        backoff: 退避系数
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
        
    Example:
        @retry_on_error(max_retries=3, delay=2)
        def fetch_data():
            return requests.get('https://api.example.com/data')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # 还有重试机会
                        print(f"⚠ 操作失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                        print(f"  等待 {current_delay:.1f} 秒后重试...")
                        
                        # 调用重试回调
                        if on_retry:
                            on_retry(attempt, e)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff  # 指数退避
                    else:
                        # 已达到最大重试次数
                        print(f"✗ 操作失败，已达到最大重试次数 ({max_retries + 1})")
                        raise
            
            # 理论上不会到这里，但为了安全
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_on_network_error(
    max_retries: int = NetworkConfig.MAX_RETRIES,
    delay: float = NetworkConfig.RETRY_DELAY
):
    """
    网络错误重试装饰器（简化版）
    
    专门用于网络请求，自动处理常见的网络异常
    
    Example:
        @retry_on_network_error(max_retries=3)
        def query_api(url):
            return requests.get(url)
    """
    network_exceptions = (
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        ConnectionError,
        TimeoutError,
    )
    
    return retry_on_error(
        max_retries=max_retries,
        delay=delay,
        exceptions=network_exceptions
    )


def with_timeout(
    connect_timeout: float = NetworkConfig.CONNECT_TIMEOUT,
    read_timeout: float = NetworkConfig.READ_TIMEOUT
):
    """
    超时控制装饰器
    
    Args:
        connect_timeout: 连接超时（秒）
        read_timeout: 读取超时（秒）
        
    Example:
        @with_timeout(connect_timeout=10, read_timeout=30)
        def fetch_data(url):
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 如果函数接受 timeout 参数，自动添加
            if 'timeout' not in kwargs:
                kwargs['timeout'] = (connect_timeout, read_timeout)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def nfs_safe_operation(delay: float = NetworkConfig.NFS_OPERATION_DELAY):
    """
    NAS/网络文件系统安全操作装饰器
    
    在操作前后添加延迟，避免网络文件系统的并发问题
    
    Args:
        delay: 操作延迟（秒）
        
    Example:
        @nfs_safe_operation(delay=1.0)
        def move_file(src, dst):
            shutil.move(src, dst)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 操作前延迟
            time.sleep(delay)
            
            try:
                result = func(*args, **kwargs)
                
                # 操作后延迟
                time.sleep(delay)
                
                return result
                
            except Exception as e:
                print(f"⚠ NFS 操作失败: {e}")
                raise
                
        return wrapper
    return decorator


class SafeRequests:
    """安全的 HTTP 请求封装"""
    
    @staticmethod
    @retry_on_network_error(max_retries=3, delay=2)
    @with_timeout(connect_timeout=10, read_timeout=30)
    def get(url: str, **kwargs) -> requests.Response:
        """安全的 GET 请求"""
        return requests.get(url, **kwargs)
    
    @staticmethod
    @retry_on_network_error(max_retries=3, delay=2)
    @with_timeout(connect_timeout=10, read_timeout=30)
    def post(url: str, **kwargs) -> requests.Response:
        """安全的 POST 请求"""
        return requests.post(url, **kwargs)
    
    @staticmethod
    @retry_on_network_error(max_retries=2, delay=1)
    @with_timeout(connect_timeout=5, read_timeout=15)
    def head(url: str, **kwargs) -> requests.Response:
        """安全的 HEAD 请求"""
        return requests.head(url, **kwargs)


def test_network_connectivity(url: str = "https://www.baidu.com") -> bool:
    """
    测试网络连接
    
    Args:
        url: 测试 URL
        
    Returns:
        是否连接成功
    """
    try:
        response = SafeRequests.head(url, timeout=5)
        return response.status_code < 500
    except:
        return False


if __name__ == '__main__':
    # 测试重试装饰器
    print("测试 1: 重试装饰器")
    print("-" * 60)
    
    attempt_count = 0
    
    @retry_on_error(max_retries=3, delay=1, backoff=1.5)
    def flaky_function():
        """模拟不稳定的函数"""
        global attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            raise ConnectionError(f"连接失败 (尝试 {attempt_count})")
        
        return "成功!"
    
    try:
        result = flaky_function()
        print(f"✓ 最终结果: {result}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试网络连接
    print("\n测试 2: 网络连接")
    print("-" * 60)
    
    if test_network_connectivity():
        print("✓ 网络连接正常")
    else:
        print("✗ 网络连接失败")
    
    # 测试安全请求
    print("\n测试 3: 安全 HTTP 请求")
    print("-" * 60)
    
    try:
        response = SafeRequests.get("https://www.baidu.com")
        print(f"✓ 请求成功: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
