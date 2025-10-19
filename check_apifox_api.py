#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Apifox API文档
"""

import requests

# 根据HTML中的信息，尝试访问具体的API文档
api_urls = [
    "https://openlist.apifox.cn/api-128101241",  # token获取
    "https://openlist.apifox.cn/api-128101246",  # 列出文件目录
    "https://openlist.apifox.cn/api-128101245",  # 获取当前用户信息
]

for url in api_urls:
    print(f"\n{'='*60}")
    print(f"访问: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        # 查找关键信息
        if 'cookie' in response.text.lower():
            print("✅ 找到Cookie相关内容")
        
        if 'authorization' in response.text.lower():
            print("✅ 找到Authorization相关内容")
        
        if 'bearer' in response.text.lower():
            print("✅ 找到Bearer Token相关内容")
        
        # 查找API端点
        import re
        endpoints = re.findall(r'https?://[^\s<>"]+/api/[^\s<>"]+', response.text)
        if endpoints:
            print(f"\n找到API端点:")
            for ep in set(endpoints[:5]):
                print(f"  - {ep}")
        
    except Exception as e:
        print(f"错误: {e}")

print("\n" + "="*60)
print("建议：直接在浏览器中打开以下链接查看完整文档")
print("="*60)
print("https://openlist.apifox.cn/")
print("\n重点查看：")
print("1. token获取 - https://openlist.apifox.cn/api-128101241")
print("2. 列出文件目录 - https://openlist.apifox.cn/api-128101246")
print("3. 获取当前用户信息 - https://openlist.apifox.cn/api-128101245")
