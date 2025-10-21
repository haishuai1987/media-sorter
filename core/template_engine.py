#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板引擎
支持灵活的文件命名模板
"""

import re
from typing import Dict, Any, Optional


class TemplateEngine:
    """简单的模板引擎（类似 Jinja2，但无需外部依赖）"""
    
    def __init__(self):
        # 预定义模板
        self.templates = {
            # 电影模板
            'movie_default': '{title} ({year})/{title} ({year}) [{resolution}-{source}].{ext}',
            'movie_simple': '{title} ({year})/{title} ({year}).{ext}',
            'movie_detailed': '{title} ({year})/{title} ({year}) [{resolution} {video_codec} {audio_codec} {source}].{ext}',
            'movie_quality': '{title} ({year})/{title} ({year}) [{quality}].{ext}',
            
            # 电视剧模板
            'tv_default': '{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d} [{resolution}-{source}].{ext}',
            'tv_simple': '{title}/S{season:02d}/{title} - S{season:02d}E{episode:02d}.{ext}',
            'tv_detailed': '{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d} [{resolution} {video_codec} {audio_codec} {source}].{ext}',
            'tv_quality': '{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d} [{quality}].{ext}',
            
            # NAS-Tools 风格
            'nas_movie': '{title} ({year})/{title} ({year}) [{resolution} {video_codec} {audio_codec}].{ext}',
            'nas_tv': '{title}/Season {season:02d}/{title} S{season:02d}E{episode:02d} [{resolution} {video_codec} {audio_codec}].{ext}',
            
            # MoviePilot 风格
            'mp_movie': '{title} ({year})/{title} ({year}) [{quality}].{ext}',
            'mp_tv': '{title}/Season {season:02d}/{title} S{season:02d}E{episode:02d} [{quality}].{ext}',
            
            # Plex 风格
            'plex_movie': '{title} ({year})/{title} ({year}).{ext}',
            'plex_tv': '{title}/Season {season:02d}/{title} - s{season:02d}e{episode:02d}.{ext}',
            
            # Jellyfin 风格
            'jellyfin_movie': '{title} ({year})/{title} ({year}) - {quality}.{ext}',
            'jellyfin_tv': '{title}/Season {season:02d}/{title} S{season:02d}E{episode:02d}.{ext}',
        }
        
        # 用户自定义模板
        self.custom_templates = {}
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            context: 上下文数据
            
        Returns:
            渲染后的字符串
        """
        # 获取模板
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 预处理上下文
        context = self._prepare_context(context)
        
        # 渲染模板
        result = self._render_template(template, context)
        
        # 清理结果
        result = self._clean_result(result)
        
        return result
    
    def get_template(self, name: str) -> Optional[str]:
        """获取模板"""
        # 优先使用自定义模板
        if name in self.custom_templates:
            return self.custom_templates[name]
        
        # 使用预定义模板
        return self.templates.get(name)
    
    def add_template(self, name: str, template: str):
        """添加自定义模板"""
        self.custom_templates[name] = template
    
    def list_templates(self) -> Dict[str, str]:
        """列出所有模板"""
        all_templates = self.templates.copy()
        all_templates.update(self.custom_templates)
        return all_templates
    
    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """预处理上下文数据"""
        prepared = context.copy()
        
        # 确保必要的字段存在
        defaults = {
            'title': 'Unknown',
            'year': '',
            'season': 0,
            'episode': 0,
            'resolution': '',
            'video_codec': '',
            'audio_codec': '',
            'source': '',
            'quality': '',
            'ext': 'mkv',
        }
        
        for key, default_value in defaults.items():
            if key not in prepared or prepared[key] is None:
                prepared[key] = default_value
        
        # 生成 quality 字段（如果不存在）
        if not prepared['quality']:
            quality_parts = []
            if prepared['resolution']:
                quality_parts.append(str(prepared['resolution']))
            if prepared['source']:
                quality_parts.append(str(prepared['source']))
            prepared['quality'] = '-'.join(quality_parts) if quality_parts else 'Unknown'
        
        return prepared
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染模板（支持格式化）"""
        result = template
        
        # 处理格式化占位符 {key:format}
        # 例如: {season:02d} -> 01
        pattern = r'\{(\w+)(?::([^}]+))?\}'
        
        def replace_placeholder(match):
            key = match.group(1)
            format_spec = match.group(2)
            
            if key not in context:
                return ''
            
            value = context[key]
            
            # 如果有格式化规范
            if format_spec:
                try:
                    # 处理数字格式化
                    if 'd' in format_spec:  # 整数格式
                        value = int(value) if value else 0
                        return f'{value:{format_spec}}'
                    elif 'f' in format_spec:  # 浮点数格式
                        value = float(value) if value else 0.0
                        return f'{value:{format_spec}}'
                    else:
                        return f'{value:{format_spec}}'
                except (ValueError, TypeError):
                    return str(value)
            
            return str(value)
        
        result = re.sub(pattern, replace_placeholder, result)
        
        return result
    
    def _clean_result(self, text: str) -> str:
        """清理渲染结果"""
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除空的括号和方括号
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)
        
        # 移除多余的分隔符
        text = re.sub(r'[-_\s]+\.', '.', text)  # 移除扩展名前的分隔符
        text = re.sub(r'[-_]{2,}', '-', text)   # 多个连字符合并
        text = re.sub(r'\s{2,}', ' ', text)     # 多个空格合并
        
        # 清理路径分隔符
        text = re.sub(r'/+', '/', text)
        
        # 移除首尾空格
        text = text.strip()
        
        return text
    
    def validate_template(self, template: str) -> tuple[bool, Optional[str]]:
        """
        验证模板是否有效
        
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查括号是否匹配
            if template.count('{') != template.count('}'):
                return False, "括号不匹配"
            
            # 检查占位符是否有效
            pattern = r'\{(\w+)(?::([^}]+))?\}'
            matches = re.findall(pattern, template)
            
            valid_keys = {
                'title', 'year', 'season', 'episode',
                'resolution', 'video_codec', 'audio_codec',
                'source', 'quality', 'ext', 'hdr',
                'language', 'subtitle', 'release_group'
            }
            
            for key, format_spec in matches:
                if key not in valid_keys:
                    return False, f"无效的占位符: {key}"
            
            # 尝试渲染测试
            test_context = {
                'title': 'Test',
                'year': 2023,
                'season': 1,
                'episode': 1,
                'resolution': '1080p',
                'video_codec': 'H264',
                'audio_codec': 'AAC',
                'source': 'WEB-DL',
                'quality': '1080p-WEB-DL',
                'ext': 'mkv',
            }
            self._render_template(template, test_context)
            
            return True, None
            
        except Exception as e:
            return False, str(e)


# 全局实例
_template_engine = None


def get_template_engine() -> TemplateEngine:
    """获取模板引擎实例（单例）"""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


# 便捷函数
def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """渲染模板的便捷函数"""
    engine = get_template_engine()
    return engine.render(template_name, context)


def add_custom_template(name: str, template: str):
    """添加自定义模板的便捷函数"""
    engine = get_template_engine()
    engine.add_template(name, template)
