#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过OpenList获取115网盘Cookie
基于OpenList API文档: https://github.com/OpenListTeam/OpenList-APIPages
"""

import requests
import json
import base64
import time

# OpenList配置
ACCESS_TOKEN = 'bfieb.5f299b2abec5e874fb7615b0561cebad.4700987d56fc9fc290d9024098f4fd6e554c9d1ef9165dd592405a231c119932'
REFRESH_TOKEN = 'bfieb.f06e132cd855211227c5f6fdc0242b2bb96949f878c531f0f5ce3dfa09d55b31.bfdd2e18de5384e7ff358e5c6d575518b4061eeb9f0b23e4064b13b04067198b'

# OpenList API地址（国内）
BASE_URL = 'https://api-cn.oplist.org'


def get_115_cookie_from_tokens():
    """
    从OpenList的Access Token中提取115网盘Cookie
    
    根据OpenList的设计，Access Token本身可能就包含了115的认证信息
    """
    print("=" * 60)
    print("方法1: 尝试从Token中提取Cookie")
    print("=" * 60)
    
    # OpenList的Token可能是Base64编码的JSON
    try:
        # 尝试解码Access Token
        token_parts = ACCESS_TOKEN.split('.')
        for i, part in enumerate(token_parts):
            print(f"\nToken部分 {i+1}:")
            try:
                # 添加padding
                padded = part + '=' * (4 - len(part) % 4)
                decoded = base64.b64decode(padded)
                print(f"  解码成功: {decoded[:100]}...")
                
                # 尝试解析为JSON
                try:
                    data = json.loads(decoded)
                    print(f"  JSON数据: {data}")
                    
                    # 查找Cookie相关字段
                    if 'cookie' in data:
                        print(f"\n✅ 找到Cookie: {data['cookie']}")
                        return data['cookie']
                except:
                    pass
            except Exception as e:
                print(f"  无法解码: {e}")
    except Exception as e:
        print(f"解析Token失败: {e}")
    
    return None


def check_openlist_storage_info():
    """
    检查OpenList存储信息
    可能可以获取到115网盘的Cookie
    """
    print("\n" + "=" * 60)
    print("方法2: 查询OpenList存储信息")
    print("=" * 60)
    
    # 可能的API端点
    endpoints = [
        f'{BASE_URL}/115cloud/info',
        f'{BASE_URL}/115cloud/storage',
        f'{BASE_URL}/115cloud/user',
        f'{BASE_URL}/storage/115cloud',
    ]
    
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }
    
    for url in endpoints:
        try:
            print(f"\n尝试: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功!")
                print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # 查找Cookie
                if 'cookie' in str(data):
                    print(f"\n✅ 找到Cookie相关信息")
                    return data
            else:
                print(f"  响应: {response.text[:200]}")
        except Exception as e:
            print(f"  异常: {e}")
    
    return None


def use_openlist_to_get_qrcode():
    """
    使用OpenList生成115网盘登录二维码
    这是OpenList的主要用途
    """
    print("\n" + "=" * 60)
    print("方法3: 使用OpenList生成登录二维码")
    print("=" * 60)
    
    url = f'{BASE_URL}/115cloud/requests'
    
    # 根据文档，需要提供这些参数
    params = {
        'server_use': 'true',  # 使用OpenList提供的AppID和Key
        'driver_txt': '115cloud_go',  # 115云盘驱动类型
    }
    
    try:
        print(f"\n请求: {url}")
        print(f"参数: {params}")
        
        response = requests.post(url, json=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功!")
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 应该返回登录链接
            if 'text' in data:
                login_url = data['text']
                print(f"\n📱 登录链接: {login_url}")
                print(f"\n请在浏览器中打开此链接并扫码登录")
                print(f"登录后会跳转到回调地址，从URL中获取code参数")
                return login_url
        else:
            print(f"失败: {response.text}")
    except Exception as e:
        print(f"异常: {e}")
    
    return None


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("通过OpenList获取115网盘Cookie")
    print("=" * 60)
    print()
    
    # 方法1: 从Token中提取
    cookie = get_115_cookie_from_tokens()
    if cookie:
        print("\n" + "=" * 60)
        print("✅ 成功获取Cookie!")
        print("=" * 60)
        print(f"\nCookie: {cookie}")
        print("\n请将此Cookie复制到系统设置中")
        return
    
    # 方法2: 查询存储信息
    info = check_openlist_storage_info()
    if info and 'cookie' in str(info):
        print("\n" + "=" * 60)
        print("✅ 找到Cookie信息!")
        print("=" * 60)
        print(f"\n{json.dumps(info, indent=2, ensure_ascii=False)}")
        return
    
    # 方法3: 生成登录二维码
    login_url = use_openlist_to_get_qrcode()
    if login_url:
        print("\n" + "=" * 60)
        print("📱 请扫码登录")
        print("=" * 60)
        print(f"\n1. 在浏览器中打开: {login_url}")
        print(f"2. 使用115手机客户端扫码")
        print(f"3. 登录后会跳转，从URL中获取code参数")
        print(f"4. 使用code参数调用回调接口获取Cookie")
        return
    
    # 所有方法都失败
    print("\n" + "=" * 60)
    print("⚠️  无法通过OpenList获取Cookie")
    print("=" * 60)
    print("\n建议：")
    print("1. 检查Access Token是否有效")
    print("2. 或者直接从浏览器手动获取Cookie")
    print("3. 或者从MoviePilot复制Cookie")


if __name__ == '__main__':
    main()
