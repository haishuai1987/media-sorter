#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文数字转换模块
支持中文数字转阿拉伯数字（可选使用 cn2an 库）
"""

import re
from typing import Optional, Union


# 中文数字映射
CHINESE_DIGITS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000, '万': 10000,
    '〇': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4,
    '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
    '拾': 10, '佰': 100, '仟': 1000, '萬': 10000,
}


class ChineseNumber:
    """中文数字转换器"""
    
    def __init__(self, use_cn2an: bool = True):
        """
        初始化转换器
        
        Args:
            use_cn2an: 是否使用 cn2an 库（如果可用）
        """
        self.use_cn2an = use_cn2an
        self.cn2an_available = False
        
        if use_cn2an:
            try:
                import cn2an
                self.cn2an = cn2an
                self.cn2an_available = True
                print("✓ cn2an 库已加载")
            except ImportError:
                print("ℹ cn2an 库未安装，使用内置转换器")
    
    def convert(self, text: str) -> str:
        """
        转换文本中的中文数字为阿拉伯数字
        
        Args:
            text: 输入文本
            
        Returns:
            转换后的文本
        """
        if not text:
            return text
        
        # 优先使用 cn2an
        if self.cn2an_available:
            return self._convert_with_cn2an(text)
        else:
            return self._convert_builtin(text)
    
    def _convert_with_cn2an(self, text: str) -> str:
        """使用 cn2an 库转换"""
        try:
            # 转换所有中文数字
            result = self.cn2an.transform(text, "cn2an")
            return result
        except Exception as e:
            print(f"⚠ cn2an 转换失败: {e}，使用内置转换器")
            return self._convert_builtin(text)
    
    def _convert_builtin(self, text: str) -> str:
        """使用内置转换器"""
        result = text
        
        # 常见模式
        patterns = [
            # 第X季/集/部
            (r'第([一二三四五六七八九十]+)季', self._replace_season),
            (r'第([一二三四五六七八九十]+)集', self._replace_episode),
            (r'第([一二三四五六七八九十]+)部', self._replace_part),
            
            # 单独的数字
            (r'([一二三四五六七八九十百千万]+)', self._replace_number),
        ]
        
        for pattern, replacer in patterns:
            result = re.sub(pattern, replacer, result)
        
        return result
    
    def _replace_season(self, match) -> str:
        """替换季数"""
        chinese = match.group(1)
        number = self._chinese_to_number(chinese)
        return f'第{number}季' if number else match.group(0)
    
    def _replace_episode(self, match) -> str:
        """替换集数"""
        chinese = match.group(1)
        number = self._chinese_to_number(chinese)
        return f'第{number}集' if number else match.group(0)
    
    def _replace_part(self, match) -> str:
        """替换部数"""
        chinese = match.group(1)
        number = self._chinese_to_number(chinese)
        return f'第{number}部' if number else match.group(0)
    
    def _replace_number(self, match) -> str:
        """替换数字"""
        chinese = match.group(1)
        
        # 跳过非数字的中文
        if not any(c in CHINESE_DIGITS for c in chinese):
            return match.group(0)
        
        number = self._chinese_to_number(chinese)
        return str(number) if number else match.group(0)
    
    def _chinese_to_number(self, chinese: str) -> Optional[int]:
        """
        中文数字转阿拉伯数字（简单实现）
        
        Args:
            chinese: 中文数字
            
        Returns:
            阿拉伯数字
        """
        if not chinese:
            return None
        
        try:
            # 简单映射
            simple_map = {
                '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5,
                '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10,
            }
            
            # 直接映射
            if chinese in simple_map:
                return simple_map[chinese]
            
            # 十几
            if chinese.startswith('十'):
                if len(chinese) == 1:
                    return 10
                elif len(chinese) == 2:
                    return 10 + simple_map.get(chinese[1], 0)
            
            # X十
            if len(chinese) == 2 and chinese[1] == '十':
                return simple_map.get(chinese[0], 0) * 10
            
            # X十Y
            if len(chinese) == 3 and chinese[1] == '十':
                tens = simple_map.get(chinese[0], 0) * 10
                ones = simple_map.get(chinese[2], 0)
                return tens + ones
            
            # 复杂情况暂不处理
            return None
            
        except Exception as e:
            print(f"⚠ 转换失败: {chinese} - {e}")
            return None
    
    def convert_season_episode(self, text: str) -> str:
        """
        专门转换季集信息
        
        Args:
            text: 输入文本
            
        Returns:
            转换后的文本
        """
        result = text
        
        # 第X季
        result = re.sub(
            r'第([一二三四五六七八九十]+)季',
            lambda m: f'第{self._chinese_to_number(m.group(1)) or m.group(1)}季',
            result
        )
        
        # 第X集
        result = re.sub(
            r'第([一二三四五六七八九十]+)集',
            lambda m: f'第{self._chinese_to_number(m.group(1)) or m.group(1)}集',
            result
        )
        
        # SXX 格式
        result = re.sub(
            r'S([一二三四五六七八九十]+)',
            lambda m: f'S{self._chinese_to_number(m.group(1)) or m.group(1):02d}',
            result,
            flags=re.IGNORECASE
        )
        
        # EXX 格式
        result = re.sub(
            r'E([一二三四五六七八九十]+)',
            lambda m: f'E{self._chinese_to_number(m.group(1)) or m.group(1):02d}',
            result,
            flags=re.IGNORECASE
        )
        
        return result


# 全局实例
_chinese_number = None


def get_chinese_number(use_cn2an: bool = True) -> ChineseNumber:
    """获取中文数字转换器实例（单例模式）"""
    global _chinese_number
    if _chinese_number is None:
        _chinese_number = ChineseNumber(use_cn2an=use_cn2an)
    return _chinese_number


def convert_chinese_number(text: str, use_cn2an: bool = True) -> str:
    """
    快捷方法：转换文本中的中文数字
    
    Args:
        text: 输入文本
        use_cn2an: 是否使用 cn2an 库
        
    Returns:
        转换后的文本
    """
    converter = get_chinese_number(use_cn2an=use_cn2an)
    return converter.convert(text)


if __name__ == '__main__':
    # 测试中文数字转换
    print("测试中文数字转换")
    print("="*60)
    
    converter = ChineseNumber(use_cn2an=False)  # 使用内置转换器
    
    test_cases = [
        "权力的游戏第一季",
        "权力的游戏第二季",
        "权力的游戏第十季",
        "权力的游戏第十五季",
        "流浪地球二",
        "复仇者联盟四",
        "第一集",
        "第二十集",
        "S一E五",
    ]
    
    print("\n内置转换器测试:")
    print("-" * 60)
    for text in test_cases:
        result = converter.convert(text)
        if result != text:
            print(f"原始: {text}")
            print(f"结果: {result}")
            print()
    
    # 测试 cn2an（如果可用）
    print("\ncn2an 转换器测试:")
    print("-" * 60)
    
    converter2 = ChineseNumber(use_cn2an=True)
    
    if converter2.cn2an_available:
        for text in test_cases:
            result = converter2.convert(text)
            if result != text:
                print(f"原始: {text}")
                print(f"结果: {result}")
                print()
    else:
        print("cn2an 库未安装，跳过测试")
    
    # 测试季集转换
    print("\n季集转换测试:")
    print("-" * 60)
    
    season_tests = [
        "权力的游戏.第一季.第五集.1080p.mkv",
        "权力的游戏.S二E十.1080p.mkv",
    ]
    
    for text in season_tests:
        result = converter.convert_season_episode(text)
        print(f"原始: {text}")
        print(f"结果: {result}")
        print()
