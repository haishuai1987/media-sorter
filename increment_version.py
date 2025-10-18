#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本号自动递增脚本
用于在上传到GitHub前自动递增版本号
"""

import os
import sys

VERSION_FILE = 'version.txt'

def parse_version(version_str):
    """解析版本号字符串为元组 (major, minor, patch)"""
    try:
        # 移除 'v' 前缀
        version_str = version_str.lstrip('v')
        parts = version_str.split('.')
        if len(parts) == 3:
            return tuple(int(p) for p in parts)
    except:
        pass
    return (1, 0, 0)

def increment_version(version_str, level='patch'):
    """递增版本号
    level: 'major', 'minor', 'patch'
    """
    major, minor, patch = parse_version(version_str)
    
    if level == 'major':
        major += 1
        minor = 0
        patch = 0
    elif level == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"v{major}.{minor}.{patch}"

def main():
    # 检查version.txt是否存在
    if not os.path.exists(VERSION_FILE):
        print(f"错误: {VERSION_FILE} 不存在")
        sys.exit(1)
    
    # 读取当前版本
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        current_version = f.read().strip()
    
    # 获取递增级别（默认patch）
    level = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    
    # 递增版本号
    new_version = increment_version(current_version, level)
    
    # 保存新版本号
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(new_version)
    
    print(f"版本号已更新: {current_version} -> {new_version}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
