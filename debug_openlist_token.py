#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenList Token 调试脚本
测试不同的API端点和请求格式
"""

import requests
import json

# Token配置
ACCESS_TOKEN = 'bfii8.f52fd0d4ed1e855a5a28cb42153c54f3.3d44322284a86508e0e02c850a5d66081b63b0909c60a16944c6df8ab125995f'
REFRESH_TOKEN = 'bfii8.e6877771dc643d2631e6d75aeb2e1a122ec51715f54652a7aa6f1dd722cb6867.6d78505939f0423b83054518061da75dcb3e9544cf5b2658fe3a62f638605262'

# 可能的API端点
API_ENDPOINTS = [
    'https://api.oplist.org.cn/115cloud',
    'https://api.oplist.org.cn/api/v1',
    'https://api.oplist.org.cn',
    'https://api.oplist.org/115cloud',
    'https://api.oplist.org/api/v1',
]

# 可能的用户信息端点
USER_PATHS = [
    '/user',
    '/userinfo',
    '/account',
    '/me',
    '/info',
]

# 可能的文件列表端点
FILE_PATHS = [
    '/files',
    '/list',
    '/file/list',
]


def test_endpoint(base_url, path, method='GET', params=None):
    """测试API端点"""
    url = f"{base_url}{path}"
    
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'MediaSorter/1.0'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=params, timeout=10)
        
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"响应体: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return response.status_code, data
        except:
            print(f"响应体(文本): {response.text[:500]}")
            return response.status_code, response.text
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"错误: {str(e)}")
        return None, str(e)


def main():
    print("OpenList Token 调试工具")
    print("="*60)
    print(f"Access Token: {ACCESS_TOKEN[:50]}...")
    print(f"Refresh Token: {REFRESH_TOKEN[:50]}...")
    print()
    
    # 测试1: 尝试不同的用户信息端点
    print("\n" + "="*60)
    print("测试1: 用户信息端点")
    print("="*60)
    
    for base_url in API_ENDPOINTS:
        for path in USER_PATHS:
            status, data = test_endpoint(base_url, path)
            if status == 200:
                print(f"\n✅ 找到有效端点: {base_url}{path}")
                break
        if status == 200:
            break
    
    # 测试2: 尝试不同的文件列表端点
    print("\n" + "="*60)
    print("测试2: 文件列表端点")
    print("="*60)
    
    for base_url in API_ENDPOINTS:
        for path in FILE_PATHS:
            # 尝试不同的参数格式
            param_sets = [
                {'cid': '0'},
                {'folder_id': '0'},
                {'parent_id': '0'},
                {'id': '0'},
            ]
            
            for params in param_sets:
                status, data = test_endpoint(base_url, path, params=params)
                if status == 200:
                    print(f"\n✅ 找到有效端点: {base_url}{path}")
                    print(f"   参数: {params}")
                    break
            if status == 200:
                break
        if status == 200:
            break
    
    # 测试3: 直接测试回调地址的基础URL
    print("\n" + "="*60)
    print("测试3: 基于回调地址的推测")
    print("="*60)
    print("回调地址: https://api.oplist.org.cn/115cloud/callback")
    print("推测基础URL: https://api.oplist.org.cn/115cloud")
    
    # 尝试常见的API路径
    common_paths = [
        '',  # 根路径
        '/user',
        '/userinfo',
        '/files',
        '/file/list',
    ]
    
    for path in common_paths:
        test_endpoint('https://api.oplist.org.cn/115cloud', path)


if __name__ == '__main__':
    main()
