#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构重构测试 (v2.0.0)
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import ConfigManager, Logger, Utils
from plugins import PluginLoader


def test_config_manager():
    """测试配置管理器"""
    print("\n=== 测试配置管理器 ===")
    
    config = ConfigManager()
    
    # 测试设置和获取
    config.set('test_key', 'test_value')
    value = config.get('test_key')
    print(f"✓ 设置/获取: {value}")
    
    # 测试嵌套键
    config.set('nested.key', 'nested_value')
    value = config.get('nested.key')
    print(f"✓ 嵌套键: {value}")
    
    # 测试默认值
    value = config.get('non_existent', 'default')
    print(f"✓ 默认值: {value}")
    
    # 测试保存和加载
    test_config_file = '.test_config.json'
    config.save(test_config_file)
    print(f"✓ 保存配置")
    
    new_config = ConfigManager(test_config_file)
    new_config.load()
    value = new_config.get('test_key')
    print(f"✓ 加载配置: {value}")
    
    # 清理
    if os.path.exists(test_config_file):
        os.remove(test_config_file)
    
    return True


def test_logger():
    """测试日志系统"""
    print("\n=== 测试日志系统 ===")
    
    logger = Logger('test_logger')
    
    logger.debug("这是调试日志")
    logger.info("这是信息日志")
    logger.warning("这是警告日志")
    logger.error("这是错误日志")
    
    print("✓ 日志系统正常")
    
    return True


def test_utils():
    """测试工具函数"""
    print("\n=== 测试工具函数 ===")
    
    # 测试文件大小格式化
    size_str = Utils.format_size(1024 * 1024 * 100)
    print(f"✓ 格式化大小: {size_str}")
    
    # 测试时间格式化
    duration_str = Utils.format_duration(3665)
    print(f"✓ 格式化时间: {duration_str}")
    
    # 测试文件名清理
    clean_name = Utils.sanitize_filename('test<>:file?.txt')
    print(f"✓ 清理文件名: {clean_name}")
    
    # 测试列表分块
    chunks = Utils.chunk_list([1, 2, 3, 4, 5, 6, 7], 3)
    print(f"✓ 列表分块: {chunks}")
    
    # 测试字典合并
    merged = Utils.merge_dicts({'a': 1}, {'b': 2}, {'c': 3})
    print(f"✓ 字典合并: {merged}")
    
    return True


def test_plugin_system():
    """测试插件系统"""
    print("\n=== 测试插件系统 ===")
    
    loader = PluginLoader()
    
    # 发现插件
    plugins = loader.discover_plugins()
    print(f"✓ 发现插件: {plugins}")
    
    # 加载示例插件
    success = loader.load_plugin('example_plugin')
    if success:
        print("✓ 加载插件成功")
    else:
        print("✗ 加载插件失败")
        return False
    
    # 获取插件
    plugin = loader.get_plugin('example_plugin')
    if plugin:
        print(f"✓ 获取插件: {plugin.name} v{plugin.version}")
        
        # 测试插件功能
        result = plugin.process("hello world")
        print(f"✓ 插件处理: {result}")
    
    # 列出插件
    plugin_list = loader.list_plugins()
    print(f"✓ 插件列表: {len(plugin_list)} 个")
    
    # 卸载插件
    success = loader.unload_plugin('example_plugin')
    if success:
        print("✓ 卸载插件成功")
    
    return True


def test_integration():
    """测试集成"""
    print("\n=== 测试集成 ===")
    
    # 配置 + 日志
    config = ConfigManager()
    config.set('log_level', 'INFO')
    
    logger = Logger(level=config.get('log_level'))
    logger.info("配置和日志集成测试")
    
    # 配置 + 插件
    config.set('max_workers', 4)
    loader = PluginLoader()
    
    print(f"✓ 最大并发数: {config.get('max_workers')}")
    print(f"✓ 插件目录: {loader.plugin_dir}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("架构重构测试 (v2.0.0)")
    print("=" * 60)
    
    tests = [
        ("配置管理器", test_config_manager),
        ("日志系统", test_logger),
        ("工具函数", test_utils),
        ("插件系统", test_plugin_system),
        ("集成测试", test_integration),
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
