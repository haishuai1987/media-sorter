#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 v2.4.0 新功能
- 中文数字转换
- 增强的识别功能
"""


def test_chinese_number_conversion():
    """测试中文数字转换"""
    print("\n" + "="*60)
    print("测试 1: 中文数字转换")
    print("="*60)
    
    from core.chinese_number import ChineseNumber
    
    # 测试内置转换器
    print("\n测试 1.1: 内置转换器")
    print("-" * 60)
    
    converter = ChineseNumber(use_cn2an=False)
    
    test_cases = [
        ("权力的游戏第一季", "权力的游戏第1季"),
        ("权力的游戏第二季", "权力的游戏第2季"),
        ("权力的游戏第十季", "权力的游戏第10季"),
        ("流浪地球二", "流浪地球2"),
        ("复仇者联盟四", "复仇者联盟4"),
        ("第一集", "第1集"),
        ("第二十集", "第20集"),
    ]
    
    for original, expected in test_cases:
        result = converter.convert(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} {original} → {result}")
        if result != expected:
            print(f"   预期: {expected}")
    
    # 测试 cn2an（如果可用）
    print("\n测试 1.2: cn2an 转换器")
    print("-" * 60)
    
    converter2 = ChineseNumber(use_cn2an=True)
    
    if converter2.cn2an_available:
        print("✓ cn2an 库可用")
        
        for original, _ in test_cases:
            result = converter2.convert(original)
            print(f"  {original} → {result}")
    else:
        print("ℹ cn2an 库未安装")
    
    # 测试季集转换
    print("\n测试 1.3: 季集转换")
    print("-" * 60)
    
    season_tests = [
        "权力的游戏.第一季.第五集.1080p.mkv",
        "权力的游戏.S二E十.1080p.mkv",
        "流浪地球.第二部.2023.mkv",
    ]
    
    for text in season_tests:
        result = converter.convert_season_episode(text)
        print(f"原始: {text}")
        print(f"结果: {result}")
        print()
    
    print("✓ 中文数字转换测试完成")


def test_enhanced_recognition():
    """测试增强的识别功能"""
    print("\n" + "="*60)
    print("测试 2: 增强的识别功能")
    print("="*60)
    
    from core.chinese_title_resolver import IntegratedRecognizer
    
    recognizer = IntegratedRecognizer()
    
    # 测试中文数字转换集成
    print("\n测试 2.1: 中文数字转换集成")
    print("-" * 60)
    
    test_files = [
        "权力的游戏.第一季.第五集.1080p.BluRay.x264.mkv",
        "流浪地球.第二部.2023.1080p.WEB-DL.H264.mkv",
        "复仇者联盟.第四部.终局之战.2019.4K.UHD.mkv",
    ]
    
    for filename in test_files:
        print(f"\n文件: {filename}")
        
        # 不转换中文数字
        info1 = recognizer.recognize_with_chinese_title(filename, convert_chinese_number=False)
        print(f"  不转换: {info1['title']} S{info1['season']:02d}E{info1['episode']:02d}" if info1['is_tv'] else f"  不转换: {info1['title']}")
        
        # 转换中文数字
        info2 = recognizer.recognize_with_chinese_title(filename, convert_chinese_number=True)
        print(f"  转换后: {info2['title']} S{info2['season']:02d}E{info2['episode']:02d}" if info2['is_tv'] else f"  转换后: {info2['title']}")
    
    print("\n✓ 增强的识别功能测试完成")


def test_integration_with_batch_processor():
    """测试与批量处理器的集成"""
    print("\n" + "="*60)
    print("测试 3: 与批量处理器集成")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    
    processor = SmartBatchProcessor()
    
    test_files = [
        "权力的游戏.第一季.第一集.1080p.BluRay.x264.mkv",
        "流浪地球.第二部.2023.1080p.WEB-DL.H264.mkv",
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
    ]
    
    print("\n批量处理测试:")
    print("-" * 60)
    
    result = processor.process_batch(test_files)
    
    print(f"\n处理结果:")
    for r in result['results']:
        if r['success']:
            print(f"✓ {r['original_name']}")
            print(f"  → {r['new_name']}")
        else:
            print(f"✗ {r['file_path']}: {r['error']}")
    
    print(f"\n统计:")
    print(f"  成功: {result['stats']['success']}/{result['stats']['total_files']}")
    print(f"  失败: {result['stats']['failed']}")
    
    print("\n✓ 批量处理器集成测试完成")


def test_custom_words_with_chinese_number():
    """测试自定义识别词与中文数字的配合"""
    print("\n" + "="*60)
    print("测试 4: 自定义识别词与中文数字配合")
    print("="*60)
    
    from core.custom_words import CustomWords
    from core.chinese_number import convert_chinese_number
    
    cw = CustomWords()
    
    # 添加测试规则
    cw.add_word({
        'type': 'replace',
        'old': '第二部',
        'new': '2',
        'description': '替换"第二部"',
        'enabled': True
    })
    
    test_text = "流浪地球.第二部.2023.1080p.mkv"
    
    print(f"\n原始文本: {test_text}")
    
    # 先转换中文数字
    step1 = convert_chinese_number(test_text)
    print(f"中文数字转换: {step1}")
    
    # 再应用自定义识别词
    step2 = cw.apply(step1)
    print(f"自定义识别词: {step2}")
    
    print("\n✓ 配合测试完成")


def test_performance_comparison():
    """性能对比测试"""
    print("\n" + "="*60)
    print("测试 5: 性能对比")
    print("="*60)
    
    import time
    from core.chinese_number import ChineseNumber
    
    # 测试数据
    test_data = [
        "权力的游戏第一季",
        "权力的游戏第二季",
        "权力的游戏第三季",
        "流浪地球二",
        "复仇者联盟四",
    ] * 100  # 500 次转换
    
    # 内置转换器
    print("\n内置转换器:")
    converter1 = ChineseNumber(use_cn2an=False)
    start = time.time()
    for text in test_data:
        converter1.convert(text)
    duration1 = time.time() - start
    print(f"  耗时: {duration1:.4f}秒")
    print(f"  速度: {len(test_data)/duration1:.0f} 次/秒")
    
    # cn2an 转换器
    print("\ncn2an 转换器:")
    converter2 = ChineseNumber(use_cn2an=True)
    if converter2.cn2an_available:
        start = time.time()
        for text in test_data:
            converter2.convert(text)
        duration2 = time.time() - start
        print(f"  耗时: {duration2:.4f}秒")
        print(f"  速度: {len(test_data)/duration2:.0f} 次/秒")
        print(f"  对比: {duration1/duration2:.2f}x")
    else:
        print("  cn2an 库未安装")
    
    print("\n✓ 性能对比测试完成")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("v2.4.0 功能增强测试套件")
    print("="*60)
    
    try:
        # 运行所有测试
        test_chinese_number_conversion()
        test_enhanced_recognition()
        test_integration_with_batch_processor()
        test_custom_words_with_chinese_number()
        test_performance_comparison()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成!")
        print("="*60)
        
        print("\nv2.4.0 新功能:")
        print("✓ 中文数字转换 - 支持内置和 cn2an 两种方式")
        print("✓ 增强识别功能 - 自动转换中文数字")
        print("✓ 批量处理集成 - 无缝集成到现有流程")
        print("✓ 性能优化 - 高效的转换算法")
        
        print("\n使用建议:")
        print("- 安装 cn2an 库以获得更好的转换效果: pip install cn2an")
        print("- 默认启用中文数字转换")
        print("- 可通过参数控制是否转换")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
