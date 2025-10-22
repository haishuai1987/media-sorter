#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检测和配置模块
自动检测部署环境并提供相应配置
"""

import os
import socket
from typing import Dict, Any


class Environment:
    """环境检测和配置管理"""
    
    # 环境类型
    LOCAL = 'local'
    CLOUD = 'cloud'
    DOCKER = 'docker'
    
    def __init__(self):
        self._env_type = None
        self._config = None
    
    @property
    def type(self) -> str:
        """获取环境类型"""
        if self._env_type is None:
            self._env_type = self.detect()
        return self._env_type
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取环境配置"""
        if self._config is None:
            self._config = self.get_config(self.type)
        return self._config
    
    def detect(self) -> str:
        """
        检测部署环境
        
        Returns:
            环境类型: 'local', 'cloud', 'docker'
        """
        try:
            # 1. 检查环境变量（最高优先级）
            deploy_env = os.environ.get('DEPLOY_ENV', '').lower()
            if deploy_env in [self.LOCAL, self.CLOUD, self.DOCKER]:
                print(f"✓ 通过环境变量检测到: {deploy_env}")
                return deploy_env
            
            # 2. 检查是否在 Docker 容器中
            if self._is_docker():
                print(f"✓ 检测到 Docker 容器环境")
                return self.DOCKER
            
            # 3. 检查云服务器标识
            if self._is_cloud():
                print(f"✓ 检测到云服务器环境")
                return self.CLOUD
            
            # 4. 检查 IP 地址（判断是否为本地网络）
            if self._is_local_network():
                print(f"✓ 检测到本地网络环境")
                return self.LOCAL
            
            # 5. 默认返回本地环境
            print(f"✓ 使用默认本地环境")
            return self.LOCAL
            
        except Exception as e:
            print(f"⚠ 环境检测失败: {e}，使用默认本地环境")
            return self.LOCAL
    
    def _is_docker(self) -> bool:
        """检查是否在 Docker 容器中"""
        # 检查 .dockerenv 文件
        if os.path.exists('/.dockerenv'):
            return True
        
        # 检查 cgroup 文件
        if os.path.exists('/proc/1/cgroup'):
            try:
                with open('/proc/1/cgroup', 'r') as f:
                    content = f.read()
                    if 'docker' in content or 'containerd' in content:
                        return True
            except:
                pass
        
        # 检查 Podman 容器
        if os.path.exists('/run/.containerenv'):
            return True
        
        return False
    
    def _is_cloud(self) -> bool:
        """检查是否为云服务器"""
        # 检查云服务器标识文件
        cloud_indicators = [
            '/etc/cloud',           # Cloud-init
            '/var/lib/cloud',       # Cloud-init data
            '/run/cloud-init',      # Cloud-init runtime
        ]
        
        for indicator in cloud_indicators:
            if os.path.exists(indicator):
                return True
        
        # 检查云服务商特定文件
        cloud_vendors = [
            '/sys/class/dmi/id/product_name',  # 可能包含云服务商信息
            '/sys/class/dmi/id/sys_vendor',
        ]
        
        for vendor_file in cloud_vendors:
            if os.path.exists(vendor_file):
                try:
                    with open(vendor_file, 'r') as f:
                        content = f.read().lower()
                        # 常见云服务商标识
                        if any(vendor in content for vendor in [
                            'amazon', 'ec2', 'aws',
                            'google', 'gce',
                            'microsoft', 'azure',
                            'alibaba', 'aliyun',
                            'tencent', 'qcloud',
                            'digitalocean', 'droplet',
                            'linode', 'vultr'
                        ]):
                            return True
                except:
                    pass
        
        return False
    
    def _is_local_network(self) -> bool:
        """检查是否为本地网络"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # 私有 IP 地址范围
            private_ranges = [
                '192.168.',  # Class C private
                '10.',       # Class A private
                '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.',
                '172.24.', '172.25.', '172.26.', '172.27.',
                '172.28.', '172.29.', '172.30.', '172.31.',  # Class B private
                '127.',      # Loopback
            ]
            
            return any(local_ip.startswith(prefix) for prefix in private_ranges)
            
        except Exception as e:
            print(f"⚠ IP 检测失败: {e}")
            return True  # 默认认为是本地
    
    def get_config(self, env_type: str) -> Dict[str, Any]:
        """
        根据环境类型获取配置
        
        Args:
            env_type: 环境类型
            
        Returns:
            配置字典
        """
        configs = {
            self.LOCAL: {
                'host': '0.0.0.0',  # 监听所有接口，方便局域网访问
                'port': 8090,       # 避免与 qBittorrent(8080) 冲突
                'debug': True,
                'workers': 1,
                'timeout': 30,
                'description': '本地开发环境'
            },
            self.CLOUD: {
                'host': '0.0.0.0',  # 监听所有接口
                'port': 8000,       # 标准 HTTP 端口
                'debug': False,
                'workers': 4,       # 多进程
                'timeout': 60,
                'description': '云服务器生产环境'
            },
            self.DOCKER: {
                'host': '0.0.0.0',  # 容器内监听所有接口
                'port': 8090,       # 与本地保持一致
                'debug': False,
                'workers': 2,
                'timeout': 45,
                'description': 'Docker 容器环境'
            }
        }
        
        return configs.get(env_type, configs[self.LOCAL])
    
    def print_info(self):
        """打印环境信息"""
        print("\n" + "="*60)
        print("环境信息")
        print("="*60)
        print(f"环境类型: {self.type}")
        print(f"描述: {self.config['description']}")
        print(f"监听地址: {self.config['host']}:{self.config['port']}")
        print(f"调试模式: {'开启' if self.config['debug'] else '关闭'}")
        print(f"工作进程: {self.config['workers']}")
        print(f"超时时间: {self.config['timeout']}秒")
        print("="*60 + "\n")


# 全局单例
_environment = None


def get_environment() -> Environment:
    """获取环境实例（单例模式）"""
    global _environment
    if _environment is None:
        _environment = Environment()
    return _environment


def detect_environment() -> str:
    """快捷方法：检测环境类型"""
    return get_environment().type


def get_environment_config() -> Dict[str, Any]:
    """快捷方法：获取环境配置"""
    return get_environment().config


if __name__ == '__main__':
    # 测试环境检测
    env = get_environment()
    env.print_info()
    
    # 测试不同环境配置
    print("\n所有环境配置:")
    for env_type in [Environment.LOCAL, Environment.CLOUD, Environment.DOCKER]:
        config = env.get_config(env_type)
        print(f"\n{env_type.upper()}:")
        for key, value in config.items():
            print(f"  {key}: {value}")
