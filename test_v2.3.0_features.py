#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 v2.3.0 新功能
- 队列管理
- 速率限制
- 增强的批量处理
"""

import time


def test_queue_manager():
    """测试队列管理器"""
    print("\n" + "="*60)
    print("测试 1: 队列管理器")
    print("="*60)
    
    from core.queue_manager import QueueManager, Priority
    
    # 创建管理器
    qm = QueueManager(max_workers=2)
    qm.start()
    
    # 定义测试任务
    def test_task(data):
        task_id = data['id']
        duration = data.get('duration', 1)
        print(f"  → 执行任务 {task_id} (耗时 {duration}秒)")
        time.sleep(duration)
        return f"任务 {task_id} 完成"
    
    # 提交不同优先级的任务
    print("\n提交任务:")
    print("-" * 60)
    
    qm.submit('task-low', {'id': 'LOW', 'duration': 2}, test_task, priority=Priority.LOW)
    qm.submit('task-high', {'id': 'HIGH', 'duration': 1}, test_task, priority=Priority.HIGH)
    qm.submit('task-critical', {'id': 'CRITICAL', 'duration': 1}, test_task, priority=Priority.CRITICAL)
    qm.submit('task-normal', {'id': 'NORMAL', 'duration': 1}, test_task, priority=Priority.NORMAL)
    
    # 等待任务完成
    print("\n等待任务完成...")
    time.sleep(6)
    
    # 打印统计
    qm.print_stats()
    
    # 停止管理器
    qm.stop()
    
    print("✓ 队列管理器测试完成")


def test_rate_limiter():
    """测试速率限制器"""
    print("\n" + "="*60)
    print("测试 2: 速率限制器")
    print("="*60)
    
    from core.rate_limiter import RateLimiter
    
    # 测试令牌桶
    print("\n测试 2.1: 令牌桶算法")
    print("-" * 60)
    
    limiter = RateLimiter(
        algorithm='token_bucket',
        max_requests=5,
        time_window=1.0,
        burst_size=2
    )
    
    print(f"配置: 5 请求/秒, 突发 2")
    print(f"初始状态: {limiter.get_stats()}")
    
    # 快速发送请求
    print("\n快速发送 10 个请求:")
    allowed_count = 0
    for i in range(10):
        allowed = limiter.allow()
        if allowed:
            allowed_count += 1
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status}")
    
    print(f"\n允许通过: {allowed_count}/10")
    
    # 测试滑动窗口
    print("\n\n测试 2.2: 滑动窗口算法")
    print("-" * 60)
    
    limiter2 = RateLimiter(
        algorithm='sliding_window',
        max_requests=3,
        time_window=2.0
    )
    
    print(f"配置: 3 请求/2秒")
    
    print("\n发送请求:")
    for i in range(5):
        allowed = limiter2.allow()
        stats = limiter2.get_stats()
        status = "✓" if allowed else "✗"
        print(f"  请求 {i+1}: {status} (当前: {stats['current_count']}/3)")
        time.sleep(0.5)
    
    print("\n✓ 速率限制器测试完成")


def test_enhanced_batch_processor():
    """测试增强的批量处理器"""
    print("\n" + "="*60)
    print("测试 3: 增强的批量处理器")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    
    # 测试文件列表
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Inception.2010.1080p.BluRay.x264.mkv",
        "Interstellar.2014.1080p.BluRay.x264.mkv",
        "流浪地球.2019.1080p.BluRay.x264.mkv",
    ]
    
    # 测试 3.1: 不使用队列（基准测试）
    print("\n测试 3.1: 普通批量处理（基准）")
    print("-" * 60)
    
    processor1 = SmartBatchProcessor(use_queue=False, use_rate_limit=False)
    
    start_time = time.time()
    result1 = processor1.process_batch(test_files)
    duration1 = time.time() - start_time
    
    print(f"\n结果:")
    print(f"  成功: {result1['stats']['success']}/{result1['stats']['total_files']}")
    print(f"  耗时: {duration1:.2f}秒")
    
    # 测试 3.2: 使用队列
    print("\n\n测试 3.2: 使用队列管理")
    print("-" * 60)
    
    processor2 = SmartBatchProcessor(use_queue=True, use_rate_limit=False, max_workers=2)
    
    def progress_callback(progress, current_file, result):
        print(f"  进度: {progress*100:.0f}% - {result.get('message', 'Processing...')}")
    
    start_time = time.time()
    result2 = processor2.process_batch_with_queue(test_files, progress_callback=progress_callback)
    duration2 = time.time() - start_time
    
    print(f"\n结果:")
    print(f"  成功: {result2['stats']['success']}/{result2['stats']['total_files']}")
    print(f"  耗时: {duration2:.2f}秒")
    
    if 'queue_stats' in result2['stats']:
        print(f"  队列统计: {result2['stats']['queue_stats']}")
    
    # 测试 3.3: 使用速率限制
    print("\n\n测试 3.3: 使用速率限制")
    print("-" * 60)
    
    processor3 = SmartBatchProcessor(use_queue=False, use_rate_limit=True, rate_limit=2)
    
    print("配置: 2 请求/秒")
    
    start_time = time.time()
    result3 = processor3.process_batch(test_files[:3])  # 只处理3个文件
    duration3 = time.time() - start_time
    
    print(f"\n结果:")
    print(f"  成功: {result3['stats']['success']}/{result3['stats']['total_files']}")
    print(f"  耗时: {duration3:.2f}秒")
    
    if 'rate_limit_stats' in result3['stats']:
        print(f"  速率限制统计: {result3['stats']['rate_limit_stats']}")
    
    print("\n✓ 增强的批量处理器测试完成")


def test_integration():
    """测试功能集成"""
    print("\n" + "="*60)
    print("测试 4: 功能集成")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    from core.queue_manager import Priority
    
    # 创建处理器（启用所有功能）
    processor = SmartBatchProcessor(
        use_queue=True,
        use_rate_limit=True,
        max_workers=2,
        rate_limit=3
    )
    
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Inception.2010.1080p.BluRay.x264.mkv",
        "流浪地球.2019.1080p.BluRay.x264.mkv",
    ]
    
    print("\n配置:")
    print("  - 队列管理: 启用 (2 工作线程)")
    print("  - 速率限制: 启用 (3 请求/秒)")
    
    print("\n开始处理...")
    
    def progress_callback(progress, current_file, result):
        print(f"  [{progress*100:.0f}%] {result.get('message', 'Processing...')}")
    
    start_time = time.time()
    result = processor.process_batch_with_queue(
        test_files,
        progress_callback=progress_callback,
        priority=Priority.HIGH
    )
    duration = time.time() - start_time
    
    print(f"\n最终结果:")
    print(f"  成功: {result['stats']['success']}/{result['stats']['total_files']}")
    print(f"  失败: {result['stats']['failed']}")
    print(f"  耗时: {duration:.2f}秒")
    
    # 显示详细统计
    stats = processor.get_stats()
    if 'queue_stats' in stats:
        print(f"\n队列统计:")
        for key, value in stats['queue_stats'].items():
            print(f"  {key}: {value}")
    
    if 'rate_limit_stats' in stats:
        print(f"\n速率限制统计:")
        for key, value in stats['rate_limit_stats'].items():
            print(f"  {key}: {value}")
    
    print("\n✓ 功能集成测试完成")


def test_performance_comparison():
    """性能对比测试"""
    print("\n" + "="*60)
    print("测试 5: 性能对比")
    print("="*60)
    
    from core.smart_batch_processor import SmartBatchProcessor
    
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Inception.2010.1080p.BluRay.x264.mkv",
        "Interstellar.2014.1080p.BluRay.x264.mkv",
        "流浪地球.2019.1080p.BluRay.x264.mkv",
        "权力的游戏.S01E01.1080p.BluRay.x265.mkv",
    ]
    
    results = {}
    
    # 测试 1: 普通模式
    print("\n模式 1: 普通批量处理")
    processor1 = SmartBatchProcessor(use_queue=False, use_rate_limit=False)
    start = time.time()
    result1 = processor1.process_batch(test_files)
    results['normal'] = {
        'duration': time.time() - start,
        'success': result1['stats']['success']
    }
    print(f"  耗时: {results['normal']['duration']:.2f}秒")
    
    # 测试 2: 队列模式
    print("\n模式 2: 队列管理 (2 workers)")
    processor2 = SmartBatchProcessor(use_queue=True, use_rate_limit=False, max_workers=2)
    start = time.time()
    result2 = processor2.process_batch_with_queue(test_files)
    results['queue'] = {
        'duration': time.time() - start,
        'success': result2['stats']['success']
    }
    print(f"  耗时: {results['queue']['duration']:.2f}秒")
    
    # 测试 3: 队列 + 速率限制
    print("\n模式 3: 队列 + 速率限制 (5 req/s)")
    processor3 = SmartBatchProcessor(use_queue=True, use_rate_limit=True, max_workers=2, rate_limit=5)
    start = time.time()
    result3 = processor3.process_batch_with_queue(test_files)
    results['queue_rate'] = {
        'duration': time.time() - start,
        'success': result3['stats']['success']
    }
    print(f"  耗时: {results['queue_rate']['duration']:.2f}秒")
    
    # 对比结果
    print("\n" + "="*60)
    print("性能对比总结")
    print("="*60)
    
    for mode, data in results.items():
        print(f"{mode:15}: {data['duration']:.2f}秒 (成功: {data['success']}/{len(test_files)})")
    
    print("\n✓ 性能对比测试完成")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("v2.3.0 性能优化测试套件")
    print("="*60)
    
    try:
        # 运行所有测试
        test_queue_manager()
        test_rate_limiter()
        test_enhanced_batch_processor()
        test_integration()
        test_performance_comparison()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成!")
        print("="*60)
        
        print("\nv2.3.0 新功能:")
        print("✓ 队列管理 - 优先级调度、并发控制")
        print("✓ 速率限制 - 令牌桶、滑动窗口算法")
        print("✓ 增强批量处理 - 集成队列和速率限制")
        print("✓ 性能优化 - 多线程并发处理")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
