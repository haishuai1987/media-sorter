#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数 (v2.0.0)

提供常用的工具函数
"""

import os
import hashlib
import time
from typing import Any, Optional, List
from datetime import datetime


class Utils:
    """工具类"""
    
    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'md5') -> Optional[str]:
        """计算文件哈希值
        
        Args:
            filepath: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256）
            
        Returns:
            哈希值，失败返回None
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败: {e}")
            return None
    
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小
        
        Args:
            size: 字节数
            
        Returns:
            格式化后的大小字符串
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size_float = float(size)
        
        while size_float >= 1024 and unit_index < len(units) - 1:
            size_float /= 1024
            unit_index += 1
        
        return f"{size_float:.2f} {units[unit_index]}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时间长度
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时间字符串
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 移除前后空格
        filename = filename.strip()
        
        # 移除多余的点号
        while '..' in filename:
            filename = filename.replace('..', '.')
        
        return filename
    
    @staticmethod
    def ensure_dir(directory: str):
        """确保目录存在
        
        Args:
            directory: 目录路径
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def get_timestamp() -> str:
        """获取当前时间戳字符串
        
        Returns:
            时间戳字符串
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def retry(func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """重试函数
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 初始延迟
            backoff: 退避系数
            
        Returns:
            函数执行结果
        """
        current_delay = delay
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    print(f"重试 {attempt + 1}/{max_retries}，等待 {current_delay:.1f}秒...")
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        raise last_error
    
    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """将列表分块
        
        Args:
            lst: 原始列表
            chunk_size: 块大小
            
        Returns:
            分块后的列表
        """
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def merge_dicts(*dicts) -> dict:
        """合并多个字典
        
        Args:
            *dicts: 要合并的字典
            
        Returns:
            合并后的字典
        """
        result = {}
        for d in dicts:
            if d:
                result.update(d)
        return result
