#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件基类 (v2.0.0)

定义插件接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Plugin(ABC):
    """插件基类"""
    
    # 插件元数据
    name: str = "plugin"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    
    def __init__(self):
        """初始化插件"""
        self.enabled = True
        self.config = {}
    
    @abstractmethod
    def on_load(self):
        """插件加载时调用
        
        在插件被加载到系统时调用，用于初始化资源
        """
        pass
    
    @abstractmethod
    def on_unload(self):
        """插件卸载时调用
        
        在插件被卸载时调用，用于清理资源
        """
        pass
    
    def on_enable(self):
        """插件启用时调用"""
        self.enabled = True
    
    def on_disable(self):
        """插件禁用时调用"""
        self.enabled = False
    
    def get_info(self) -> Dict[str, str]:
        """获取插件信息
        
        Returns:
            插件信息字典
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'enabled': self.enabled
        }
    
    def set_config(self, config: Dict[str, Any]):
        """设置插件配置
        
        Args:
            config: 配置字典
        """
        self.config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)


class ProcessorPlugin(Plugin):
    """处理器插件基类"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        pass


class ServicePlugin(Plugin):
    """服务插件基类"""
    
    @abstractmethod
    def start(self):
        """启动服务"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止服务"""
        pass


class HookPlugin(Plugin):
    """钩子插件基类"""
    
    @abstractmethod
    def on_before_process(self, data: Any) -> Any:
        """处理前钩子
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        pass
    
    @abstractmethod
    def on_after_process(self, data: Any, result: Any) -> Any:
        """处理后钩子
        
        Args:
            data: 输入数据
            result: 处理结果
            
        Returns:
            处理后的结果
        """
        pass
