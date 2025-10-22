#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理模块
管理用户的配置预设
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "data/configs"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.configs_file = self.config_dir / "configs.json"
        self._ensure_configs_file()
    
    def _ensure_configs_file(self):
        """确保配置文件存在"""
        if not self.configs_file.exists():
            self._save_configs([])
    
    def _load_configs(self) -> List[Dict[str, Any]]:
        """加载所有配置"""
        try:
            with open(self.configs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []
    
    def _save_configs(self, configs: List[Dict[str, Any]]):
        """保存所有配置"""
        with open(self.configs_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
    
    def add_config(self, config: Dict[str, Any]) -> str:
        """
        添加配置
        
        Args:
            config: 配置数据
            
        Returns:
            配置 ID
        """
        configs = self._load_configs()
        
        # 生成 ID
        config_id = f"config_{int(datetime.now().timestamp() * 1000)}"
        
        # 添加元数据
        config['id'] = config_id
        config['created_at'] = datetime.now().isoformat()
        config['updated_at'] = datetime.now().isoformat()
        
        configs.append(config)
        self._save_configs(configs)
        
        return config_id
    
    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        获取配置
        
        Args:
            config_id: 配置 ID
            
        Returns:
            配置数据
        """
        configs = self._load_configs()
        for config in configs:
            if config.get('id') == config_id:
                return config
        return None
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有配置
        
        Returns:
            配置列表
        """
        return self._load_configs()
    
    def update_config(self, config_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_id: 配置 ID
            updates: 更新数据
            
        Returns:
            是否成功
        """
        configs = self._load_configs()
        
        for i, config in enumerate(configs):
            if config.get('id') == config_id:
                config.update(updates)
                config['updated_at'] = datetime.now().isoformat()
                configs[i] = config
                self._save_configs(configs)
                return True
        
        return False
    
    def delete_config(self, config_id: str) -> bool:
        """
        删除配置
        
        Args:
            config_id: 配置 ID
            
        Returns:
            是否成功
        """
        configs = self._load_configs()
        original_length = len(configs)
        
        configs = [c for c in configs if c.get('id') != config_id]
        
        if len(configs) < original_length:
            self._save_configs(configs)
            return True
        
        return False
    
    def export_config(self, config_id: str) -> Optional[str]:
        """
        导出配置为 JSON 字符串
        
        Args:
            config_id: 配置 ID
            
        Returns:
            JSON 字符串
        """
        config = self.get_config(config_id)
        if config:
            return json.dumps(config, ensure_ascii=False, indent=2)
        return None
    
    def import_config(self, config_json: str) -> Optional[str]:
        """
        导入配置
        
        Args:
            config_json: JSON 字符串
            
        Returns:
            配置 ID
        """
        try:
            config = json.loads(config_json)
            
            # 移除旧的 ID 和时间戳
            config.pop('id', None)
            config.pop('created_at', None)
            config.pop('updated_at', None)
            
            return self.add_config(config)
        except Exception as e:
            print(f"导入配置失败: {e}")
            return None
    
    def get_default_configs(self) -> List[Dict[str, Any]]:
        """
        获取默认配置模板
        
        Returns:
            默认配置列表
        """
        return [
            {
                'name': '电影 - 标准配置',
                'description': '适用于大多数电影文件',
                'template': 'movie_default',
                'priority': 5,
                'use_queue': True,
                'settings': {
                    'auto_rename': True,
                    'backup_original': False,
                    'quality_threshold': 80
                }
            },
            {
                'name': '电视剧 - 标准配置',
                'description': '适用于电视剧集',
                'template': 'tv_default',
                'priority': 5,
                'use_queue': True,
                'settings': {
                    'auto_rename': True,
                    'backup_original': False,
                    'quality_threshold': 80
                }
            },
            {
                'name': '高质量 - 严格模式',
                'description': '只处理高质量识别结果',
                'template': 'movie_detailed',
                'priority': 7,
                'use_queue': True,
                'settings': {
                    'auto_rename': False,
                    'backup_original': True,
                    'quality_threshold': 90
                }
            }
        ]


# 全局单例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == '__main__':
    # 测试
    manager = get_config_manager()
    
    # 添加测试配置
    test_config = {
        'name': '测试配置',
        'description': '这是一个测试配置',
        'template': 'movie_default',
        'priority': 5,
        'use_queue': True,
        'settings': {
            'auto_rename': True,
            'backup_original': False
        }
    }
    
    config_id = manager.add_config(test_config)
    print(f"添加配置 ID: {config_id}")
    
    # 获取所有配置
    configs = manager.get_all_configs()
    print(f"\n所有配置:")
    for config in configs:
        print(f"  {config['id']}: {config['name']}")
    
    # 获取默认配置
    defaults = manager.get_default_configs()
    print(f"\n默认配置模板:")
    for config in defaults:
        print(f"  - {config['name']}: {config['description']}")
