#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
副标题解析测试 - v1.4.0
"""

import sys

try:
    import cn2an
    CN2AN_AVAILABLE = True
except ImportError:
    CN2AN_AVAILABLE = False
    print("错误: cn2an 未安装")
    print("请运行: pip install cn2an")
    sys.exit(1)

import re

# 测试用例
test_cases = [
    {
        'input': '第七季',
        'expected': {'season': 7},
        'description': '第X季（中文数字）'
    },
    {
        'input': '第3季',
        'expected': {'season': 3},
        'description': '第X季（阿拉伯数字）'
    },
    {
        'input': '全12集',
        'expected': {'total_episodes': 12},
        'description': '全X集（阿拉伯数字）'
    },
    {
        'input': '全十二集',
        'expected': {'total_episodes': 12},
        'description': '全X集（中文数字）'
    },
    {
        'input': '第二季 全10集',
        'expected': {'season': 2, 'total_episodes': 10},
        'description': '组合'
    },
    {
        'input': '正常标题',
        'expected': {},
        'description': '无匹配'
    }
]

def parse_subtitle(subtitle):
    """解析副标题"""
    result = {}
    
    # 第X季
    season_re = re.compile(r'第\s*([0-9一二三四五六七八九十]+)\s*季', re.IGNORECASE)
    season_match = season_re.search(subtitle)
    if season_match:
        season_str = season_match.group(1)
        try:
            result['season'] = cn2an.cn2an(season_str, mode='smart')
        except:
            pass
    
    # 全X集
    episode_re = re.compile(r'全\s*([0-9一二三四五六七八九十百零]+)\s*集', re.IGNORECASE)
    episode_match = episode_re.search(subtitle)
    if episode_match:
        episode_str = episode_match.group(1)
        try:
            result['total_episodes'] = cn2an.cn2an(episode_str, mode='smart')
        except:
            pass
    
    return result

def test_subtitle_parser():
    """测试副标题解析"""
    print("=" * 60)
    print("副标题解析测试 - v1.4.0")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_subtitle = test['input']
        expected = test['expected']
        description = test['description']
        
        result = parse_subtitle(input_subtitle)
        
        if result == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"测试 {i}: {description}")
        print(f"  输入:   {input_subtitle}")
        print(f"  期望:   {expected}")
        print(f"  实际:   {result}")
        print(f"  状态:   {status}")
        print()
    
    print("=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print(f"通过率: {passed / len(test_cases) * 100:.1f}%")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = test_subtitle_parser()
    sys.exit(0 if success else 1)
