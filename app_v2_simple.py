#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Renamer Web UI - v2.5.0 (简化版)
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """主页"""
    return send_from_directory('public', 'index_v2.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """静态文件"""
    return send_from_directory('public', filename)

@app.route('/api/info')
def api_info():
    """获取系统信息"""
    return jsonify({
        'success': True,
        'data': {
            'version': '2.5.0',
            'environment': 'local',
            'features': {
                'chinese_number': True,
                'queue_management': True,
                'rate_limit': True,
                'custom_words': True,
                'templates': True
            }
        }
    })

@app.route('/api/templates')
def api_templates():
    """获取模板列表"""
    return jsonify({
        'success': True,
        'data': {
            'movie_default': '{title} ({year})',
            'movie_simple': '{title}',
            'tv_default': '{title} S{season:02d}E{episode:02d}'
        }
    })

if __name__ == '__main__':
    import argparse
    import os
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Media Renamer Web UI v2.5.0 (简化版)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='监听地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=None,
                        help='监听端口 (默认: 5000，可通过环境变量 PORT 设置)')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')
    args = parser.parse_args()
    
    # 优先级: 命令行参数 > 环境变量 > 默认值
    host = args.host
    port = args.port or int(os.getenv('PORT', 5000))
    debug_mode = args.debug
    
    print("\n" + "="*60)
    print("Media Renamer Web UI v2.5.0 (简化版)")
    print("="*60)
    print(f"监听地址: {host}:{port}")
    print(f"调试模式: {'开启' if debug_mode else '关闭'}")
    print("="*60)
    print(f"\n访问地址: http://{host}:{port}")
    print("\n提示: 使用 --help 查看更多选项")
    print("="*60 + "\n")
    
    try:
        app.run(host=host, port=port, debug=debug_mode)
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ 错误: 端口 {port} 已被占用！")
            print(f"\n解决方案:")
            print(f"  1. 使用其他端口: python app_v2_simple.py --port 5001")
            print(f"  2. 设置环境变量: PORT=5001 python app_v2_simple.py")
            print(f"  3. 停止占用端口的进程")
            print()
        else:
            raise
