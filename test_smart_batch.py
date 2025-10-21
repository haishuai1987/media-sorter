#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能批量处理器
演示借鉴 media-renamer-2 的批量处理功能
"""

def test_smart_batch_processor():
    """测试智能批量处理器"""
    print("\n" + "="*60)
    print("测试: 智能批量处理器")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    
    # 创建处理器
    processor = SmartBatchProcessor()
    
    # 测试文件列表
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv",
        "Avengers.Endgame.2019.4K.UHD.BluRay.REMUX.HDR10+.DV.TrueHD.Atmos.mkv",
        "Game.of.Thrones.S08E06.1080p.WEB-DL.H264.AAC.mp4",
        "流浪地球.2019.1080p.BluRay.x264.AAC.mkv",
        "权力的游戏.S01E01.1080p.BluRay.x265.HEVC.mkv",
    ]
    
    print(f"\n待处理文件数量: {len(test_files)}")
    print("-" * 60)
    
    # 进度回调函数
    def progress_callback(progress, current_file, result):
        print(f"进度: {progress*100:.1f}% - {result['message']}")
    
    # 批量处理
    print("\n开始批量处理...")
    batch_result = processor.process_batch(
        test_files,
        progress_callback=progress_callback
    )
    
    # 显示结果
    print("\n" + "="*60)
    print("处理结果")
    print("="*60)
    
    for result in batch_result['results']:
        if result['success']:
            print(f"✓ {result['original_name']}")
            print(f"  → {result['new_name']}")
            if result['info'].get('original_title'):
                print(f"  中文标题: {result['info']['original_title']} → {result['info']['title']}")
            print(f"  质量分数: {result['quality_score']}")
        else:
            print(f"✗ {result['file_path']}")
            print(f"  错误: {result['error']}")
        print()
    
    # 显示统计
    stats = batch_result['stats']
    print("="*60)
    print("统计信息")
    print("="*60)
    print(f"总文件数: {stats['total_files']}")
    print(f"处理文件数: {stats['processed_files']}")
    print(f"成功: {stats['success']}")
    print(f"失败: {stats['failed']}")
    print(f"跳过: {stats['skipped']}")
    print(f"成功率: {stats['success_rate']*100:.1f}%")
    print(f"中文标题查询: {stats['chinese_title_queries']}")
    print(f"模板渲染: {stats['template_renders']}")
    print(f"处理时间: {stats['duration']:.2f}秒")
    
    if stats['errors']:
        print(f"\n错误详情:")
        for error in stats['errors']:
            print(f"  - {error}")


def test_progress_tracking():
    """测试进度跟踪"""
    print("\n" + "="*60)
    print("测试: 进度跟踪")
    print("="*60)
    
    from core.smart_batch_processor import ProcessingStats
    import time
    
    stats = ProcessingStats()
    
    # 模拟处理过程
    total_files = 10
    stats.start(total_files)
    
    print(f"开始处理 {total_files} 个文件...")
    
    for i in range(total_files):
        # 模拟处理时间
        time.sleep(0.1)
        
        # 随机成功/失败
        success = i % 7 != 0  # 每7个失败一个
        
        if success:
            stats.update(True)
        else:
            stats.update(False, f"文件 {i+1} 处理失败")
        
        # 显示进度
        progress = stats.get_progress()
        eta = stats.get_eta()
        print(f"进度: {progress*100:.1f}% - ETA: {eta:.1f}秒")
    
    stats.finish()
    
    # 显示最终统计
    summary = stats.get_summary()
    print("\n最终统计:")
    print(f"  总计: {summary['total_files']}")
    print(f"  成功: {summary['success']}")
    print(f"  失败: {summary['failed']}")
    print(f"  成功率: {summary['success_rate']*100:.1f}%")
    print(f"  总时间: {summary['duration']:.2f}秒")


def test_event_integration():
    """测试事件集成"""
    print("\n" + "="*60)
    print("测试: 事件集成")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    from core.events import get_event_bus
    
    # 设置事件监听
    bus = get_event_bus()
    
    def on_batch_start(event):
        print(f"📂 批量处理开始: {event.data['total_files']} 个文件")
    
    def on_batch_progress(event):
        progress = event.data['progress']
        stats = event.data['stats']
        print(f"📊 进度: {progress*100:.1f}% - 成功: {stats['success']}, 失败: {stats['failed']}")
    
    def on_batch_complete(event):
        stats = event.data['stats']
        print(f"✅ 批量处理完成!")
        print(f"   成功率: {stats['success_rate']*100:.1f}%")
        print(f"   处理时间: {stats['duration']:.2f}秒")
    
    bus.on('batch.process.start', on_batch_start)
    bus.on('batch.process.progress', on_batch_progress)
    bus.on('batch.process.complete', on_batch_complete)
    
    # 创建处理器并处理文件
    processor = SmartBatchProcessor()
    test_files = [
        "The.Wandering.Earth.2019.1080p.BluRay.x264.AAC.mkv",
        "流浪地球2.2023.2160p.WEB-DL.H265.DTS-HD.mkv",
    ]
    
    processor.process_batch(test_files)


def demo_template_usage():
    """演示模板使用"""
    print("\n" + "="*60)
    print("演示: 模板使用")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    
    processor = SmartBatchProcessor()
    test_file = "The.Matrix.1999.1080p.BluRay.x264.DTS.mkv"
    
    # 测试不同模板
    templates = [
        'movie_default',
        'movie_simple', 
        'movie_detailed',
        'nas_movie',
        'plex_movie'
    ]
    
    print(f"文件: {test_file}")
    print("\n不同模板效果:")
    
    for template in templates:
        result = processor._process_single_file(test_file, template)
        if result['success']:
            print(f"  {template:15}: {result['new_name']}")
        else:
            print(f"  {template:15}: 错误 - {result['error']}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("智能批量处理器测试套件")
    print("="*60)
    
    try:
        test_smart_batch_processor()
        test_progress_tracking()
        test_event_integration()
        demo_template_usage()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成!")
        print("="*60)
        
        print("\n新功能特点:")
        print("✓ 智能批量处理 - 借鉴 media-renamer-2 设计")
        print("✓ 实时进度跟踪 - 进度、ETA、统计信息")
        print("✓ 事件驱动架构 - 与现有事件系统集成")
        print("✓ 详细统计信息 - 成功率、处理时间、错误详情")
        print("✓ 中文标题查询 - 自动转换英文标题")
        print("✓ 模板引擎集成 - 灵活的命名方式")
        print("✓ 无外部依赖 - 保持简单")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
