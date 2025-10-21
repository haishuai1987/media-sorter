#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 (v2.0.0)

提供统一的配置管理接口
"""

import json
import os
from typing import Any, Optional, Dict
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'version': '2.0.0',
        'tmdb_api_key': '',
        'tmdb_proxy': '',
        'douban_cookie': '',
        'max_workers': 4,
        'enable_checkpoint': True,
        'enable_rollback': True,
        'log_level': 'INFO',
        'cache_enabled': True,
        'cache_ttl': 3600,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or self._get_default_config_file()
        self.config = self.DEFAULT_CONFIG.copy()
        self._ensure_config_dir()
    
    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        home = Path.home()
        config_dir = home / '.media-renamer'
        return str(config_dir / 'config.json')
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def load(self, config_file: Optional[str] = None) -> bool:
        """加载配置
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否成功
        """
        if config_file:
            self.config_file = config_file
        
        if not os.path.exists(self.config_file):
            # 配置文件不存在，使用默认配置
            return True
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # 合并配置
                self.config.update(user_config)
                
                # 迁移旧版本配置
                self._migrate_config()
                
                return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
    
    def save(self, config_file: Optional[str] = None) -> bool:
        """保存配置
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否成功
        """
        if config_file:
            self.config_file = config_file
        
        try:
            self._ensure_config_dir()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_all(self) -> Dict:
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self.config.copy()
    
    def reset(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
    
    def _migrate_config(self):
        """迁移旧版本配置"""
        # 检查版本
        version = self.config.get('version', '1.0.0')
        
        if version.startswith('1.'):
            # 从 v1.x 迁移到 v2.0
            print(f"检测到旧版本配置 ({version})，正在迁移...")
            
            # 添加新配置项
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in self.config:
                    self.config[key] = value
            
            # 更新版本号
            self.config['version'] = '2.0.0'
            
            # 保存迁移后的配置
            self.save()
            
            print("配置迁移完成")
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置
        
        Returns:
            (是否有效, 错误消息)
        """
        # 检查必需的配置项
        if not self.config.get('tmdb_api_key'):
            return False, "TMDB API Key 未配置"
        
        # 检查并发数
        max_workers = self.config.get('max_workers', 4)
        if not isinstance(max_workers, int) or max_workers < 1:
            return False, "max_workers 必须是正整数"
        
        return True, None


# 全局配置实例
_global_config = None


def get_config() -> ConfigManager:
    """获取全局配置实例
    
    Returns:
        配置管理器实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
        _global_config.load()
    return _global_config
