"""
核心模块 (v2.0.0)

提供配置管理、日志系统和工具函数
"""

from .config import ConfigManager
from .logger import Logger
from .utils import Utils

__all__ = ['ConfigManager', 'Logger', 'Utils']
__version__ = '2.0.0'
