#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Renamer - 命令行工具
Version: 2.4.0
"""

import sys
import argparse
from pathlib import Path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Media Renamer - 智能媒体文件整理工具 v2.4.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 处理单个文件
  python media-renamer.py process "The.Matrix.1999.1080p.mkv"
  
  # 批量处理目录
  python media-renamer.py batch /path/to/movies
  
  # 查看版本
  python media-renamer.py version
  
  # 运行测试
  python media-renamer.py test
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # process 命令
    process_parser = subparsers.add_parser('process', help='处理单个文件')
    process_parser.add_argument('file', help='文件路径')
    process_parser.add_argument('--template', help='模板名称', default='movie_default')
    process_parser.add_argument('--dry-run', action='store_true', help='预览模式（不实际重命名）')
    
    # batch 命令
    batch_parser = subparsers.add_parser('batch', help='批量处理目录')
    batch_parser.add_argument('directory', help='目录路径')
    batch_parser.add_argument('--template', help='模板名称')
    batch_parser.add_argument('--workers', type=int, default=4, help='工作线程数')
    batch_parser.add_argument('--rate-limit', type=int, default=0, help='速率限制（请求/秒）')
    batch_parser.add_argument('--dry-run', action='store_true', help='预览模式')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='设置配置项')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='运行测试')
    test_parser.add_argument('--version', help='测试版本', choices=['2.2.0', '2.3.0', '2.4.0'])
    
    # version 命令
    version_parser = subparsers.add_parser('version', help='显示版本信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'process':
        process_file(args)
    elif args.command == 'batch':
        batch_process(args)
    elif args.command == 'config':
        manage_config(args)
    elif args.command == 'test':
        run_tests(args)
    elif args.command == 'version':
        show_version()


def process_file(args):
    """处理单个文件"""
    from core.smart_batch_processor import SmartBatchProcessor
    
    print(f"\n处理文件: {args.file}")
    print("-" * 60)
    
    processor = SmartBatchProcessor()
    
    result = processor.process_batch(
        [args.file],
        template_name=args.template
    )
    
    if result['results']:
        r = result['results'][0]
        if r['success']:
            print(f"✓ 成功")
            print(f"  原始: {r['original_name']}")
            print(f"  新名: {r['new_name']}")
            
            if args.dry_run:
                print("\n  [预览模式] 未实际重命名")
        else:
            print(f"✗ 失败: {r['error']}")


def batch_process(args):
    """批量处理目录"""
    from core.smart_batch_processor import SmartBatchProcessor
    import os
    
    directory = Path(args.directory)
    
    if not directory.exists():
        print(f"✗ 目录不存在: {directory}")
        return
    
    # 查找视频文件
    video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v']
    files = []
    
    for ext in video_extensions:
        files.extend(directory.glob(f'**/*{ext}'))
    
    if not files:
        print(f"✗ 未找到视频文件")
        return
    
    print(f"\n找到 {len(files)} 个视频文件")
    print("-" * 60)
    
    # 创建处理器
    use_queue = len(files) > 10
    use_rate_limit = args.rate_limit > 0
    
    processor = SmartBatchProcessor(
        use_queue=use_queue,
        use_rate_limit=use_rate_limit,
        max_workers=args.workers,
        rate_limit=args.rate_limit if use_rate_limit else 10
    )
    
    # 进度回调
    def progress_callback(progress, current_file, result):
        print(f"[{progress*100:.0f}%] {result.get('message', 'Processing...')}")
    
    # 批量处理
    if use_queue:
        result = processor.process_batch_with_queue(
            [str(f) for f in files],
            progress_callback=progress_callback,
            template_name=args.template
        )
    else:
        result = processor.process_batch(
            [str(f) for f in files],
            progress_callback=progress_callback,
            template_name=args.template
        )
    
    # 显示结果
    print("\n" + "=" * 60)
    print("处理完成")
    print("=" * 60)
    print(f"总计: {result['stats']['total_files']}")
    print(f"成功: {result['stats']['success']}")
    print(f"失败: {result['stats']['failed']}")
    print(f"成功率: {result['stats']['success_rate']*100:.1f}%")
    print(f"耗时: {result['stats']['duration']:.2f}秒")
    
    if args.dry_run:
        print("\n[预览模式] 未实际重命名")


def manage_config(args):
    """配置管理"""
    from core.environment import get_environment
    
    if args.show:
        env = get_environment()
        env.print_info()
    elif args.set:
        key, value = args.set
        print(f"设置配置: {key} = {value}")
        # TODO: 实现配置设置
    else:
        print("请使用 --show 或 --set 参数")


def run_tests(args):
    """运行测试"""
    import subprocess
    
    if args.version:
        test_file = f"test_v{args.version}_features.py"
    else:
        test_file = "test_v2.4.0_features.py"
    
    print(f"\n运行测试: {test_file}")
    print("=" * 60)
    
    try:
        subprocess.run([sys.executable, test_file], check=True)
    except subprocess.CalledProcessError:
        print("\n✗ 测试失败")
        sys.exit(1)


def show_version():
    """显示版本信息"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              Media Renamer v2.4.0                        ║
║                                                          ║
║  智能媒体文件整理工具                                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

核心功能:
  ✓ 智能识别 - 自动识别电影/剧集信息
  ✓ 中文标题 - 自动查询中文标题
  ✓ 中文数字 - 自动转换中文数字
  ✓ 批量处理 - 高效的批量处理
  ✓ 队列管理 - 智能任务调度
  ✓ 速率限制 - 保护外部服务

版本历史:
  v2.4.0 - 功能增强（中文数字转换）
  v2.3.0 - 性能优化（队列管理、速率限制）
  v2.2.0 - 基础增强（环境检测、网络重试）
  v2.1.0 - 核心功能（识别器、模板引擎）

项目地址:
  https://github.com/haishuai1987/media-sorter

许可证: MIT
作者: haishuai1987
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
