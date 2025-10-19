#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单获取OpenList Apifox文档
"""

import requests
import json
import re

url = "https://openlist.apifox.cn/"

try:
    print(f"正在访问: {url}")
    response = requests.get(url, timeout=10)
    
    print(f"状态码: {response.status_code}")
    print(f"内容类型: {response.headers.get('content-type')}")
    print(f"内容长度: {len(response.text)}")
    
    # 保存HTML
    with open('openlist_apifox.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("\n完整HTML已保存到: openlist_apifox.html")
    
    # 尝试提取关键信息
    print("\n" + "="*60)
    print("查找API相关信息...")
    print("="*60)
    
    # 查找API端点
    api_patterns = [
        r'https?://[^\s<>"]+/api/[^\s<>"]+',
        r'https?://api\.[^\s<>"]+',
        r'/api/v\d+/[^\s<>"]+',
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, response.text)
        if matches:
            print(f"\n找到API端点 ({pattern}):")
            for match in set(matches[:10]):
                print(f"  - {match}")
    
    # 查找Cookie相关
    if 'cookie' in response.text.lower():
        print("\n找到Cookie相关内容")
        cookie_lines = [line for line in response.text.split('\n') if 'cookie' in line.lower()]
        for line in cookie_lines[:5]:
            print(f"  {line.strip()[:100]}")
    
    # 查找文档链接
    doc_pattern = r'https?://[^\s<>"]*doc[^\s<>"]*'
    doc_matches = re.findall(doc_pattern, response.text)
    if doc_matches:
        print("\n找到文档链接:")
        for match in set(doc_matches[:10]):
            print(f"  - {match}")
    
    print("\n" + "="*60)
    print("请打开 openlist_apifox.html 查看完整内容")
    print("或在浏览器中访问: https://openlist.apifox.cn/")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
