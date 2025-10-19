#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析OpenList Desktop项目
"""

import requests

# GitHub API
repo_url = "https://api.github.com/repos/OpenListTeam/OpenList-Desktop"
readme_url = "https://raw.githubusercontent.com/OpenListTeam/OpenList-Desktop/main/README.md"

print("="*60)
print("分析 OpenList-Desktop 项目")
print("="*60)

# 1. 获取仓库信息
try:
    print("\n1. 获取仓库信息...")
    response = requests.get(repo_url, timeout=10)
    if response.status_code == 200:
        repo_data = response.json()
        print(f"✅ 项目名称: {repo_data.get('name')}")
        print(f"   描述: {repo_data.get('description')}")
        print(f"   语言: {repo_data.get('language')}")
        print(f"   Stars: {repo_data.get('stargazers_count')}")
        print(f"   主题: {repo_data.get('topics', [])}")
except Exception as e:
    print(f"❌ 获取仓库信息失败: {e}")

# 2. 获取README
try:
    print("\n2. 获取README内容...")
    response = requests.get(readme_url, timeout=10)
    if response.status_code == 200:
        readme = response.text
        print(f"✅ README长度: {len(readme)} 字符")
        
        # 保存README
        with open('openlist_desktop_readme.md', 'w', encoding='utf-8') as f:
            f.write(readme)
        print("   已保存到: openlist_desktop_readme.md")
        
        # 分析关键词
        print("\n3. 关键词分析:")
        keywords = {
            'rclone': 'Rclone',
            'token': 'Token',
            'cookie': 'Cookie',
            'oauth': 'OAuth',
            '115': '115网盘',
            'mount': '挂载',
            'webdav': 'WebDAV',
        }
        
        for key, name in keywords.items():
            count = readme.lower().count(key.lower())
            if count > 0:
                print(f"   ✅ {name}: 出现 {count} 次")
        
        # 提取重要段落
        print("\n4. README内容预览:")
        print("-"*60)
        lines = readme.split('\n')
        for i, line in enumerate(lines[:50], 1):
            if line.strip():
                print(f"{i}. {line[:100]}")
        
except Exception as e:
    print(f"❌ 获取README失败: {e}")

# 3. 获取项目文件结构
try:
    print("\n5. 获取项目文件结构...")
    contents_url = "https://api.github.com/repos/OpenListTeam/OpenList-Desktop/contents"
    response = requests.get(contents_url, timeout=10)
    if response.status_code == 200:
        contents = response.json()
        print(f"✅ 根目录文件:")
        for item in contents:
            icon = "📁" if item['type'] == 'dir' else "📄"
            print(f"   {icon} {item['name']}")
except Exception as e:
    print(f"❌ 获取文件结构失败: {e}")

print("\n" + "="*60)
print("分析完成！")
print("="*60)
print("\n关键发现：")
print("请查看 openlist_desktop_readme.md 了解详细信息")
