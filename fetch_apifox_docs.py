#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取OpenList Apifox文档
"""

import requests
from bs4 import BeautifulSoup

url = "https://openlist.apifox.cn/"

try:
    print(f"正在访问: {url}")
    response = requests.get(url, timeout=10)
    
    print(f"状态码: {response.status_code}")
    print(f"内容长度: {len(response.text)}")
    print("\n" + "="*60)
    
    # 解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 获取标题
    title = soup.find('title')
    if title:
        print(f"页面标题: {title.text}")
    
    # 查找API相关信息
    print("\n" + "="*60)
    print("查找API端点信息...")
    print("="*60)
    
    # 查找所有链接
    links = soup.find_all('a', href=True)
    api_links = [link for link in links if 'api' in link.get('href', '').lower() or 'api' in link.text.lower()]
    
    if api_links:
        print(f"\n找到 {len(api_links)} 个API相关链接:")
        for link in api_links[:10]:
            print(f"  - {link.text.strip()}: {link.get('href')}")
    
    # 查找文档内容
    print("\n" + "="*60)
    print("页面主要内容:")
    print("="*60)
    
    # 尝试找到主要内容区域
    main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
    
    if main_content:
        # 提取文本，限制长度
        text = main_content.get_text(separator='\n', strip=True)
        lines = text.split('\n')
        
        # 过滤空行
        lines = [line for line in lines if line.strip()]
        
        # 显示前100行
        for i, line in enumerate(lines[:100], 1):
            if line.strip():
                print(f"{i}. {line[:100]}")
    
    # 保存完整HTML
    with open('openlist_apifox.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("\n" + "="*60)
    print("完整HTML已保存到: openlist_apifox.html")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
