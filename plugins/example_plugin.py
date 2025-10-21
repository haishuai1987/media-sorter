#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例插件 (v2.0.0)

演示如何创建插件
"""

from plugins.base import ProcessorPlugin


class ExamplePlugin(ProcessorPlugin):
    """示例插件"""
    
    name = "example"
    version = "1.0.0"
    description = "这是一个示例插件"
    author = "Media Renamer Team"
    
    def on_load(self):
        """插件加载时调用"""
        print(f"[{self.name}] 插件已加载")
    
    def on_unload(self):
        """插件卸载时调用"""
        print(f"[{self.name}] 插件已卸载")
    
    def process(self, data):
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        print(f"[{self.name}] 处理数据: {data}")
        
        # 示例：将字符串转为大写
        if isinstance(data, str):
            return data.upper()
        
        return data
