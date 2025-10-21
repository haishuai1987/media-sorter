#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义识别词测试 - v1.3.0
"""

import json
import os
import sys

# 测试配置
TEST_WORDS = {
    "custom_words": [
        {
            "type": "block",
            "pattern": "大神版",
            "enabled": True
        },
        {
            "type": "replace",
            "old": "密室大逃脱大神版",
            "new": "密室大逃脱 大神版",
            "enabled": True
        },
        {
            "type": "block",
            "pattern": "特别篇",
            "enabled": True
        }
    ]
}

# 测试用例
test_cases = [
    {
        'input': '密室大逃脱大神版.S07E01',
        'expected': '密室大逃脱 .S07E01',  # 先替换，再屏蔽
        'description': '替换词 + 屏蔽词'
    },
    {
        'input': '某剧大神版',
        'expected': '某剧',
        'description': '屏蔽词'
    },
    {
        'input': '某剧特别篇',
        'expected': '某剧',
        'description': '屏蔽词'
    },
    {
        'input': '正常标题',
        'expected': '正常标题',
        'description': '无匹配'
    }
]

def test_custom_words():
    """测试自定义识别词"""
    print("=" * 60)
    print("自定义识别词测试 - v1.3.0")
    print("=" * 60)
    print()
    
    # 模拟识别词处理
    def apply_words(title, words):
        for word in words:
            if not word.get('enabled', True):
                continue
            
            word_type = word.get('type', '')
            
            if word_type == 'block':
                pattern = word.get('pattern', '')
                if pattern:
                    title = title.replace(pattern, '')
            
            elif word_type == 'replace':
                old = word.get('old', '')
                new = word.get('new', '')
                if old:
                    title = title.replace(old, new)
        
        return title.strip()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_title = test['input']
        expected = test['expected']
        description = test['description']
        
        result = apply_words(input_title, TEST_WORDS['custom_words'])
        
        if result == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"测试 {i}: {description}")
        print(f"  输入:   {input_title}")
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
    success = test_custom_words()
    sys.exit(0 if success else 1)
