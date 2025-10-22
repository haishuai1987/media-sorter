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
    print("\n" + "="*60)
    print("Media Renamer Web UI v2.5.0 (简化版)")
    print("="*60)
    print("地址: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
