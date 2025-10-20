#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞牛OS文件夹访问
用于诊断文件夹浏览问题
"""

import os
import sys

def test_folder_access(path):
    """测试文件夹访问"""
    print(f"\n{'='*60}")
    print(f"测试路径: {path}")
    print(f"{'='*60}")
    
    # 1. 检查路径是否存在
    exists = os.path.exists(path)
    print(f"1. 路径存在: {exists}")
    
    if not exists:
        # 检查是否为符号链接
        is_link = os.path.islink(path)
        print(f"   是符号链接: {is_link}")
        if is_link:
            try:
                target = os.readlink(path)
                print(f"   链接目标: {target}")
            except:
                pass
        return False
    
    # 2. 检查是否为目录
    is_dir = os.path.isdir(path)
    print(f"2. 是目录: {is_dir}")
    
    if not is_dir:
        return False
    
    # 3. 检查是否为符号链接
    is_link = os.path.islink(path)
    print(f"3. 是符号链接: {is_link}")
    
    # 4. 检查权限
    readable = os.access(path, os.R_OK)
    writable = os.access(path, os.W_OK)
    executable = os.access(path, os.X_OK)
    print(f"4. 权限:")
    print(f"   可读: {readable}")
    print(f"   可写: {writable}")
    print(f"   可执行: {executable}")
    
    # 5. 尝试列出内容
    try:
        items = os.listdir(path)
        print(f"5. 列出内容: 成功 ({len(items)} 个项目)")
        
        # 显示前10个项目
        if items:
            print(f"   前10个项目:")
            for item in sorted(items)[:10]:
                item_path = os.path.join(path, item)
                item_type = "目录" if os.path.isdir(item_path) else "文件"
                print(f"     - {item} ({item_type})")
        
        return True
    except PermissionError as e:
        print(f"5. 列出内容: 权限错误 - {e}")
        return False
    except Exception as e:
        print(f"5. 列出内容: 错误 - {e}")
        return False

def main():
    """主函数"""
    print("飞牛OS文件夹访问测试")
    print("="*60)
    
    # 测试路径列表
    test_paths = [
        '/',
        '/vol00',
        '/vol01',
        '/vol02',
        '/vol1',
        '/vol2',
        '/vol02/1000-1-b23abde7',
        '/vol02/1000-1-b23abde7/待整理',
    ]
    
    results = []
    for path in test_paths:
        success = test_folder_access(path)
        results.append((path, success))
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    for path, success in results:
        status = "✅ 可访问" if success else "❌ 不可访问"
        print(f"{status}: {path}")
    
    # 额外建议
    print(f"\n{'='*60}")
    print("建议")
    print(f"{'='*60}")
    
    accessible_vols = [path for path, success in results if success and path.startswith('/vol')]
    
    if accessible_vols:
        print(f"\n可访问的存储卷:")
        for vol in accessible_vols:
            print(f"  - {vol}")
        print(f"\n建议使用这些路径作为扫描起点。")
    else:
        print("\n未找到可访问的存储卷。")
        print("可能的原因:")
        print("  1. Python进程没有足够的权限")
        print("  2. 存储卷未正确挂载")
        print("  3. 路径名称不正确")
        print("\n解决方案:")
        print("  1. 使用 sudo 运行服务")
        print("  2. 检查挂载点: mount | grep vol")
        print("  3. 检查实际路径: ls -la /")

if __name__ == '__main__':
    main()
