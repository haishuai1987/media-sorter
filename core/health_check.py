# -*- coding: utf-8 -*-
"""
健康检查模块
v4.0.0 新增
"""

from typing import Dict, List, Callable
from datetime import datetime
import time


class HealthCheck:
    """健康检查基类"""
    
    def __init__(self, service_name: str, version: str = "4.0.0"):
        """
        初始化健康检查
        
        Args:
            service_name: 服务名称
            version: 服务版本
        """
        self.service_name = service_name
        self.version = version
        self.checks = []
        self.start_time = time.time()
    
    def add_check(self, name: str, check_func: Callable, critical: bool = True):
        """
        添加健康检查项
        
        Args:
            name: 检查项名称
            check_func: 检查函数，返回 (bool, str) 表示 (是否健康, 消息)
            critical: 是否为关键检查项
        """
        self.checks.append({
            'name': name,
            'func': check_func,
            'critical': critical
        })
    
    def check_database(self, db) -> tuple:
        """
        检查数据库连接
        
        Args:
            db: 数据库实例
        
        Returns:
            tuple: (是否健康, 消息)
        """
        try:
            # 执行简单查询测试连接
            db.session.execute('SELECT 1')
            return True, "Database connection OK"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
    
    def check_redis(self, redis_client) -> tuple:
        """
        检查 Redis 连接
        
        Args:
            redis_client: Redis 客户端实例
        
        Returns:
            tuple: (是否健康, 消息)
        """
        try:
            redis_client.ping()
            return True, "Redis connection OK"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"
    
    def check_service_dependency(self, service_name: str, get_instances_func: Callable) -> tuple:
        """
        检查服务依赖
        
        Args:
            service_name: 依赖的服务名称
            get_instances_func: 获取服务实例的函数
        
        Returns:
            tuple: (是否健康, 消息)
        """
        try:
            instances = get_instances_func(service_name)
            if instances:
                return True, f"{service_name} available ({len(instances)} instances)"
            else:
                return False, f"{service_name} not available"
        except Exception as e:
            return False, f"{service_name} check failed: {str(e)}"
    
    def run_checks(self) -> Dict:
        """
        运行所有健康检查
        
        Returns:
            Dict: 健康检查结果
        """
        results = []
        all_healthy = True
        critical_healthy = True
        
        for check in self.checks:
            try:
                start = time.time()
                healthy, message = check['func']()
                duration = time.time() - start
                
                results.append({
                    'name': check['name'],
                    'healthy': healthy,
                    'message': message,
                    'critical': check['critical'],
                    'duration_ms': round(duration * 1000, 2)
                })
                
                if not healthy:
                    all_healthy = False
                    if check['critical']:
                        critical_healthy = False
                        
            except Exception as e:
                results.append({
                    'name': check['name'],
                    'healthy': False,
                    'message': f"Check failed: {str(e)}",
                    'critical': check['critical'],
                    'duration_ms': 0
                })
                all_healthy = False
                if check['critical']:
                    critical_healthy = False
        
        # 计算运行时间
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = self._format_uptime(uptime_seconds)
        
        return {
            'service': self.service_name,
            'version': self.version,
            'status': 'healthy' if critical_healthy else 'unhealthy',
            'all_checks_passed': all_healthy,
            'critical_checks_passed': critical_healthy,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'uptime': uptime_str,
            'uptime_seconds': uptime_seconds,
            'checks': results
        }
    
    def _format_uptime(self, seconds: int) -> str:
        """
        格式化运行时间
        
        Args:
            seconds: 秒数
        
        Returns:
            str: 格式化的时间字符串
        """
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def get_simple_status(self) -> Dict:
        """
        获取简单的健康状态（不运行检查）
        
        Returns:
            Dict: 简单的状态信息
        """
        uptime_seconds = int(time.time() - self.start_time)
        
        return {
            'service': self.service_name,
            'version': self.version,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'uptime_seconds': uptime_seconds
        }


def create_health_check_endpoint(health_check: HealthCheck, detailed: bool = True):
    """
    创建健康检查端点函数
    
    Args:
        health_check: HealthCheck 实例
        detailed: 是否返回详细信息
    
    Returns:
        function: Flask 路由函数
    """
    def health_endpoint():
        if detailed:
            result = health_check.run_checks()
            status_code = 200 if result['critical_checks_passed'] else 503
        else:
            result = health_check.get_simple_status()
            status_code = 200
        
        return result, status_code
    
    return health_endpoint
