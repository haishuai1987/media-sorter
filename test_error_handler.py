#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理模块测试 (v1.7.0)
"""

import time
from error_handler import (
    ErrorHandler, ErrorType, ErrorSeverity,
    retry_on_error, safe_execute, ErrorRecovery
)


def test_error_classification():
    """测试错误分类"""
    print("\n=== 测试错误分类 ===")
    
    test_cases = [
        (Exception("Connection timeout"), ErrorType.NETWORK, "网络超时"),
        (Exception("HTTP 401 Unauthorized"), ErrorType.API, "API未授权"),
        (Exception("Permission denied"), ErrorType.PERMISSION, "权限错误"),
        (Exception("File not found"), ErrorType.FILE, "文件错误"),
        (Exception("Invalid cookie format"), ErrorType.VALIDATION, "验证错误"),
    ]
    
    passed = 0
    for error, expected_type, desc in test_cases:
        error_type, severity = ErrorHandler.classify_error(error)
        if error_type == expected_type:
            print(f"✓ {desc}: {error_type.value} (严重程度: {severity.value})")
            passed += 1
        else:
            print(f"✗ {desc}: 期望 {expected_type.value}, 实际 {error_type.value}")
    
    print(f"\n通过: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_friendly_messages():
    """测试友好错误消息"""
    print("\n=== 测试友好错误消息 ===")
    
    test_cases = [
        (Exception("Connection timeout"), "网络连接超时"),
        (Exception("HTTP 401"), "Cookie已过期"),
        (Exception("HTTP 429"), "请求过于频繁"),
        (Exception("Permission denied"), "没有权限"),
        (Exception("File not found"), "文件不存在"),
    ]
    
    passed = 0
    for error, expected_keyword in test_cases:
        msg = ErrorHandler.get_friendly_message(error, "测试操作")
        if expected_keyword in msg:
            print(f"✓ {str(error)[:30]}: {msg}")
            passed += 1
        else:
            print(f"✗ {str(error)[:30]}: 未找到关键词 '{expected_keyword}'")
    
    print(f"\n通过: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_retry_mechanism():
    """测试重试机制"""
    print("\n=== 测试重试机制 ===")
    
    # 测试1: 成功重试
    print("\n测试1: 网络错误自动重试")
    attempt_count = [0]
    
    @retry_on_error(max_retries=3, delay=0.1, backoff=1.5)
    def flaky_network_call():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise Exception("Connection timeout")
        return "成功"
    
    try:
        result = flaky_network_call()
        print(f"✓ 重试成功: {result} (尝试了 {attempt_count[0]} 次)")
        test1_passed = True
    except:
        print(f"✗ 重试失败")
        test1_passed = False
    
    # 测试2: 不应重试的错误
    print("\n测试2: 不可重试的错误")
    attempt_count[0] = 0
    
    @retry_on_error(max_retries=3, delay=0.1)
    def auth_error_call():
        attempt_count[0] += 1
        raise Exception("HTTP 401 Unauthorized")
    
    try:
        auth_error_call()
        test2_passed = False
    except:
        if attempt_count[0] == 1:
            print(f"✓ 正确跳过重试 (只尝试了 {attempt_count[0]} 次)")
            test2_passed = True
        else:
            print(f"✗ 不应该重试但重试了 {attempt_count[0]} 次")
            test2_passed = False
    
    return test1_passed and test2_passed


def test_safe_execute():
    """测试安全执行"""
    print("\n=== 测试安全执行 ===")
    
    # 测试1: 成功执行
    print("\n测试1: 正常执行")
    success, result, error = safe_execute(
        lambda: 1 + 1,
        operation="加法运算"
    )
    test1_passed = success and result == 2 and error is None
    print(f"{'✓' if test1_passed else '✗'} 结果: {result}, 错误: {error}")
    
    # 测试2: 异常捕获
    print("\n测试2: 异常捕获")
    success, result, error = safe_execute(
        lambda: 1 / 0,
        default_value=-1,
        operation="除零运算",
        log_error=False
    )
    test2_passed = not success and result == -1 and error is not None
    print(f"{'✓' if test2_passed else '✗'} 成功: {success}, 结果: {result}")
    print(f"  错误消息: {error}")
    
    return test1_passed and test2_passed


def test_error_recovery():
    """测试错误恢复"""
    print("\n=== 测试错误恢复 ===")
    
    # 测试1: 网络错误恢复
    print("\n测试1: 网络错误恢复")
    attempt_count = [0]
    
    def network_op():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception("Connection timeout")
        return "网络请求成功"
    
    success, result = ErrorRecovery.recover_from_network_error(network_op)
    test1_passed = success and result == "网络请求成功"
    print(f"{'✓' if test1_passed else '✗'} 恢复成功: {result}")
    
    # 测试2: 文件错误恢复
    print("\n测试2: 文件错误恢复")
    
    def file_op():
        raise FileNotFoundError("test.txt not found")
    
    success, result = ErrorRecovery.recover_from_file_error(file_op)
    test2_passed = not success and result is None
    print(f"{'✓' if test2_passed else '✗'} 正确处理文件错误")
    
    return test1_passed and test2_passed


def test_should_retry():
    """测试重试判断"""
    print("\n=== 测试重试判断 ===")
    
    test_cases = [
        (Exception("Connection timeout"), True, "网络超时"),
        (Exception("HTTP 500"), True, "服务器错误"),
        (Exception("HTTP 401"), False, "认证错误"),
        (Exception("Permission denied"), False, "权限错误"),
        (Exception("Invalid input"), False, "验证错误"),
    ]
    
    passed = 0
    for error, should_retry, desc in test_cases:
        result = ErrorHandler.should_retry(error)
        if result == should_retry:
            print(f"✓ {desc}: {'应该重试' if should_retry else '不应重试'}")
            passed += 1
        else:
            print(f"✗ {desc}: 期望 {should_retry}, 实际 {result}")
    
    print(f"\n通过: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("错误处理模块测试 (v1.7.0)")
    print("=" * 60)
    
    tests = [
        ("错误分类", test_error_classification),
        ("友好消息", test_friendly_messages),
        ("重试机制", test_retry_mechanism),
        ("安全执行", test_safe_execute),
        ("错误恢复", test_error_recovery),
        ("重试判断", test_should_retry),
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
