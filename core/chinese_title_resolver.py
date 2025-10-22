#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文标题解析器
整合高级识别器 + TMDB/豆瓣查询，确保所有标题都是中文
"""

import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, Tuple


class ChineseTitleResolver:
    """中文标题解析器 - 确保所有标题都转换为中文"""
    
    def __init__(self, tmdb_api_key: str = None, douban_cookie: str = None):
        self.tmdb_api_key = tmdb_api_key
        self.douban_cookie = douban_cookie
        
        # 缓存
        self._cache = {}
    
    def resolve(self, english_title: str, year: int = None, is_tv: bool = False) -> Optional[str]:
        """
        解析英文标题为中文标题
        
        Args:
            english_title: 英文标题
            year: 年份
            is_tv: 是否为电视剧
            
        Returns:
            中文标题，如果查询失败则返回 None
        """
        # 检查缓存
        cache_key = f"{english_title}_{year}_{is_tv}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 如果已经是中文，直接返回
        if self._is_chinese(english_title):
            return english_title
        
        # 优先使用豆瓣（中文结果更准确）
        chinese_title = None
        if self.douban_cookie:
            chinese_title = self._query_douban(english_title, year, is_tv)
        
        # 如果豆瓣失败，使用 TMDB
        if not chinese_title and self.tmdb_api_key:
            chinese_title = self._query_tmdb(english_title, year, is_tv)
        
        # 缓存结果
        if chinese_title:
            self._cache[cache_key] = chinese_title
        
        return chinese_title
    
    def _is_chinese(self, text: str) -> bool:
        """检查文本是否包含中文"""
        if not text:
            return False
        # 检查是否有中文字符
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def _query_douban(self, title: str, year: int = None, is_tv: bool = False) -> Optional[str]:
        """查询豆瓣获取中文标题"""
        try:
            # 构建搜索URL
            search_type = 'tv' if is_tv else 'movie'
            query = f"{title} {year}" if year else title
            url = f"https://movie.douban.com/j/subject_suggest?q={urllib.parse.quote(query)}"
            
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Cookie': self.douban_cookie,
                'Referer': 'https://movie.douban.com/'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 解析结果
            if data and len(data) > 0:
                # 优先匹配年份
                if year:
                    for item in data:
                        if str(year) in item.get('year', ''):
                            return item.get('title')
                
                # 返回第一个结果
                return data[0].get('title')
            
        except Exception as e:
            print(f"豆瓣查询失败: {e}")
        
        return None
    
    def _query_tmdb(self, title: str, year: int = None, is_tv: bool = False) -> Optional[str]:
        """查询 TMDB 获取中文标题"""
        try:
            # 构建搜索URL
            endpoint = 'tv' if is_tv else 'movie'
            params = {
                'api_key': self.tmdb_api_key,
                'query': title,
                'language': 'zh-CN',  # 请求中文结果
            }
            if year:
                params['year'] = year
            
            url = f"https://api.themoviedb.org/3/search/{endpoint}?{urllib.parse.urlencode(params)}"
            
            # 发送请求
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 解析结果
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                
                # 获取中文标题
                chinese_title = result.get('title') if not is_tv else result.get('name')
                
                # 如果 TMDB 返回的还是英文，尝试获取原始标题
                if not self._is_chinese(chinese_title):
                    chinese_title = result.get('original_title') if not is_tv else result.get('original_name')
                
                return chinese_title
            
        except Exception as e:
            print(f"TMDB 查询失败: {e}")
        
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


class IntegratedRecognizer:
    """集成识别器 - 高级识别 + 中文标题解析"""
    
    def __init__(self, tmdb_api_key: str = None, douban_cookie: str = None):
        from core.advanced_recognizer import get_advanced_recognizer
        
        self.advanced_recognizer = get_advanced_recognizer()
        self.title_resolver = ChineseTitleResolver(tmdb_api_key, douban_cookie)
    
    def recognize_with_chinese_title(self, filename: str, convert_chinese_number: bool = True) -> Dict[str, Any]:
        """
        识别文件并获取中文标题（v2.4.0 增强）
        
        Args:
            filename: 文件名
            convert_chinese_number: 是否转换中文数字（v2.4.0 新增）
            
        Returns:
            识别结果（包含中文标题）
        """
        # 0. 转换中文数字（v2.4.0 新增）
        processed_filename = filename
        if convert_chinese_number:
            try:
                from core.chinese_number import convert_chinese_number
                processed_filename = convert_chinese_number(filename, use_cn2an=True)
                if processed_filename != filename:
                    print(f"✓ 中文数字转换: {filename} → {processed_filename}")
            except Exception as e:
                print(f"⚠ 中文数字转换失败: {e}")
        
        # 1. 使用高级识别器提取信息
        info = self.advanced_recognizer.recognize(processed_filename)
        
        # 2. 如果标题不是中文，查询中文标题
        if info['title'] and not self._is_chinese(info['title']):
            print(f"检测到英文标题: {info['title']}, 正在查询中文标题...")
            
            chinese_title = self.title_resolver.resolve(
                info['title'],
                info['year'],
                info['is_tv']
            )
            
            if chinese_title:
                print(f"✓ 找到中文标题: {chinese_title}")
                info['original_title'] = info['title']  # 保存原始英文标题
                info['title'] = chinese_title  # 替换为中文标题
            else:
                print(f"✗ 未找到中文标题，保留英文: {info['title']}")
        
        return info
    
    def _is_chinese(self, text: str) -> bool:
        """检查文本是否包含中文"""
        if not text:
            return False
        return bool(re.search(r'[\u4e00-\u9fff]', text))


# 全局实例
_integrated_recognizer = None


def get_integrated_recognizer(tmdb_api_key: str = None, douban_cookie: str = None) -> IntegratedRecognizer:
    """获取集成识别器实例"""
    global _integrated_recognizer
    if _integrated_recognizer is None:
        _integrated_recognizer = IntegratedRecognizer(tmdb_api_key, douban_cookie)
    return _integrated_recognizer


# 便捷函数
def recognize_with_chinese_title(filename: str, tmdb_api_key: str = None, douban_cookie: str = None) -> Dict[str, Any]:
    """识别文件并获取中文标题的便捷函数"""
    recognizer = get_integrated_recognizer(tmdb_api_key, douban_cookie)
    return recognizer.recognize_with_chinese_title(filename)
