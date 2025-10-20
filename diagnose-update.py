#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web更新功能诊断工具
用于排查本地服务器Web更新失败的问题
"""

import os
import sys
import subprocess
import json

def check_git_status():
    """检查Git状态"""
    print("=" * 60)
    print("1. 检查Git仓库状态")
    print("=" * 60)
    
    if not os.path.exists('.git'):
        print("❌ 错误：当前目录不是Git仓库")
        print("   解决方案：请在项目根目录运行此脚本")
        return False
    
    print("✅ Git仓库存在")
    
    # 检查是否有未提交的修改
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  警告：检测到未提交的修改")
                print(result.stdout)
                print("   这可能会阻止更新")
            else:
                print("✅ 工作目录干净，无未提交修改")
        else:
            print(f"❌ Git命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 检查Git状态失败: {e}")
        return False
    
    # 检查远程仓库
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("\n远程仓库配置:")
            print(result.stdout)
        else:
            print(f"❌ 无法获取远程仓库信息: {result.stderr}")
    except Exception as e:
        print(f"❌ 检查远程仓库失败: {e}")
    
    return True

def check_network():
    """检查网络连接"""
    print("\n" + "=" * 60)
    print("2. 检查网络连接")
    print("=" * 60)
    
    # 测试GitHub连接
    try:
        result = subprocess.run(
            ['git', 'ls-remote', '--heads', 'origin'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ 可以连接到GitHub远程仓库")
            return True
        else:
            print(f"❌ 无法连接到GitHub: {result.stderr}")
            print("\n可能的原因:")
            print("  1. 网络连接问题")
            print("  2. 需要配置代理")
            print("  3. GitHub访问受限")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 连接超时（30秒）")
        print("   建议：配置代理或检查网络")
        return False
    except Exception as e:
        print(f"❌ 网络检查失败: {e}")
        return False

def check_config():
    """检查配置文件"""
    print("\n" + "=" * 60)
    print("3. 检查配置文件")
    print("=" * 60)
    
    config_file = os.path.expanduser('~/.media-renamer/config.json')
    
    if not os.path.exists(config_file):
        print(f"⚠️  配置文件不存在: {config_file}")
        print("   这是正常的，将使用默认配置")
        return True
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 配置文件存在: {config_file}")
        
        # 检查更新相关配置
        update_proxy = config.get('update_proxy', '')
        update_proxy_enabled = config.get('update_proxy_enabled', False)
        
        if update_proxy_enabled and update_proxy:
            print(f"   更新代理已启用: {update_proxy}")
        else:
            print("   更新代理未启用（直连GitHub）")
        
        return True
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False

def check_permissions():
    """检查文件权限"""
    print("\n" + "=" * 60)
    print("4. 检查文件权限")
    print("=" * 60)
    
    # 检查当前目录是否可写
    if os.access('.', os.W_OK):
        print("✅ 当前目录可写")
    else:
        print("❌ 当前目录不可写")
        print("   解决方案：检查目录权限")
        return False
    
    # 检查app.py是否可读
    if os.path.exists('app.py'):
        if os.access('app.py', os.R_OK):
            print("✅ app.py可读")
        else:
            print("❌ app.py不可读")
            return False
    else:
        print("❌ app.py不存在")
        return False
    
    return True

def test_update_command():
    """测试更新命令"""
    print("\n" + "=" * 60)
    print("5. 测试更新命令（模拟）")
    print("=" * 60)
    
    print("测试 git fetch...")
    try:
        result = subprocess.run(
            ['git', 'fetch', 'origin', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ git fetch 测试成功")
        else:
            print(f"❌ git fetch 测试失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ git fetch 测试失败: {e}")
        return False
    
    return True

def provide_solutions():
    """提供解决方案"""
    print("\n" + "=" * 60)
    print("常见问题解决方案")
    print("=" * 60)
    
    print("""
1. 如果无法连接GitHub:
   - 在Web界面的"设置"中配置代理
   - 代理地址示例: http://127.0.0.1:7890
   - 勾选"启用更新代理"

2. 如果有未提交的修改:
   - 使用"强制更新"功能（会重置本地修改）
   - 或手动提交/放弃修改后再更新

3. 如果权限不足:
   - Windows: 以管理员身份运行
   - Linux/Mac: 使用 sudo 或检查目录权限

4. 如果仍然失败:
   - 查看浏览器控制台（F12）的错误信息
   - 查看服务器日志
   - 手动执行: git pull origin main
""")

def main():
    """主函数"""
    print("媒体库文件管理器 - Web更新诊断工具")
    print("=" * 60)
    
    # 检查是否在项目根目录
    if not os.path.exists('app.py'):
        print("❌ 错误：请在项目根目录运行此脚本")
        print(f"   当前目录: {os.getcwd()}")
        sys.exit(1)
    
    results = []
    
    # 执行各项检查
    results.append(("Git仓库", check_git_status()))
    results.append(("网络连接", check_network()))
    results.append(("配置文件", check_config()))
    results.append(("文件权限", check_permissions()))
    results.append(("更新命令", test_update_command()))
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ 所有检查通过！Web更新功能应该可以正常工作。")
        print("   如果仍然失败，请提供具体的错误信息。")
    else:
        print("\n❌ 发现问题，请参考上面的解决方案。")
        provide_solutions()

if __name__ == '__main__':
    main()
