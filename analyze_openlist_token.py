#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析OpenList Token的真实作用
"""

import requests
import json
import base64

# Token
ACCESS_TOKEN = 'bfii8.f52fd0d4ed1e855a5a28cb42153c54f3.3d44322284a86508e0e02c850a5d66081b63b0909c60a16944c6df8ab125995f'
REFRESH_TOKEN = 'bfii8.e6877771dc643d2631e6d75aeb2e1a122ec51715f54652a7aa6f1dd722cb6867.6d78505939f0423b83054518061da75dcb3e9544cf5b2658fe3a62f638605262'

print("="*60)
print("OpenList Token 分析")
print("="*60)

# 1. 分析Token结构
print("\n1. Token结构分析")
print("-"*60)

access_parts = ACCESS_TOKEN.split('.')
refresh_parts = REFRESH_TOKEN.split('.')

print(f"Access Token 部分数: {len(access_parts)}")
print(f"  - 前缀: {access_parts[0]}")
print(f"  - 部分1长度: {len(access_parts[1])}")
print(f"  - 部分2长度: {len(access_parts[2])}")

print(f"\nRefresh Token 部分数: {len(refresh_parts)}")
print(f"  - 前缀: {refresh_parts[0]}")
print(f"  - 部分1长度: {len(refresh_parts[1])}")
print(f"  - 部分2长度: {len(refresh_parts[2])}")

# 2. 尝试Base64解码
print("\n2. 尝试解码Token内容")
print("-"*60)

def try_decode(part, name):
    """尝试各种解码方式"""
    print(f"\n{name}:")
    
    # 尝试Base64
    try:
        decoded = base64.b64decode(part + '==')  # 添加padding
        print(f"  Base64解码: {decoded[:100]}")
    except:
        print(f"  Base64解码: 失败")
    
    # 尝试Base64 URL-safe
    try:
        decoded = base64.urlsafe_b64decode(part + '==')
        print(f"  Base64 URL-safe: {decoded[:100]}")
    except:
        print(f"  Base64 URL-safe: 失败")
    
    # 尝试Hex
    try:
        decoded = bytes.fromhex(part)
        print(f"  Hex解码: {decoded[:100]}")
    except:
        print(f"  Hex解码: 失败")

try_decode(access_parts[1], "Access Token 部分1")
try_decode(access_parts[2], "Access Token 部分2")

# 3. 测试Token是否可以用于OpenList的刷新接口
print("\n3. 测试Token刷新功能")
print("-"*60)

refresh_url = 'https://api.oplist.org.cn/115cloud/renewapi'
params = {
    'apps_types': '115cloud_go',
    'refresh_ui': REFRESH_TOKEN,
    'server_use': 'true'
}

try:
    response = requests.get(refresh_url, params=params, timeout=10)
    print(f"刷新接口状态码: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print(f"响应(文本): {response.text[:500]}")
    else:
        print(f"响应: {response.text[:200]}")
except Exception as e:
    print(f"请求失败: {e}")

# 4. 分析Token的可能用途
print("\n4. Token用途总结")
print("-"*60)
print("""
根据分析，OpenList的Token可能有以下用途：

1. **Alist等工具的内部使用**
   - 这些工具有自己的115驱动实现
   - Token可能包含了某些认证信息
   - 工具内部会将Token转换为115 API调用

2. **可能包含的信息**
   - 用户ID
   - 会话标识
   - 签名信息
   - 过期时间

3. **不能直接用于115 API**
   - 115官方API不认这种Token格式
   - 需要通过中间层（如Alist）转换

4. **可能的工作方式**
   Token → 第三方工具 → 转换为Cookie/签名 → 调用115 API

5. **对我们的意义**
   - ❌ 不能直接用于我们的应用
   - ❌ 需要实现类似Alist的转换逻辑（太复杂）
   - ✅ 但可以利用OAuth登录流程获取Cookie
""")

# 5. Cookie vs Token 对比
print("\n5. Cookie vs Token 对比")
print("-"*60)
print("""
┌─────────────────┬──────────────────┬──────────────────┐
│     特性        │      Cookie      │   OpenList Token │
├─────────────────┼──────────────────┼──────────────────┤
│ 115官方支持     │        ✅        │        ❌        │
│ 直接调用API     │        ✅        │        ❌        │
│ 获取难度        │       简单       │      需OAuth     │
│ 稳定性          │       很好       │      依赖工具    │
│ 功能完整性      │       完整       │      受限        │
│ 推荐使用        │        ✅        │        ❌        │
└─────────────────┴──────────────────┴──────────────────┘
""")

print("\n结论：")
print("="*60)
print("""
OpenList Token的作用：
1. 主要给Alist、CloudDrive等工具使用
2. 这些工具内部有115的API实现
3. Token可能包含认证信息，但不是115官方格式
4. 对我们的应用来说，Cookie仍然是最佳选择

建议：
- 使用OpenList的OAuth登录流程（避免二维码问题）
- 但最终目标是获取Cookie（不是Token）
- Cookie可以直接用于115 API调用
""")
