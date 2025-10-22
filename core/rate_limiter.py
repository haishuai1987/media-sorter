#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制器
实现令牌桶、滑动窗口等速率限制算法
"""

import time
import threading
from typing import Dict, Optional
from collections import deque
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    max_requests: int = 10      # 最大请求数
    time_window: float = 1.0    # 时间窗口（秒）
    burst_size: int = 0          # 突发大小（0表示不允许突发）


class TokenBucket:
    """令牌桶算法"""
    
    def __init__(self, rate: float, capacity: int):
        """
        初始化令牌桶
        
        Args:
            rate: 令牌生成速率（个/秒）
            capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 计算新增令牌数
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌
        
        Args:
            tokens: 需要消费的令牌数
            
        Returns:
            是否成功消费
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        等待令牌
        
        Args:
            tokens: 需要的令牌数
            timeout: 超时时间（秒）
            
        Returns:
            是否获取到令牌
        """
        start_time = time.time()
        
        while True:
            if self.consume(tokens):
                return True
            
            # 检查超时
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # 短暂休眠
            time.sleep(0.01)
    
    def get_available_tokens(self) -> float:
        """获取可用令牌数"""
        with self.lock:
            self._refill()
            return self.tokens


class SlidingWindow:
    """滑动窗口算法"""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        初始化滑动窗口
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = threading.Lock()
    
    def _clean_old_requests(self):
        """清理过期请求"""
        now = time.time()
        cutoff = now - self.time_window
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def allow_request(self) -> bool:
        """
        检查是否允许请求
        
        Returns:
            是否允许
        """
        with self.lock:
            self._clean_old_requests()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(time.time())
                return True
            return False
    
    def wait_for_slot(self, timeout: Optional[float] = None) -> bool:
        """
        等待可用槽位
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否获取到槽位
        """
        start_time = time.time()
        
        while True:
            if self.allow_request():
                return True
            
            # 检查超时
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # 短暂休眠
            time.sleep(0.01)
    
    def get_current_count(self) -> int:
        """获取当前请求数"""
        with self.lock:
            self._clean_old_requests()
            return len(self.requests)
    
    def get_wait_time(self) -> float:
        """获取需要等待的时间"""
        with self.lock:
            self._clean_old_requests()
            
            if len(self.requests) < self.max_requests:
                return 0.0
            
            # 计算最早请求的剩余时间
            oldest = self.requests[0]
            wait_time = self.time_window - (time.time() - oldest)
            return max(0.0, wait_time)


class RateLimiter:
    """速率限制器（支持多种算法）"""
    
    def __init__(
        self,
        algorithm: str = 'token_bucket',
        max_requests: int = 10,
        time_window: float = 1.0,
        burst_size: int = 0
    ):
        """
        初始化速率限制器
        
        Args:
            algorithm: 算法类型 ('token_bucket' 或 'sliding_window')
            max_requests: 最大请求数
            time_window: 时间窗口（秒）
            burst_size: 突发大小
        """
        self.algorithm = algorithm
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size
        
        if algorithm == 'token_bucket':
            rate = max_requests / time_window
            capacity = max_requests + burst_size
            self.limiter = TokenBucket(rate, capacity)
        elif algorithm == 'sliding_window':
            self.limiter = SlidingWindow(max_requests, time_window)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")
    
    def allow(self) -> bool:
        """检查是否允许请求"""
        if isinstance(self.limiter, TokenBucket):
            return self.limiter.consume(1)
        else:
            return self.limiter.allow_request()
    
    def wait(self, timeout: Optional[float] = None) -> bool:
        """等待可用配额"""
        if isinstance(self.limiter, TokenBucket):
            return self.limiter.wait_for_token(1, timeout)
        else:
            return self.limiter.wait_for_slot(timeout)
    
    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        stats = {
            'algorithm': self.algorithm,
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'burst_size': self.burst_size,
        }
        
        if isinstance(self.limiter, TokenBucket):
            stats['available_tokens'] = self.limiter.get_available_tokens()
        else:
            stats['current_count'] = self.limiter.get_current_count()
            stats['wait_time'] = self.limiter.get_wait_time()
        
        return stats


class MultiRateLimiter:
    """多级速率限制器"""
    
    def __init__(self):
        """初始化多级速率限制器"""
        self.limiters: Dict[str, RateLimiter] = {}
        self.lock = threading.Lock()
    
    def add_limiter(self, name: str, limiter: RateLimiter):
        """添加限制器"""
        with self.lock:
            self.limiters[name] = limiter
    
    def remove_limiter(self, name: str):
        """移除限制器"""
        with self.lock:
            if name in self.limiters:
                del self.limiters[name]
    
    def allow(self, limiter_name: Optional[str] = None) -> bool:
        """
        检查是否允许请求
        
        Args:
            limiter_name: 限制器名称（None表示检查所有）
            
        Returns:
            是否允许
        """
        with self.lock:
            if limiter_name:
                limiter = self.limiters.get(limiter_name)
                return limiter.allow() if limiter else True
            else:
                # 检查所有限制器
                return all(limiter.allow() for limiter in self.limiters.values())
    
    def wait(self, timeout: Optional[float] = None, limiter_name: Optional[str] = None) -> bool:
        """
        等待可用配额
        
        Args:
            timeout: 超时时间
            limiter_name: 限制器名称（None表示等待所有）
            
        Returns:
            是否获取到配额
        """
        start_time = time.time()
        
        with self.lock:
            limiters = [self.limiters[limiter_name]] if limiter_name else list(self.limiters.values())
        
        for limiter in limiters:
            remaining_timeout = None
            if timeout:
                elapsed = time.time() - start_time
                remaining_timeout = max(0, timeout - elapsed)
            
            if not limiter.wait(remaining_timeout):
                return False
        
        return True
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有限制器的统计信息"""
        with self.lock:
            return {name: limiter.get_stats() for name, limiter in self.limiters.items()}


