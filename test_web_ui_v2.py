#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Web UI v2.5.0
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8090"


def test_api_info():
    """测试系统信息接口"""
    print("\n=== 测试系统信息接口 ===")
    response = requests.get(f"{BASE_URL}/api/info")
    data = response.json()
    
    assert data['success'], "API 调用失败"
    print(f"✓ 版本: {data['data']['version']}")
    print(f"✓ 环境: {data['data']['environment']}")
    print(f"✓ 功能: {', '.join(data['data']['features'].keys())}")


def test_api_recognize():
    """测试文件识别接口"""
    print("\n=== 测试文件识别接口 ===")
    
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "权力的游戏.第一季.第一集.1080p.mkv",
        "Inception.2010.1080p.BluRay.x264.mkv"
    ]
    
    for filename in test_files:
        response = requests.post(
            f"{BASE_URL}/api/recognize",
            json={"filename": filename}
        )
        data = response.json()
        
        assert data['success'], f"识别失败: {filename}"
        info = data['data']
        print(f"\n文件: {filename}")
        print(f"  标题: {info.get('title', 'N/A')}")
        print(f"  年份: {info.get('year', 'N/A')}")
        print(f"  类型: {'电视剧' if info.get('is_tv') else '电影'}")
        if info.get('is_tv'):
            print(f"  季: {info.get('season', 'N/A')}, 集: {info.get('episode', 'N/A')}")


def test_api_templates():
    """测试模板接口"""
    print("\n=== 测试模板接口 ===")
    response = requests.get(f"{BASE_URL}/api/templates")
    data = response.json()
    
    assert data['success'], "获取模板失败"
    templates = data['data']
    print(f"✓ 共有 {len(templates)} 个模板:")
    for name in templates.keys():
        print(f"  - {name}")


def test_api_custom_words():
    """测试自定义识别词接口"""
    print("\n=== 测试自定义识别词接口 ===")
    
    # 获取识别词列表
    response = requests.get(f"{BASE_URL}/api/custom-words")
    data = response.json()
    
    assert data['success'], "获取识别词失败"
    words = data['data']
    print(f"✓ 共有 {len(words)} 个自定义识别词")
    
    # 添加测试识别词
    test_word = {
        "type": "block",
        "pattern": "TEST_PATTERN",
        "description": "测试屏蔽词",
        "enabled": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/custom-words",
        json=test_word
    )
    data = response.json()
    
    if data['success']:
        print("✓ 添加测试识别词成功")
        
        # 获取更新后的列表
        response = requests.get(f"{BASE_URL}/api/custom-words")
        data = response.json()
        new_words = data['data']
        
        # 删除测试识别词
        if len(new_words) > len(words):
            index = len(new_words) - 1
            response = requests.delete(f"{BASE_URL}/api/custom-words/{index}")
            data = response.json()
            if data['success']:
                print("✓ 删除测试识别词成功")


def test_api_stats():
    """测试统计信息接口"""
    print("\n=== 测试统计信息接口 ===")
    response = requests.get(f"{BASE_URL}/api/stats")
    data = response.json()
    
    assert data['success'], "获取统计信息失败"
    stats = data['data']
    print(f"✓ 总处理文件: {stats.get('total_files', 0)}")
    print(f"✓ 成功处理: {stats.get('success', 0)}")
    print(f"✓ 处理失败: {stats.get('failed', 0)}")
    print(f"✓ 成功率: {stats.get('success_rate', 0) * 100:.1f}%")


def test_api_process():
    """测试批量处理接口"""
    print("\n=== 测试批量处理接口 ===")
    
    test_files = [
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Inception.2010.1080p.BluRay.x264.mkv"
    ]
    
    # 开始处理
    response = requests.post(
        f"{BASE_URL}/api/process",
        json={
            "files": test_files,
            "template": "movie_default",
            "priority": 5,
            "use_queue": True
        }
    )
    data = response.json()
    
    assert data['success'], "启动处理失败"
    print("✓ 批量处理已启动")
    
    # 轮询状态
    print("等待处理完成...")
    max_wait = 30  # 最多等待30秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/status")
        data = response.json()
        
        if data['success']:
            status = data['data']
            progress = status['progress'] * 100
            print(f"  进度: {progress:.0f}%", end='\r')
            
            if not status['is_processing']:
                print("\n✓ 处理完成")
                results = status['results']
                print(f"  成功: {sum(1 for r in results if r.get('success'))}/{len(results)}")
                break
        
        time.sleep(1)
    else:
        print("\n⚠ 等待超时")


def main():
    """运行所有测试"""
    print("="*60)
    print("Media Renamer Web UI v2.5.0 - API 测试")
    print("="*60)
    
    try:
        test_api_info()
        test_api_recognize()
        test_api_templates()
        test_api_custom_words()
        test_api_stats()
        test_api_process()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
