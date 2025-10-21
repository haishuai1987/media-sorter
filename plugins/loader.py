#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件加载器 (v2.0.0)

负责插件的加载、卸载和管理
"""

import os
import importlib
import importlib.util
from typing import Dict, List, Optional, Type
from .base import Plugin


class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugin_dir: str = 'plugins'):
        """初始化
        
        Args:
            plugin_dir: 插件目录
        """
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_classes: Dict[str, Type[Plugin]] = {}
    
    def discover_plugins(self) -> List[str]:
        """发现插件
        
        Returns:
            插件名称列表
        """
        if not os.path.exists(self.plugin_dir):
            return []
        
        plugin_names = []
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]
                plugin_names.append(plugin_name)
        
        return plugin_names
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        if plugin_name in self.plugins:
            print(f"插件 {plugin_name} 已加载")
            return True
        
        try:
            # 导入插件模块
            plugin_file = os.path.join(self.plugin_dir, f'{plugin_name}.py')
            
            if not os.path.exists(plugin_file):
                print(f"插件文件不存在: {plugin_file}")
                return False
            
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if spec is None or spec.loader is None:
                print(f"无法加载插件: {plugin_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Plugin) and 
                    attr is not Plugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                print(f"插件 {plugin_name} 中未找到Plugin类")
                return False
            
            # 实例化插件
            plugin = plugin_class()
            
            # 调用加载钩子
            plugin.on_load()
            
            # 保存插件
            self.plugins[plugin_name] = plugin
            self.plugin_classes[plugin_name] = plugin_class
            
            print(f"✓ 插件 {plugin_name} 加载成功")
            return True
            
        except Exception as e:
            print(f"✗ 加载插件 {plugin_name} 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        if plugin_name not in self.plugins:
            print(f"插件 {plugin_name} 未加载")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            
            # 调用卸载钩子
            plugin.on_unload()
            
            # 移除插件
            del self.plugins[plugin_name]
            del self.plugin_classes[plugin_name]
            
            print(f"✓ 插件 {plugin_name} 卸载成功")
            return True
            
        except Exception as e:
            print(f"✗ 卸载插件 {plugin_name} 失败: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
        
        return self.load_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例，不存在返回None
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict]:
        """列出所有已加载的插件
        
        Returns:
            插件信息列表
        """
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.on_enable()
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.on_disable()
            return True
        return False
    
    def load_all_plugins(self) -> int:
        """加载所有插件
        
        Returns:
            成功加载的插件数量
        """
        plugin_names = self.discover_plugins()
        success_count = 0
        
        for plugin_name in plugin_names:
            if self.load_plugin(plugin_name):
                success_count += 1
        
        return success_count
