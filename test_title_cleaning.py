#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试标题清理功能"""

import re

def extract_chinese_title(title):
    """从混合标题中提取纯中文标题（借鉴 MoviePilot 实现）"""
    if not title:
        return title
    
    # 检查是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in title)
    
    if not has_chinese:
        # 没有中文，返回原标题
        return title
    
    # 1. 移除 Release Group（常见的制作组）
    release_groups = [
        'CHDWEB', 'CHDWEBII', 'CHDWEBIII', 'ADWeb', 'HHWEB', 'DBTV', 
        'NGB', 'FRDS', 'mUHD', 'AilMWeb', 'UBWEB', 'CHDTV', 'HDCTV'
    ]
    for group in release_groups:
        # 移除末尾的 -GROUP
        title = re.sub(rf'-{group}$', '', title, flags=re.IGNORECASE)
        # 移除中间的 .GROUP.
        title = re.sub(rf'\.{group}\.', '.', title, flags=re.IGNORECASE)
        # 移除末尾的 .GROUP
        title = re.sub(rf'\.{group}$', '', title, flags=re.IGNORECASE)
    
    # 2. 移除技术参数
    tech_params = [
        '2160p', '1080p', '720p', '480p', '4K', '8K',
        'H.264', 'H.265', 'H264', 'H265', 'x264', 'x265', 'HEVC', 'AVC',
        'WEB-DL', 'WEBRip', 'BluRay', 'BDRip', 'HDRip', 'DVDRip',
        'DDP', 'DD', 'AAC', 'AC3', 'DTS', 'Atmos', 'TrueHD',
        'DDP5.1', 'DDP2.0', 'AAC2.0', 'AAC5.1',
        'HDR', 'SDR', 'Dolby', 'Vision', 'HDR10', 'HDR10+',
        'AMZN', 'NF', 'DSNP', 'HMAX', 'ATVP', 'PCOK', 'PMTP'
    ]
    for param in tech_params:
        # 移除 .PARAM.
        title = re.sub(rf'\.{param}\.', '.', title, flags=re.IGNORECASE)
        # 移除 .PARAM
        title = re.sub(rf'\.{param}$', '', title, flags=re.IGNORECASE)
        # 移除 PARAM.
        title = re.sub(rf'^{param}\.', '', title, flags=re.IGNORECASE)
    
    # 3. 替换点号为空格，方便处理
    cleaned = title.replace('.', ' ')
    
    # 4. 分割成词
    parts = cleaned.split()
    
    # 5. 提取中文部分（只保留包含中文的词）
    chinese_parts = []
    for part in parts:
        # 只保留包含中文字符的词
        if any('\u4e00' <= c <= '\u9fff' for c in part):
            chinese_parts.append(part)
    
    if chinese_parts:
        result = ' '.join(chinese_parts)
        # 移除多余空格
        result = ' '.join(result.split())
        # 只移除末尾的"第X季"等冗余信息（保留"大神版"等版本标识）
        result = re.sub(r'\s*第[一二三四五六七八九十\d]+季$', '', result)
        return result.strip()
    
    # 如果提取失败，返回原标题
    return title

# 测试用例
test_cases = [
    # 基础测试
    ("密室大逃脱 Great Escape", "密室大逃脱"),
    ("密室大逃脱大神版 Great Escape Super", "密室大逃脱大神版"),
    ("密室大逃脱大神版.第七季.Great.Escape.Super", "密室大逃脱大神版"),
    ("Great Escape", "Great Escape"),
    
    # 带 Release Group
    ("密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB", "密室大逃脱"),
    ("花牌情缘：巡.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-CHDWEB", "花牌情缘：巡"),
    ("间谍过家家.S03.2025.1080p.CR.WEB-DL.x264.AAC-ADWeb", "间谍过家家"),
    
    # 带技术参数
    ("奔跑吧.Keep.Running.S09.2025.1080p.WEB-DL.H265.AAC", "奔跑吧"),
    ("坂本日常.SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC", "坂本日常"),
    
    # 复杂情况
    ("新·吊带袜天使.New.PANTY.&.STOCKING.S01.1080p.AMZN.WEB-DL.DDP.5.1.H.264-CHDWEB", "新·吊带袜天使"),
    ("从前有个刺客.Nero.the.Assassin.S01.2025.1080p.NF.WEB-DL.x264.DDP5.1.Atmos-ADWeb", "从前有个刺客"),
    
    # 纯英文
    ("Black Rabbit", "Black Rabbit"),
]

print("测试标题清理功能：\n")
for original, expected in test_cases:
    result = extract_chinese_title(original)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{original}'")
    print(f"  期望: '{expected}'")
    print(f"  结果: '{result}'")
    print()
