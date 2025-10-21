"""
插件系统 (v2.0.0)

提供插件加载和管理功能
"""

from .base import Plugin
from .loader import PluginLoader

__all__ = ['Plugin', 'PluginLoader']
