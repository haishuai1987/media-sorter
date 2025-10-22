#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 v2.2.0 新功能
- 环境检测
- 网络重试
- 自定义识别词
"""

def test_environment_detection():
    """测试环境检测"""
    print("\n" + "="*60)
    print("测试 1: 环境检测")
    print("="*60)
    
    from core.environment import get_environment, detect_environment, get_environment_config
    
    # 获取环境实例
    env = get_environment()
    
    # 打印环境信息
    env.print_info()
    
    # 测试快捷方法
    print("快捷方法测试:")
    print(f"  环境类型: {detect_environment()}")
    print(f"  环境配置: {get_environment_config()}")
    
    print("\n✓ 环境检测测试完成")


def test_network_retry():
    """测试网络重试"""
    print("\n" + "="*60)
    print("测试 2: 网络重试机制")
    print("="*60)
    
    from core.network_utils import retry_on_error, retry_on_network_error, test_network_connectivity
    
    # 测试 1: 基本重试
    print("\n测试 2.1: 基本重试装饰器")
    print("-" * 60)
    
    attempt_count = [0]  # 使用列表避免闭包问题
    
    @retry_on_error(max_retries=3, delay=0.5, backoff=1.5)
    def flaky_function():
        """模拟不稳定的函数"""
        attempt_count[0] += 1
        
        if attempt_count[0] < 3:
            raise ConnectionError(f"连接失败 (尝试 {attempt_count[0]})")
        
        return "成功!"
    
    try:
        result = flaky_function()
        print(f"✓ 最终结果: {result}")
        print(f"  总尝试次数: {attempt_count[0]}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试 2: 网络连接测试
    print("\n测试 2.2: 网络连接测试")
    print("-" * 60)
    
    if test_network_connectivity():
        print("✓ 网络连接正常")
    else:
        print("✗ 网络连接失败")
    
    # 测试 3: 安全 HTTP 请求
    print("\n测试 2.3: 安全 HTTP 请求")
    print("-" * 60)
    
    from core.network_utils import SafeRequests
    
    try:
        response = SafeRequests.get("https://www.baidu.com")
        print(f"✓ 请求成功: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    print("\n✓ 网络重试测试完成")


def test_custom_words():
    """测试自定义识别词"""
    print("\n" + "="*60)
    print("测试 3: 自定义识别词")
    print("="*60)
    
    from core.custom_words import CustomWords
    
    # 创建实例
    cw = CustomWords()
    
    # 显示当前识别词
    cw.print_words()
    
    # 测试应用识别词
    print("测试 3.1: 应用识别词")
    print("-" * 60)
    
    test_titles = [
        "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv",
        "Inception.2010.720p.BluRay.x264-YTS.mp4",
        "Interstellar.2014.1080p.WEB-DL.H264.AAC.mkv",
    ]
    
    for title in test_titles:
        result = cw.apply(title)
        print(f"原始: {title}")
        print(f"结果: {result}")
        if result != title:
            print("  ✓ 已应用识别词")
        print()
    
    # 测试添加识别词
    print("测试 3.2: 添加识别词")
    print("-" * 60)
    
    success = cw.add_word({
        'type': 'replace',
        'old': 'BluRay',
        'new': 'Blu-ray',
        'description': '统一蓝光格式',
        'enabled': True
    })
    
    if success:
        print("✓ 添加识别词成功")
    else:
        print("✗ 添加识别词失败")
    
    # 测试切换状态
    print("\n测试 3.3: 切换识别词状态")
    print("-" * 60)
    
    if len(cw.words) > 0:
        cw.toggle_word(0)
        print("✓ 切换状态成功")
    
    # 再次显示
    cw.print_words()
    
    print("✓ 自定义识别词测试完成")


def test_integration():
    """测试功能集成"""
    print("\n" + "="*60)
    print("测试 4: 功能集成")
    print("="*60)
    
    from core.environment import get_environment
    from core.custom_words import get_custom_words
    from core.network_utils import SafeRequests
    
    # 1. 获取环境配置
    env = get_environment()
    print(f"\n当前环境: {env.type}")
    print(f"监听地址: {env.config['host']}:{env.config['port']}")
    
    # 2. 应用自定义识别词
    cw = get_custom_words()
    test_title = "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv"
    cleaned_title = cw.apply(test_title)
    print(f"\n标题清理:")
    print(f"  原始: {test_title}")
    print(f"  清理: {cleaned_title}")
    
    # 3. 测试网络请求
    print(f"\n网络请求测试:")
    try:
        response = SafeRequests.head("https://www.baidu.com", timeout=5)
        print(f"  ✓ 网络正常 ({response.status_code})")
    except:
        print(f"  ✗ 网络异常")
    
    print("\n✓ 功能集成测试完成")


def test_with_existing_features():
    """测试与现有功能的集成"""
    print("\n" + "="*60)
    print("测试 5: 与现有功能集成")
    print("="*60)
    
    try:
        from core.chinese_title_resolver import IntegratedRecognizer
        from core.custom_words import get_custom_words
        
        # 创建识别器
        recognizer = IntegratedRecognizer()
        cw = get_custom_words()
        
        # 测试文件
        test_files = [
            "The.Matrix.1999.1080p.BluRay.x264.DTS-RARBG.mkv",
            "流浪地球.2019.1080p.BluRay.x264.AAC.mkv",
        ]
        
        print("\n集成测试:")
        print("-" * 60)
        
        for filename in test_files:
            # 1. 先应用自定义识别词
            cleaned = cw.apply(filename)
            
            # 2. 再进行识别
            info = recognizer.recognize_with_chinese_title(cleaned)
            
            print(f"\n文件: {filename}")
            if cleaned != filename:
                print(f"清理: {cleaned}")
            print(f"标题: {info['title']}")
            print(f"年份: {info['year']}")
            print(f"分辨率: {info['resolution']}")
        
        print("\n✓ 与现有功能集成测试完成")
        
    except ImportError as e:
        print(f"⚠ 跳过集成测试（缺少依赖）: {e}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("v2.2.0 新功能测试套件")
    print("="*60)
    
    try:
        # 运行所有测试
        test_environment_detection()
        test_network_retry()
        test_custom_words()
        test_integration()
        test_with_existing_features()
        
        print("\n" + "="*60)
        print("🎉 所有测试完成!")
        print("="*60)
        
        print("\nv2.2.0 新功能:")
        print("✓ 环境自动检测 - 自动适配本地/云/Docker环境")
        print("✓ 网络重试机制 - 提升网络操作稳定性")
        print("✓ 自定义识别词 - 灵活的标题清理规则")
        print("✓ 功能集成 - 与现有功能无缝集成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
