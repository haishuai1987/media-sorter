#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义识别词模块
允许用户自定义屏蔽词、替换词等规则
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class CustomWords:
    """自定义识别词管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化识别词管理器
        
        Args:
            config_file: 配置文件路径，默认为 ~/.media-renamer/custom_words.json
        """
        if config_file is None:
            config_file = os.path.expanduser('~/.media-renamer/custom_words.json')
        
        self.config_file = config_file
        self.words: List[Dict[str, Any]] = []
        self.load()
    
    def load(self) -> bool:
        """
        加载识别词配置
        
        Returns:
            是否加载成功
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.words = data.get('words', [])
                    print(f"✓ 加载了 {len(self.words)} 个自定义识别词")
                    return True
            else:
                print("ℹ 未找到自定义识别词配置，使用默认配置")
                self.words = self._get_default_words()
                self.save()  # 保存默认配置
                return True
        except Exception as e:
            print(f"⚠ 加载识别词失败: {e}")
            self.words = []
            return False
    
    def save(self) -> bool:
        """
        保存识别词配置
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '1.0',
                    'words': self.words
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 保存了 {len(self.words)} 个自定义识别词")
            return True
            
        except Exception as e:
            print(f"⚠ 保存识别词失败: {e}")
            return False
    
    def _get_default_words(self) -> List[Dict[str, Any]]:
        """获取默认识别词"""
        return [
            # 屏蔽词示例
            {
                'type': 'block',
                'pattern': 'RARBG',
                'description': '屏蔽 RARBG 标识',
                'enabled': True
            },
            {
                'type': 'block',
                'pattern': 'YTS',
                'description': '屏蔽 YTS 标识',
                'enabled': True
            },
            # 替换词示例
            {
                'type': 'replace',
                'old': 'BluRay',
                'new': 'Blu-ray',
                'description': '统一蓝光格式',
                'enabled': False  # 默认禁用
            },
        ]
    
    def apply(self, title: str) -> str:
        """
        应用识别词到标题
        
        Args:
            title: 原始标题
            
        Returns:
            处理后的标题
        """
        if not title or not self.words:
            return title
        
        result = title
        applied_count = 0
        
        for word in self.words:
            # 跳过禁用的规则
            if not word.get('enabled', True):
                continue
            
            word_type = word.get('type', '')
            
            try:
                if word_type == 'block':
                    # 屏蔽词：移除内容
                    pattern = word.get('pattern', '')
                    if pattern and pattern in result:
                        result = result.replace(pattern, '')
                        applied_count += 1
                
                elif word_type == 'replace':
                    # 替换词：修正标题
                    old = word.get('old', '')
                    new = word.get('new', '')
                    if old and old in result:
                        result = result.replace(old, new)
                        applied_count += 1
                
                elif word_type == 'regex_block':
                    # 正则屏蔽：使用正则表达式移除
                    pattern = word.get('pattern', '')
                    if pattern:
                        result = re.sub(pattern, '', result)
                        applied_count += 1
                
                elif word_type == 'regex_replace':
                    # 正则替换：使用正则表达式替换
                    pattern = word.get('pattern', '')
                    replacement = word.get('replacement', '')
                    if pattern:
                        result = re.sub(pattern, replacement, result)
                        applied_count += 1
                        
            except Exception as e:
                print(f"⚠ 应用识别词失败 ({word.get('description', 'unknown')}): {e}")
        
        # 清理多余空格
        result = ' '.join(result.split())
        
        if applied_count > 0:
            print(f"✓ 应用了 {applied_count} 个识别词规则")
        
        return result
    
    def add_word(self, word: Dict[str, Any]) -> bool:
        """
        添加识别词
        
        Args:
            word: 识别词配置
            
        Returns:
            是否添加成功
        """
        # 验证必需字段
        if 'type' not in word:
            print("⚠ 识别词必须包含 type 字段")
            return False
        
        word_type = word['type']
        
        if word_type in ['block', 'regex_block']:
            if 'pattern' not in word:
                print("⚠ 屏蔽词必须包含 pattern 字段")
                return False
        
        elif word_type in ['replace']:
            if 'old' not in word or 'new' not in word:
                print("⚠ 替换词必须包含 old 和 new 字段")
                return False
        
        elif word_type in ['regex_replace']:
            if 'pattern' not in word or 'replacement' not in word:
                print("⚠ 正则替换必须包含 pattern 和 replacement 字段")
                return False
        
        else:
            print(f"⚠ 不支持的识别词类型: {word_type}")
            return False
        
        # 添加默认字段
        if 'enabled' not in word:
            word['enabled'] = True
        if 'description' not in word:
            word['description'] = ''
        
        self.words.append(word)
        return self.save()
    
    def remove_word(self, index: int) -> bool:
        """
        删除识别词
        
        Args:
            index: 识别词索引
            
        Returns:
            是否删除成功
        """
        if 0 <= index < len(self.words):
            removed = self.words.pop(index)
            print(f"✓ 删除识别词: {removed.get('description', 'unknown')}")
            return self.save()
        else:
            print(f"⚠ 无效的索引: {index}")
            return False
    
    def update_word(self, index: int, word: Dict[str, Any]) -> bool:
        """
        更新识别词
        
        Args:
            index: 识别词索引
            word: 新的识别词配置
            
        Returns:
            是否更新成功
        """
        if 0 <= index < len(self.words):
            self.words[index] = word
            print(f"✓ 更新识别词: {word.get('description', 'unknown')}")
            return self.save()
        else:
            print(f"⚠ 无效的索引: {index}")
            return False
    
    def toggle_word(self, index: int) -> bool:
        """
        切换识别词启用状态
        
        Args:
            index: 识别词索引
            
        Returns:
            是否切换成功
        """
        if 0 <= index < len(self.words):
            self.words[index]['enabled'] = not self.words[index].get('enabled', True)
            status = "启用" if self.words[index]['enabled'] else "禁用"
            print(f"✓ {status}识别词: {self.words[index].get('description', 'unknown')}")
            return self.save()
        else:
            print(f"⚠ 无效的索引: {index}")
            return False
    
    def get_words(self) -> List[Dict[str, Any]]:
        """获取所有识别词"""
        return self.words.copy()
    
    def clear_words(self) -> bool:
        """清空所有识别词"""
        self.words = []
        return self.save()
    
    def print_words(self):
        """打印所有识别词"""
        print("\n" + "="*60)
        print("自定义识别词列表")
        print("="*60)
        
        if not self.words:
            print("(无)")
        else:
            for i, word in enumerate(self.words):
                status = "✓" if word.get('enabled', True) else "✗"
                word_type = word.get('type', 'unknown')
                description = word.get('description', '无描述')
                
                print(f"\n[{i}] {status} {word_type.upper()}")
                print(f"    描述: {description}")
                
                if word_type == 'block':
                    print(f"    屏蔽: {word.get('pattern', '')}")
                elif word_type == 'replace':
                    print(f"    替换: {word.get('old', '')} → {word.get('new', '')}")
                elif word_type == 'regex_block':
                    print(f"    正则屏蔽: {word.get('pattern', '')}")
                elif word_type == 'regex_replace':
                    print(f"    正则替换: {word.get('pattern', '')} → {word.get('replacement', '')}")
        
        print("\n" + "="*60 + "\n")


# 全局单例
_custom_words = None


def get_custom_words() -> CustomWords:
    """获取自定义识别词实例（单例模式）"""
    global _custom_words
    if _custom_words is None:
        _custom_words = CustomWords()
    return _custom_words


if __name__ == '__main__':
    # 测试自定义识别词
    print("测试自定义识别词模块")
    print("="*60)
    
    # 创建实例
    cw = CustomWords()
    
    # 显示当前识别词
    cw.print_words()
    
    # 测试应用识别词
    test_titles = [
        "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv",
        "Inception.2010.720p.BluRay.x264-YTS.mp4",
        "Interstellar.2014.1080p.WEB-DL.H264.AAC.mkv",
    ]
    
    print("测试应用识别词:")
    print("-" * 60)
    for title in test_titles:
        result = cw.apply(title)
        if result != title:
            print(f"原始: {title}")
            print(f"结果: {result}")
            print()
    
    # 测试添加识别词
    print("\n测试添加识别词:")
    print("-" * 60)
    cw.add_word({
        'type': 'block',
        'pattern': 'WEB-DL',
        'description': '屏蔽 WEB-DL 标识',
        'enabled': True
    })
    
    # 再次显示
    cw.print_words()