# 全局实例
_rate_limiter = None


def get_rate_limiter(
    algorithm: str = 'token_bucket',
    max_requests: int = 10,
    time_window: float = 1.0
) -> RateLimiter:
    """获取速率限制器实例（单例模式）"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(algorithm, max_requests, time_window)
    return _rate_limiter


if __name__ == '__main__':
    # 测试令牌桶
    print("测试 1: 令牌桶算法")
    print("="*60)
    
    limiter = RateLimiter(
        algorithm='token_bucket',
        max_requests=5,
        time_window=1.0,
        burst_size=2
    )
    
    print(f"配置: 5 请求/秒, 突发 2")
    print(f"初始状态: {limiter.get_stats()}")
    
    # 快速发送请求
    print("\n快速发送 10 个请求:")
    for i in range(10):
        allowed = limiter.allow()
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status}")
    
    # 等待后再试
    print("\n等待 1 秒后再试:")
    time.sleep(1)
    for i in range(3):
        allowed = limiter.allow()
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status}")
    
    # 测试滑动窗口
    print("\n\n测试 2: 滑动窗口算法")
    print("="*60)
    
    limiter2 = RateLimiter(
        algorithm='sliding_window',
        max_requests=3,
        time_window=2.0
    )
    
    print(f"配置: 3 请求/2秒")
    print(f"初始状态: {limiter2.get_stats()}")
    
    print("\n发送请求:")
    for i in range(5):
        allowed = limiter2.allow()
        stats = limiter2.get_stats()
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status} (当前: {stats['current_count']}/3, 等待: {stats['wait_time']:.2f}秒)")
        time.sleep(0.5)
    
    # 测试多级限制器
    print("\n\n测试 3: 多级速率限制器")
    print("="*60)
    
    multi = MultiRateLimiter()
    multi.add_limiter('per_second', RateLimiter('token_bucket', 5, 1.0))
    multi.add_limiter('per_minute', RateLimiter('sliding_window', 20, 60.0))
    
    print("配置:")
    print("  - 每秒限制: 5 请求")
    print("  - 每分钟限制: 20 请求")
    
    print("\n发送请求:")
    for i in range(10):
        allowed = multi.allow()
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status}")
        time.sleep(0.1)
    
    print("\n统计信息:")
    for name, stats in multi.get_all_stats().items():
        print(f"  {name}: {stats}")
