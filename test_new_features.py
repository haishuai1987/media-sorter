#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新功能：高级识别器、模板引擎、事件系统
"""

def test_advanced_recognizer():
    """测试高级识别器"""
    print("\n" + "="*60)
    print("测试 1: 高级识别器")
    print("="*60)
    
    from core.advanced_recognizer import get_advanced_recognizer
    
    recognizer = get_advanced_recognizer()
    
    # 测试用例
    test_cases = [
        "The.Wandering.Earth.2019.1080p.BluRay.x264.AAC-RARBG.mkv",
        "权力的游戏.Game.of.Thrones.S08E06.1080p.WEB-DL.H264.AAC.mp4",
        "流浪地球2.2023.2160p.WEB-DL.H265.DTS-HD.mkv",
        "进击的巨人.第4季.第16集.1080p.WEBRip.x264.mkv",
        "Avengers.Endgame.2019.4K.UHD.BluRay.REMUX.HDR10+.DV.TrueHD.Atmos.mkv",
    ]
    
    for filename in test_cases:
        print(f"\n文件名: {filename}")
        result = recognizer.recognize(filename)
        
        print(f"  标题: {result['title']}")
        print(f"  年份: {result['year']}")
        if result['is_tv']:
            print(f"  季: {result['season']}, 集: {result['episode']}")
        print(f"  分辨率: {result['resolution']}")
        print(f"  视频编码: {result['video_codec']}")
        print(f"  音频编码: {result['audio_codec']}")
        print(f"  来源: {result['source']}")
        print(f"  HDR: {result['hdr']}")
        print(f"  质量分数: {recognizer.get_quality_score(result)}")
    
    print("\n✅ 高级识别器测试完成")


def test_template_engine():
    """测试模板引擎"""
    print("\n" + "="*60)
    print("测试 2: 模板引擎")
    print("="*60)
    
    from core.template_engine import get_template_engine
    
    engine = get_template_engine()
    
    # 测试电影模板
    movie_context = {
        'title': '流浪地球',
        'year': 2019,
        'resolution': '1080p',
        'video_codec': 'H264',
        'audio_codec': 'AAC',
        'source': 'BluRay',
        'ext': 'mkv',
    }
    
    print("\n电影模板测试:")
    print(f"  输入: {movie_context}")
    
    templates = ['movie_default', 'movie_simple', 'movie_detailed', 'nas_movie', 'plex_movie']
    for template_name in templates:
        result = engine.render(template_name, movie_context)
        print(f"  {template_name}: {result}")
    
    # 测试电视剧模板
    tv_context = {
        'title': '权力的游戏',
        'year': 2011,
        'season': 1,
        'episode': 1,
        'resolution': '1080p',
        'video_codec': 'H265',
        'audio_codec': 'DTS',
        'source': 'WEB-DL',
        'ext': 'mkv',
    }
    
    print("\n电视剧模板测试:")
    print(f"  输入: {tv_context}")
    
    templates = ['tv_default', 'tv_simple', 'tv_detailed', 'nas_tv', 'plex_tv']
    for template_name in templates:
        result = engine.render(template_name, tv_context)
        print(f"  {template_name}: {result}")
    
    # 测试自定义模板
    print("\n自定义模板测试:")
    custom_template = '{title} [{year}] - {quality}.{ext}'
    engine.add_template('my_custom', custom_template)
    result = engine.render('my_custom', movie_context)
    print(f"  自定义模板: {custom_template}")
    print(f"  渲染结果: {result}")
    
    # 测试模板验证
    print("\n模板验证测试:")
    valid_template = '{title} ({year}).{ext}'
    invalid_template = '{title} ({year}.{ext'
    
    is_valid, error = engine.validate_template(valid_template)
    print(f"  有效模板: {valid_template} -> {is_valid}")
    
    is_valid, error = engine.validate_template(invalid_template)
    print(f"  无效模板: {invalid_template} -> {is_valid}, 错误: {error}")
    
    print("\n✅ 模板引擎测试完成")


def test_event_system():
    """测试事件系统"""
    print("\n" + "="*60)
    print("测试 3: 事件系统")
    print("="*60)
    
    from core.events import get_event_bus, EventTypes, event_handler
    
    bus = get_event_bus()
    
    # 测试基本的发布/订阅
    print("\n基本发布/订阅测试:")
    
    received_events = []
    
    def handler1(event):
        print(f"  处理器1收到事件: {event.type}, 数据: {event.data}")
        received_events.append(event)
    
    def handler2(event):
        print(f"  处理器2收到事件: {event.type}, 数据: {event.data}")
    
    # 订阅事件
    bus.on('test.event', handler1)
    bus.on('test.event', handler2)
    
    # 发布事件
    bus.emit('test.event', {'message': 'Hello World'}, source='test')
    
    # 测试一次性处理器
    print("\n一次性处理器测试:")
    
    def once_handler(event):
        print(f"  一次性处理器收到事件: {event.type}")
    
    bus.once('once.event', once_handler)
    
    bus.emit('once.event', {'count': 1})
    bus.emit('once.event', {'count': 2})  # 这次不会触发
    
    # 测试优先级
    print("\n优先级测试:")
    
    def high_priority(event):
        print(f"  高优先级处理器")
    
    def low_priority(event):
        print(f"  低优先级处理器")
    
    bus.on('priority.event', low_priority, priority=1)
    bus.on('priority.event', high_priority, priority=10)
    
    bus.emit('priority.event')
    
    # 测试预定义事件类型
    print("\n预定义事件类型测试:")
    
    def file_handler(event):
        print(f"  文件处理事件: {event.type}, 文件: {event.data.get('filename')}")
    
    bus.on(EventTypes.FILE_PROCESS_START, file_handler)
    bus.on(EventTypes.FILE_PROCESS_COMPLETE, file_handler)
    
    bus.emit(EventTypes.FILE_PROCESS_START, {'filename': 'test.mkv'})
    bus.emit(EventTypes.FILE_PROCESS_COMPLETE, {'filename': 'test.mkv', 'success': True})
    
    # 测试事件历史
    print("\n事件历史测试:")
    history = bus.get_history(limit=5)
    print(f"  最近5个事件:")
    for event in history:
        print(f"    - {event.type} @ {event.datetime.strftime('%H:%M:%S')}")
    
    # 测试统计信息
    print("\n统计信息:")
    stats = bus.get_stats()
    print(f"  总事件数: {stats['total_events']}")
    print(f"  按类型统计: {dict(list(stats['events_by_type'].items())[:3])}")
    print(f"  活跃处理器: {stats['active_handlers']}")
    
    # 测试装饰器
    print("\n装饰器测试:")
    
    @event_handler('decorated.event', priority=5)
    def decorated_handler(event):
        print(f"  装饰器处理器收到事件: {event.type}")
    
    bus.emit('decorated.event', {'test': 'decorator'})
    
    print("\n✅ 事件系统测试完成")


def test_integration():
    """测试集成场景"""
    print("\n" + "="*60)
    print("测试 4: 集成场景")
    print("="*60)
    
    from core.advanced_recognizer import get_advanced_recognizer
    from core.template_engine import get_template_engine
    from core.events import get_event_bus, EventTypes
    
    recognizer = get_advanced_recognizer()
    engine = get_template_engine()
    bus = get_event_bus()
    
    # 设置事件监听
    def on_process_start(event):
        print(f"  📂 开始处理: {event.data['filename']}")
    
    def on_process_complete(event):
        print(f"  ✅ 处理完成: {event.data['new_name']}")
    
    bus.on(EventTypes.FILE_PROCESS_START, on_process_start)
    bus.on(EventTypes.FILE_PROCESS_COMPLETE, on_process_complete)
    
    # 模拟完整的处理流程
    print("\n完整处理流程:")
    
    filename = "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv"
    
    # 1. 发布开始事件
    bus.emit(EventTypes.FILE_PROCESS_START, {'filename': filename})
    
    # 2. 识别文件
    info = recognizer.recognize(filename)
    print(f"  🔍 识别结果: {info['title']} ({info['year']}) - {info['resolution']}")
    
    # 3. 使用模板生成新文件名
    context = {
        'title': info['title'],
        'year': info['year'],
        'resolution': info['resolution'],
        'video_codec': info['video_codec'],
        'audio_codec': info['audio_codec'],
        'source': info['source'],
        'ext': 'mkv',
    }
    
    new_name = engine.render('movie_detailed', context)
    print(f"  📝 新文件名: {new_name}")
    
    # 4. 发布完成事件
    bus.emit(EventTypes.FILE_PROCESS_COMPLETE, {
        'filename': filename,
        'new_name': new_name,
        'quality_score': recognizer.get_quality_score(info)
    })
    
    print("\n✅ 集成测试完成")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("新功能测试套件")
    print("="*60)
    
    try:
        test_advanced_recognizer()
        test_template_engine()
        test_event_system()
        test_integration()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
