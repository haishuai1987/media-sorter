#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文标题解析
演示完整的识别 + 中文标题查询流程
"""

def test_chinese_title_resolver():
    """测试中文标题解析器"""
    print("\n" + "="*60)
    print("测试: 中文标题解析器")
    print("="*60)
    
    from core.chinese_title_resolver import IntegratedRecognizer
    
    # 注意：需要配置 API Key 和 Cookie
    # 这里使用模拟数据演示流程
    
    print("\n说明：")
    print("1. 高级识别器只提取文件名中的信息")
    print("2. 中文标题解析器会查询 TMDB/豆瓣获取中文标题")
    print("3. 最终确保所有标题都是中文")
    
    # 创建识别器（需要配置 API）
    recognizer = IntegratedRecognizer(
        tmdb_api_key="YOUR_TMDB_API_KEY",  # 需要替换
        douban_cookie="YOUR_DOUBAN_COOKIE"  # 需要替换
    )
    
    # 测试用例
    test_cases = [
        "The.Wandering.Earth.2019.1080p.BluRay.x264.AAC-RARBG.mkv",
        "Avengers.Endgame.2019.4K.UHD.BluRay.REMUX.HDR10+.DV.TrueHD.Atmos.mkv",
        "流浪地球2.2023.2160p.WEB-DL.H265.DTS-HD.mkv",  # 已经是中文
    ]
    
    print("\n" + "-"*60)
    print("完整识别流程演示：")
    print("-"*60)
    
    for filename in test_cases:
        print(f"\n文件名: {filename}")
        print("步骤 1: 高级识别器提取信息...")
        
        # 只使用高级识别器
        from core.advanced_recognizer import get_advanced_recognizer
        basic_info = get_advanced_recognizer().recognize(filename)
        print(f"  提取的标题: {basic_info['title']}")
        print(f"  年份: {basic_info['year']}")
        print(f"  分辨率: {basic_info['resolution']}")
        
        print("步骤 2: 检查是否需要查询中文标题...")
        if not any('\u4e00' <= c <= '\u9fff' for c in basic_info['title']):
            print(f"  ✗ 标题是英文，需要查询中文标题")
            print(f"  → 查询 TMDB/豆瓣: '{basic_info['title']}' ({basic_info['year']})")
            print(f"  → 期望结果: 流浪地球 / 复仇者联盟4：终局之战")
        else:
            print(f"  ✓ 标题已经是中文，无需查询")


def demo_workflow():
    """演示完整工作流程"""
    print("\n" + "="*60)
    print("完整工作流程演示")
    print("="*60)
    
    from core.advanced_recognizer import get_advanced_recognizer
    from core.template_engine import get_template_engine
    
    recognizer = get_advanced_recognizer()
    engine = get_template_engine()
    
    print("\n场景 1: 英文文件名 → 需要查询中文标题")
    print("-"*60)
    
    filename = "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv"
    print(f"输入: {filename}")
    
    # 步骤 1: 高级识别
    info = recognizer.recognize(filename)
    print(f"\n步骤 1 - 高级识别:")
    print(f"  标题: {info['title']}")
    print(f"  年份: {info['year']}")
    print(f"  分辨率: {info['resolution']}")
    print(f"  来源: {info['source']}")
    
    # 步骤 2: 查询中文标题（模拟）
    print(f"\n步骤 2 - 查询中文标题:")
    print(f"  英文标题: {info['title']}")
    print(f"  → 查询 TMDB/豆瓣...")
    print(f"  → 找到中文标题: 黑客帝国")
    
    # 模拟替换为中文标题
    info['original_title'] = info['title']
    info['title'] = '黑客帝国'
    
    # 步骤 3: 使用模板生成文件名
    print(f"\n步骤 3 - 生成新文件名:")
    context = {
        'title': info['title'],
        'year': info['year'],
        'resolution': info['resolution'],
        'video_codec': info['video_codec'],
        'audio_codec': info['audio_codec'],
        'source': info['source'],
        'ext': 'mkv',
    }
    
    new_name = engine.render('movie_default', context)
    print(f"  模板: movie_default")
    print(f"  结果: {new_name}")
    
    print("\n" + "="*60)
    print("场景 2: 中文文件名 → 无需查询")
    print("-"*60)
    
    filename = "流浪地球.2019.1080p.BluRay.x264.AAC.mkv"
    print(f"输入: {filename}")
    
    info = recognizer.recognize(filename)
    print(f"\n步骤 1 - 高级识别:")
    print(f"  标题: {info['title']}")
    print(f"  年份: {info['year']}")
    
    print(f"\n步骤 2 - 检查标题:")
    print(f"  ✓ 标题已经是中文，跳过查询")
    
    context = {
        'title': info['title'],
        'year': info['year'],
        'resolution': info['resolution'],
        'video_codec': info['video_codec'],
        'audio_codec': info['audio_codec'],
        'source': info['source'],
        'ext': 'mkv',
    }
    
    new_name = engine.render('movie_default', context)
    print(f"\n步骤 3 - 生成新文件名:")
    print(f"  结果: {new_name}")


def show_integration_guide():
    """显示集成指南"""
    print("\n" + "="*60)
    print("集成指南")
    print("="*60)
    
    print("""
在 app.py 中集成中文标题解析：

1. 导入模块：
   from core.chinese_title_resolver import IntegratedRecognizer

2. 创建识别器：
   recognizer = IntegratedRecognizer(
       tmdb_api_key=TMDB_API_KEY,
       douban_cookie=DOUBAN_COOKIE
   )

3. 识别文件（自动获取中文标题）：
   info = recognizer.recognize_with_chinese_title(filename)
   
   # info['title'] 现在是中文标题
   # info['original_title'] 保存原始英文标题（如果有）

4. 使用模板生成文件名：
   from core.template_engine import get_template_engine
   
   engine = get_template_engine()
   new_name = engine.render('movie_default', {
       'title': info['title'],  # 中文标题
       'year': info['year'],
       'resolution': info['resolution'],
       'source': info['source'],
       'ext': 'mkv',
   })

完整流程：
  英文文件名 
    ↓
  高级识别器（提取信息）
    ↓
  检测到英文标题
    ↓
  查询 TMDB/豆瓣
    ↓
  获取中文标题
    ↓
  使用模板生成新文件名
    ↓
  中文文件名 ✓

关键点：
- ✓ 所有英文标题都会自动查询中文
- ✓ 中文标题直接使用，不查询
- ✓ 保留原始英文标题在 original_title 字段
- ✓ 查询失败时保留英文标题（不会丢失信息）
""")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("中文标题解析测试")
    print("="*60)
    
    try:
        test_chinese_title_resolver()
        demo_workflow()
        show_integration_guide()
        
        print("\n" + "="*60)
        print("✓ 测试完成")
        print("="*60)
        
        print("\n重要提示：")
        print("1. 需要配置 TMDB API Key 和豆瓣 Cookie")
        print("2. 高级识别器 + 中文标题解析器 = 完整解决方案")
        print("3. 确保所有标题最终都是中文")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
