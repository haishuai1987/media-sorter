#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TitleParser 测试脚本
测试文件名解析功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入TitleParser（需要从app.py导入）
from app import TitleParser, TitleMapper, QueryStrategy

def test_title_parser():
    """测试TitleParser"""
    print("=" * 80)
    print("测试 TitleParser（标题解析器）")
    print("=" * 80)
    
    test_cases = [
        "The.Mandalorian.S02E01.2160p.WEB-DL.x265-ADWeb.mkv",
        "Breaking.Bad.S05E16.1080p.BluRay.x264-ROVERS.mkv",
        "Game.of.Thrones.S08E06.The.Iron.Throne.1080p.WEB-DL.DD5.1.H264-GoT.mkv",
        "Inception.2010.1080p.BluRay.x264-SPARKS.mkv",
        "The.Dark.Knight.2008.2160p.UHD.BluRay.x265-TERMINAL.mkv",
        "Friends.S10E18.The.Last.One.Part.2.1080p.BluRay.x264-PSYCHD.mkv",
    ]
    
    for filename in test_cases:
        print(f"\n原始文件名: {filename}")
        
        # 移除扩展名
        name_without_ext = os.path.splitext(filename)[0]
        
        # 解析
        result = TitleParser.parse(name_without_ext)
        
        print(f"解析结果:")
        print(f"  标题: {result['title']}")
        print(f"  年份: {result['year'] or '无'}")
        print(f"  季数: {result['season'] or '无'}")
        print(f"  集数: {result['episode'] or '无'}")
        print("-" * 80)

def test_title_mapper():
    """测试TitleMapper"""
    print("\n" + "=" * 80)
    print("测试 TitleMapper（标题映射器）")
    print("=" * 80)
    
    mapper = TitleMapper()
    
    test_titles = [
        "Breaking Bad",
        "breaking bad",  # 不区分大小写
        "The Mandalorian",
        "Game of Thrones",
        "Unknown Show",  # 不存在的
    ]
    
    for title in test_titles:
        print(f"\n查询标题: {title}")
        mapping = mapper.get_mapping(title)
        
        if mapping:
            print(f"  ✓ 找到映射:")
            print(f"    中文标题: {mapping['chinese_title']}")
            print(f"    TMDB ID: {mapping['tmdb_id']}")
            print(f"    类型: {mapping['type']}")
        else:
            print(f"  ✗ 未找到映射")
        print("-" * 80)

def test_query_strategy():
    """测试QueryStrategy"""
    print("\n" + "=" * 80)
    print("测试 QueryStrategy（查询策略引擎）")
    print("=" * 80)
    
    mapper = TitleMapper()
    strategy = QueryStrategy(mapper)
    
    test_cases = [
        ("Breaking Bad", None, True),
        ("The Mandalorian", "2019", True),
        ("Inception", "2010", False),
    ]
    
    for title, year, is_tv in test_cases:
        print(f"\n查询: {title} ({year or '无年份'}) - {'电视剧' if is_tv else '电影'}")
        
        result = strategy.query(title, year, is_tv)
        
        print(f"结果:")
        print(f"  标题: {result['title']}")
        print(f"  年份: {result['year'] or '无'}")
        print(f"  分类: {result['category'] or '无'}")
        print(f"  策略: {result['strategy']}")
        print("-" * 80)
        
        # 显示查询日志
        print("\n查询日志:")
        for log in strategy.get_query_log():
            print(f"  {log}")

if __name__ == '__main__':
    print("\n🎬 媒体库文件管理器 - TitleParser 测试\n")
    
    try:
        # 测试TitleParser
        test_title_parser()
        
        # 测试TitleMapper
        test_title_mapper()
        
        # 测试QueryStrategy（需要网络连接和TMDB API Key）
        print("\n⚠️  注意: QueryStrategy测试需要配置TMDB API Key")
        response = input("是否测试QueryStrategy？(y/n): ")
        if response.lower() == 'y':
            test_query_strategy()
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
