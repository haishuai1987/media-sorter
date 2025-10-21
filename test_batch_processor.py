#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理模块测试 (v1.9.0)
"""

import time
import random
from batch_processor import (
    ProgressTracker, ConcurrentProcessor,
    CheckpointManager, RollbackManager
)


def test_progress_tracker():
    """测试进度追踪器"""
    print("\n=== 测试进度追踪器 ===")
    
    tracker = ProgressTracker(total=100)
    
    # 模拟处理
    for i in range(100):
        success = random.random() > 0.1  # 90%成功率
        tracker.update(success=success, item=f"item_{i}", error="测试错误" if not success else None)
        time.sleep(0.01)
        
        if i % 20 == 0:
            stats = tracker.get_stats()
            print(f"进度: {stats['progress']*100:.1f}% | "
                  f"完成: {stats['completed']} | "
                  f"失败: {stats['failed']} | "
                  f"ETA: {stats['eta']:.1f}秒" if stats['eta'] else "ETA: 计算中...")
    
    final_stats = tracker.get_stats()
    print(f"\n最终统计:")
    print(f"  总数: {final_stats['total']}")
    print(f"  成功: {final_stats['completed']}")
    print(f"  失败: {final_stats['failed']}")
    print(f"  成功率: {final_stats['success_rate']*100:.1f}%")
    print(f"  耗时: {final_stats['elapsed']:.2f}秒")
    
    return final_stats['failed'] < 20  # 失败少于20个算通过


def test_concurrent_processor():
    """测试并发处理器"""
    print("\n=== 测试并发处理器 ===")
    
    def process_item(item):
        """处理单个项目"""
        time.sleep(0.1)  # 模拟处理时间
        if random.random() > 0.9:  # 10%失败率
            raise Exception(f"处理失败: {item}")
        return f"processed_{item}"
    
    processor = ConcurrentProcessor(max_workers=4)
    items = [f"item_{i}" for i in range(20)]
    
    print(f"开始处理 {len(items)} 个项目（4线程）...")
    start_time = time.time()
    
    def progress_callback(stats):
        print(f"  进度: {stats['progress']*100:.0f}% | "
              f"完成: {stats['completed']} | "
              f"失败: {stats['failed']}")
    
    result = processor.process_batch(items, process_item, progress_callback)
    
    elapsed = time.time() - start_time
    stats = result['stats']
    
    print(f"\n处理完成:")
    print(f"  耗时: {elapsed:.2f}秒")
    print(f"  成功: {stats['completed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']*100:.1f}%")
    
    processor.shutdown()
    
    # 单线程对比
    print(f"\n单线程对比（预计耗时: {len(items) * 0.1:.1f}秒）")
    print(f"并发加速: {(len(items) * 0.1) / elapsed:.1f}x")
    
    return stats['completed'] > 15  # 成功超过15个算通过


def test_checkpoint_manager():
    """测试断点管理器"""
    print("\n=== 测试断点管理器 ===")
    
    manager = CheckpointManager()
    
    # 保存检查点
    operation_id = "test_op_001"
    state = {
        'processed_items': ['item_1', 'item_2', 'item_3'],
        'remaining_items': ['item_4', 'item_5'],
        'progress': 0.6
    }
    
    print(f"保存检查点: {operation_id}")
    manager.save_checkpoint(operation_id, state)
    
    # 加载检查点
    print(f"加载检查点: {operation_id}")
    loaded_state = manager.load_checkpoint(operation_id)
    
    if loaded_state:
        print(f"  已处理: {len(loaded_state['processed_items'])} 个")
        print(f"  剩余: {len(loaded_state['remaining_items'])} 个")
        print(f"  进度: {loaded_state['progress']*100:.0f}%")
    
    # 列出检查点
    checkpoints = manager.list_checkpoints()
    print(f"\n检查点列表: {len(checkpoints)} 个")
    
    # 删除检查点
    print(f"删除检查点: {operation_id}")
    manager.delete_checkpoint(operation_id)
    
    # 验证删除
    loaded_state = manager.load_checkpoint(operation_id)
    success = loaded_state is None
    
    print(f"✓ 检查点已删除" if success else "✗ 删除失败")
    
    return success


def test_rollback_manager():
    """测试回滚管理器"""
    print("\n=== 测试回滚管理器 ===")
    
    manager = RollbackManager()
    
    # 记录操作
    operation_id = "test_rollback_001"
    operation = {
        'type': 'file_move',
        'files': [
            {'from': '/path/a.txt', 'to': '/path/b.txt'},
            {'from': '/path/c.txt', 'to': '/path/d.txt'}
        ]
    }
    
    print(f"记录操作: {operation_id}")
    manager.record_operation(operation_id, operation)
    
    # 列出操作
    operations = manager.list_operations(rollback_available_only=True)
    print(f"可回滚操作: {len(operations)} 个")
    
    # 回滚操作
    def rollback_handler(op):
        print(f"  回滚类型: {op['type']}")
        print(f"  回滚文件: {len(op['files'])} 个")
        return True
    
    print(f"执行回滚: {operation_id}")
    success = manager.rollback(operation_id, rollback_handler)
    
    if success:
        print("✓ 回滚成功")
        
        # 验证不能再次回滚
        operations = manager.list_operations(rollback_available_only=True)
        print(f"可回滚操作: {len(operations)} 个（应该减少1个）")
    else:
        print("✗ 回滚失败")
    
    return success


def test_concurrent_with_checkpoint():
    """测试并发处理 + 断点续传"""
    print("\n=== 测试并发处理 + 断点续传 ===")
    
    processor = ConcurrentProcessor(max_workers=4)
    checkpoint_mgr = CheckpointManager()
    
    operation_id = "test_concurrent_checkpoint"
    items = [f"item_{i}" for i in range(50)]
    
    # 检查是否有断点
    checkpoint = checkpoint_mgr.load_checkpoint(operation_id)
    if checkpoint:
        print(f"发现断点，从 {checkpoint['progress']*100:.0f}% 处继续")
        processed = checkpoint['processed_items']
        remaining = checkpoint['remaining_items']
    else:
        print("开始新操作")
        processed = []
        remaining = items
    
    def process_item(item):
        time.sleep(0.05)
        # 模拟中断（处理到一半时）
        if len(processed) == 25 and not checkpoint:
            raise KeyboardInterrupt("模拟中断")
        return f"processed_{item}"
    
    try:
        result = processor.process_batch(remaining, process_item)
        processed.extend([r['item'] for r in result['results'] if r['success']])
        
        print(f"✓ 处理完成: {len(processed)}/{len(items)}")
        checkpoint_mgr.delete_checkpoint(operation_id)
        success = True
        
    except KeyboardInterrupt:
        print(f"⚠ 操作中断，保存断点...")
        
        # 保存断点
        state = {
            'processed_items': processed,
            'remaining_items': [item for item in items if item not in processed],
            'progress': len(processed) / len(items)
        }
        checkpoint_mgr.save_checkpoint(operation_id, state)
        print(f"  已处理: {len(processed)}/{len(items)}")
        success = False
    
    processor.shutdown()
    
    return success


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("批量处理模块测试 (v1.9.0)")
    print("=" * 60)
    
    tests = [
        ("进度追踪器", test_progress_tracker),
        ("并发处理器", test_concurrent_processor),
        ("断点管理器", test_checkpoint_manager),
        ("回滚管理器", test_rollback_manager),
        ("并发+断点", test_concurrent_with_checkpoint),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed_count}/{total_count} 通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
