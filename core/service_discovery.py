# -*- coding: utf-8 -*-
"""
服务发现工具模块
v4.0.0 新增
"""

import consul
import os
import time
from typing import List, Dict, Optional


class ServiceDiscovery:
    """服务发现客户端封装"""
    
    def __init__(self, consul_host: str = None, consul_port: int = 8500):
        """
        初始化服务发现客户端
        
        Args:
            consul_host: Consul 服务器地址
            consul_port: Consul 服务器端口
        """
        self.consul_host = consul_host or os.getenv('CONSUL_HOST', 'localhost')
        self.consul_port = consul_port
        self.client = consul.Consul(host=self.consul_host, port=self.consul_port)
        self.cache = {}
        self.cache_ttl = 30  # 缓存30秒
    
    def register_service(
        self,
        service_name: str,
        service_id: str,
        host: str,
        port: int,
        health_check_url: str = None,
        health_check_interval: str = "10s",
        tags: List[str] = None
    ) -> bool:
        """
        注册服务到 Consul
        
        Args:
            service_name: 服务名称
            service_id: 服务实例ID
            host: 服务主机地址
            port: 服务端口
            health_check_url: 健康检查URL
            health_check_interval: 健康检查间隔
            tags: 服务标签
        
        Returns:
            bool: 注册是否成功
        """
        try:
            # 默认健康检查URL
            if not health_check_url:
                health_check_url = f"http://{host}:{port}/health"
            
            # 创建健康检查配置
            check = consul.Check.http(health_check_url, interval=health_check_interval)
            
            # 注册服务
            self.client.agent.service.register(
                name=service_name,
                service_id=service_id,
                address=host,
                port=port,
                tags=tags or [],
                check=check
            )
            
            print(f"✓ 服务已注册到 Consul: {service_name} ({service_id}) at {host}:{port}")
            return True
            
        except Exception as e:
            print(f"✗ 服务注册失败: {e}")
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        从 Consul 注销服务
        
        Args:
            service_id: 服务实例ID
        
        Returns:
            bool: 注销是否成功
        """
        try:
            self.client.agent.service.deregister(service_id)
            print(f"✓ 服务已从 Consul 注销: {service_id}")
            return True
            
        except Exception as e:
            print(f"✗ 服务注销失败: {e}")
            return False
    
    def get_service_instances(
        self,
        service_name: str,
        passing_only: bool = True,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        获取服务实例列表
        
        Args:
            service_name: 服务名称
            passing_only: 是否只返回健康的实例
            use_cache: 是否使用缓存
        
        Returns:
            List[Dict]: 服务实例列表
        """
        # 检查缓存
        if use_cache and service_name in self.cache:
            cached_data, timestamp = self.cache[service_name]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        try:
            # 从 Consul 获取服务实例
            _, services = self.client.health.service(service_name, passing=passing_only)
            
            instances = []
            for service in services:
                service_info = service['Service']
                instances.append({
                    'id': service_info['ID'],
                    'service': service_info['Service'],
                    'host': service_info['Address'],
                    'port': service_info['Port'],
                    'url': f"http://{service_info['Address']}:{service_info['Port']}",
                    'tags': service_info.get('Tags', [])
                })
            
            # 更新缓存
            if use_cache:
                self.cache[service_name] = (instances, time.time())
            
            return instances
            
        except Exception as e:
            print(f"✗ 获取服务实例失败: {e}")
            return []
    
    def get_service_health(self, service_name: str) -> Dict:
        """
        获取服务健康状态
        
        Args:
            service_name: 服务名称
        
        Returns:
            Dict: 服务健康状态信息
        """
        try:
            all_instances = self.get_service_instances(service_name, passing_only=False, use_cache=False)
            healthy_instances = self.get_service_instances(service_name, passing_only=True, use_cache=False)
            
            return {
                'service': service_name,
                'total_instances': len(all_instances),
                'healthy_instances': len(healthy_instances),
                'unhealthy_instances': len(all_instances) - len(healthy_instances),
                'available': len(healthy_instances) > 0,
                'instances': healthy_instances
            }
            
        except Exception as e:
            print(f"✗ 获取服务健康状态失败: {e}")
            return {
                'service': service_name,
                'total_instances': 0,
                'healthy_instances': 0,
                'unhealthy_instances': 0,
                'available': False,
                'instances': []
            }
    
    def clear_cache(self, service_name: str = None):
        """
        清除缓存
        
        Args:
            service_name: 服务名称，如果为None则清除所有缓存
        """
        if service_name:
            self.cache.pop(service_name, None)
        else:
            self.cache.clear()


# 全局服务发现实例
_service_discovery = None


def get_service_discovery() -> ServiceDiscovery:
    """获取全局服务发现实例"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
    return _service_discovery


def register_service(
    service_name: str,
    host: str = None,
    port: int = None,
    **kwargs
) -> bool:
    """
    便捷函数：注册服务
    
    Args:
        service_name: 服务名称
        host: 服务主机地址
        port: 服务端口
        **kwargs: 其他参数
    
    Returns:
        bool: 注册是否成功
    """
    host = host or os.getenv(f'{service_name.upper().replace("-", "_")}_HOST', 'localhost')
    port = port or int(os.getenv(f'{service_name.upper().replace("-", "_")}_PORT', 8000))
    service_id = f"{service_name}-{host}-{port}"
    
    sd = get_service_discovery()
    return sd.register_service(service_name, service_id, host, port, **kwargs)


def deregister_service(service_name: str, host: str = None, port: int = None) -> bool:
    """
    便捷函数：注销服务
    
    Args:
        service_name: 服务名称
        host: 服务主机地址
        port: 服务端口
    
    Returns:
        bool: 注销是否成功
    """
    host = host or os.getenv(f'{service_name.upper().replace("-", "_")}_HOST', 'localhost')
    port = port or int(os.getenv(f'{service_name.upper().replace("-", "_")}_PORT', 8000))
    service_id = f"{service_name}-{host}-{port}"
    
    sd = get_service_discovery()
    return sd.deregister_service(service_id)


def get_service_instances(service_name: str, **kwargs) -> List[Dict]:
    """
    便捷函数：获取服务实例
    
    Args:
        service_name: 服务名称
        **kwargs: 其他参数
    
    Returns:
        List[Dict]: 服务实例列表
    """
    sd = get_service_discovery()
    return sd.get_service_instances(service_name, **kwargs)
