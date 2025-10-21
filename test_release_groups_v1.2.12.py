#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Release Group 识别测试 - v1.2.12
测试新增的 100+ 制作组识别能力
"""

import re

# 从 app.py 复制的 Release Group 列表
RELEASE_GROUPS = [
    # CHD 系列
    'CHD', 'CHDBits', 'CHDPAD', 'CHDTV', 'CHDHKTV', 'CHDWEB', 'CHDWEBII', 'CHDWEBIII',
    'StBOX', 'OneHD', 'Lee', 'xiaopie',
    # HDChina 系列
    'HDC', 'HDChina', 'HDCTV', 'k9611', 'tudou', 'iHD',
    # HHanClub
    'HHWEB',
    # KeepFrds
    'FRDS', 'Yumi', 'cXcY',
    # LemonHD
    'LeagueCD', 'LeagueHD', 'LeagueMV', 'LeagueTV', 'LeagueNF', 'LeagueWEB', 
    'LHD', 'i18n', 'CiNT',
    # MTeam
    'MTeam', 'MTeamTV', 'MPAD', 'MWeb',
    # OurBits
    'OurBits', 'OurTV', 'FLTTH', 'Ao', 'PbK', 'MGs', 'iLoveHD', 'iLoveTV',
    # PTerClub
    'PTer', 'PTerDIY', 'PTerGame', 'PTerMV', 'PTerTV', 'PTerWEB',
    # PTHome
    'PTH', 'PTHAudio', 'PTHeBook', 'PTHmusic', 'PTHome', 'PTHtv', 'PTHWEB',
    # PTsbao
    'PTsbao', 'OPS', 'FFans', 'FFansAIeNcE', 'FFansBD', 'FFansDVD', 'FFansDIY', 
    'FFansTV', 'FFansWEB', 'FHDMv', 'SGXT',
    # ToTheGlory
    'TTG', 'WiKi', 'NGB', 'DoA', 'ARiN', 'ExREN',
    # 动漫组
    'ANi', 'HYSUB', 'KTXP', 'LoliHouse', 'MCE', 'Nekomoe kissaten',
    # 国际组
    'NTb', 'FLUX', 'SMURF', 'CMRG', 'DON', 'EVO',
]

def remove_release_group(title):
    """移除 Release Group"""
    for group in RELEASE_GROUPS:
        escaped_group = re.escape(group)
        patterns = [
            rf'\[{escaped_group}\]',  # [GROUP] - 优先处理括号
            rf'\({escaped_group}\)',  # (GROUP)
            rf'【{escaped_group}】',  # 【GROUP】
            rf'[-.]?{escaped_group}(?=[@.\s\[\]】&]|$)',  # -GROUP, .GROUP
        ]
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # 清理多余的空括号和分隔符
    title = re.sub(r'\[\s*\]', '', title)  # 移除空方括号
    title = re.sub(r'【\s*】', '', title)  # 移除空中文括号
    title = re.sub(r'\(\s*\)', '', title)  # 移除空圆括号
    title = re.sub(r'[-.\s]+$', '', title)  # 移除末尾的分隔符
    title = re.sub(r'^[-.\s]+', '', title)  # 移除开头的分隔符
    
    return title.strip()

# 测试用例
test_cases = [
    # CHD 系列
    {
        'input': '密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB',
        'expected': '密室大逃脱.S07.1080p.WEB-DL.H265.AAC',
        'description': 'CHD 系列 - CHDWEB'
    },
    {
        'input': '某剧[CHDBits]',
        'expected': '某剧',
        'description': 'CHD 系列 - 方括号格式'
    },
    {
        'input': '某剧【CHDTV】',
        'expected': '某剧',
        'description': 'CHD 系列 - 中文括号'
    },
    {
        'input': '某剧.CHD.1080p',
        'expected': '某剧.1080p',
        'description': 'CHD 系列 - 点号分隔'
    },
    
    # HDChina 系列
    {
        'input': '某剧-HDChina',
        'expected': '某剧',
        'description': 'HDChina 系列'
    },
    {
        'input': '某剧.HDCTV.1080p',
        'expected': '某剧.1080p',
        'description': 'HDChina 系列 - HDCTV'
    },
    
    # LemonHD 系列
    {
        'input': '某剧-LeagueHD',
        'expected': '某剧',
        'description': 'LemonHD 系列'
    },
    {
        'input': '某剧.LeagueWEB.1080p',
        'expected': '某剧.1080p',
        'description': 'LemonHD 系列 - LeagueWEB'
    },
    
    # MTeam 系列
    {
        'input': '某剧-MTeam',
        'expected': '某剧',
        'description': 'MTeam 系列'
    },
    {
        'input': '某剧.MTeamTV.1080p',
        'expected': '某剧.1080p',
        'description': 'MTeam 系列 - MTeamTV'
    },
    
    # OurBits 系列
    {
        'input': '某剧-OurBits',
        'expected': '某剧',
        'description': 'OurBits 系列'
    },
    {
        'input': '某剧.OurTV.1080p',
        'expected': '某剧.1080p',
        'description': 'OurBits 系列 - OurTV'
    },
    
    # PTer 系列
    {
        'input': '某剧-PTer',
        'expected': '某剧',
        'description': 'PTer 系列'
    },
    {
        'input': '某剧.PTerWEB.1080p',
        'expected': '某剧.1080p',
        'description': 'PTer 系列 - PTerWEB'
    },
    
    # PTHome 系列
    {
        'input': '某剧-PTHome',
        'expected': '某剧',
        'description': 'PTHome 系列'
    },
    {
        'input': '某剧.PTHWEB.1080p',
        'expected': '某剧.1080p',
        'description': 'PTHome 系列 - PTHWEB'
    },
    
    # 动漫字幕组
    {
        'input': '[LoliHouse] 某动漫 - 01 [WebRip 1080p HEVC-10bit AAC]',
        'expected': '某动漫 - 01 [WebRip 1080p HEVC-10bit AAC]',
        'description': '动漫组 - LoliHouse'
    },
    {
        'input': '[ANi] 某动漫 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT]',
        'expected': '某动漫 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT]',
        'description': '动漫组 - ANi'
    },
    {
        'input': '[KTXP] 某动漫 [01][GB][1080p]',
        'expected': '某动漫 [01][GB][1080p]',
        'description': '动漫组 - KTXP'
    },
    
    # 国际组
    {
        'input': '某剧-NTb',
        'expected': '某剧',
        'description': '国际组 - NTb'
    },
    {
        'input': '某剧.FLUX.1080p',
        'expected': '某剧.1080p',
        'description': '国际组 - FLUX'
    },
    
    # 多个制作组
    {
        'input': '某剧-CHDWEB-NGB',
        'expected': '某剧',
        'description': '多个制作组'
    },
    {
        'input': '某剧[CHDBits][FRDS]',
        'expected': '某剧',
        'description': '多个制作组 - 方括号'
    },
    
    # 边界测试
    {
        'input': 'CHDWEB某剧',
        'expected': 'CHDWEB某剧',
        'description': '边界测试 - 前面没有分隔符（不应匹配）'
    },
    {
        'input': '某剧CHDWEB',
        'expected': '某剧CHDWEB',
        'description': '边界测试 - 后面没有分隔符（不应匹配）'
    },
    
    # 大小写测试
    {
        'input': '某剧-chdweb',
        'expected': '某剧',
        'description': '大小写测试 - 小写'
    },
    {
        'input': '某剧-ChDwEb',
        'expected': '某剧',
        'description': '大小写测试 - 混合'
    },
]

def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("Release Group 识别测试 - v1.2.12")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_title = test['input']
        expected = test['expected']
        description = test['description']
        
        result = remove_release_group(input_title)
        
        if result == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"测试 {i}: {description}")
        print(f"  输入:   {input_title}")
        print(f"  期望:   {expected}")
        print(f"  实际:   {result}")
        print(f"  状态:   {status}")
        print()
    
    print("=" * 80)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print(f"通过率: {passed / len(test_cases) * 100:.1f}%")
    print("=" * 80)
    
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
