#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试smart-rename 500错误的诊断脚本
"""

import json
import sys

# 模拟一个测试文件
test_file = {
    'name': 'SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb.mkv',
    'path': '/vol1/1000/video/媒体库/电视剧/日番/SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb/SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb.mkv',
    'type': 'media',
    'size': 1000000000
}

# 模拟metadata（查询失败的情况）
metadata = {
    'title': 'SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb',
    'year': 2025,
    'season': 1,
    'episode': None,
    'type': 'tv',
    'videoFormat': '1080p.WEB-DL.H264',
    'audioFormat': 'AAC',
    'releaseGroup': 'ADWeb',
    'category': None,  # 这个可能是问题！
    'originalTitle': 'SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb'
}

print("测试结果构建...")
print(f"metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}")

# 测试构建结果
try:
    result = {
        'oldPath': test_file['path'],
        'oldName': test_file['name'],
        'newPath': '/vol02/1000-1-b23abde7/电视剧/未分类/SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb.mkv',
        'newName': 'SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb.mkv',
        'metadata': metadata,
        'category': metadata.get('category'),  # 可能返回None
        'needsFolder': True
    }
    
    print("\n✓ 结果构建成功:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试JSON序列化
    json_str = json.dumps({'results': [result], 'toDelete': []}, ensure_ascii=False)
    print(f"\n✓ JSON序列化成功，长度: {len(json_str)}")
    
except Exception as e:
    import traceback
    print(f"\n✗ 错误: {e}")
    print(f"堆栈:\n{traceback.format_exc()}")

print("\n" + "="*60)
print("诊断建议：")
print("1. 检查metadata中是否有None值导致后续处理失败")
print("2. 检查category字段是否正确处理")
print("3. 检查路径生成是否有问题")
print("="*60)
