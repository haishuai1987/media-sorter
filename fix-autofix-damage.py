#!/usr/bin/env python3
"""修复Kiro IDE Autofix破坏的代码"""

import re

# 读取文件
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复被破坏的正则表达式
# 查找并替换所有被Autofix破坏的代码
content = re.sub(
    r"name = re\.sub\(r'\[-\\\[\\\(\]\[A-Z0-9\]\+\[\\\]\\\)\]</content>\s*</file>, '', name\)",
    "name = re.sub(r'[-\\[\\(][A-Z0-9]+[\\]\\)]$', '', name)",
    content
)

# 写回文件
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 修复完成！")
print("已移除Autofix插入的XML标签")
