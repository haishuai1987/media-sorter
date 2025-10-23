#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Renamer Web UI - v3.0.0
下一代 Web 管理界面 - 支持多用户和认证
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
from pathlib import Path
from datetime import datetime
import threading
import time

# 导入核心模块
from core.smart_batch_processor import SmartBatchProcessor
from core.chinese_title_resolver import IntegratedRecognizer
from core.template_engine import get_template_engine
from core.custom_words import get_custom_words
from core.environment import get_environment
from core.queue_manager import get_queue_manager, Priority
from core.events import get_event_bus
from core.history_manager import get_history_manager
from core.config_manager import get_config_manager

# v3.0.0 新增：认证和数据库
from core.models import db, init_db
from core.auth import init_auth, login_required_api, admin_required
from routes.auth import auth_bp

# v3.0.0 新增：异步任务
from core.celery_app import init_celery
from routes.tasks import tasks_bp

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/media_renamer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

# 创建 SocketIO 实例
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
processor = None
recognizer = None
template_engine = None
custom_words = None
event_bus = None
processing_status = {
    'is_processing': False,
    'current_file': '',
    'progress': 0,
    'total_files': 0,
    'processed_files': 0,
    'results': []
}
status_lock = threading.Lock()


def init_app():
    """初始化应用"""
    global processor, recognizer, template_engine, custom_words, event_bus
    
    # v3.0.0: 初始化数据库和认证
    init_db(app)
    init_auth(app)
    
    # v3.0.0: 初始化 Celery
    init_celery(app)
    
    # 注册路由
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    
    # 初始化核心组件
    processor = SmartBatchProcessor(
        use_queue=True,
        use_rate_limit=True,
        max_workers=4,
        rate_limit=10
    )
    
    recognizer = IntegratedRecognizer()
    template_engine = get_template_engine()
    custom_words = get_custom_words()
    event_bus = get_event_bus()
    
    # 注册事件监听
    event_bus.on('batch.process.start', on_batch_start)
    event_bus.on('batch.process.progress', on_batch_progress)
    event_bus.on('batch.process.complete', on_batch_complete)
    
    print("✓ Web UI v3.0.0 初始化完成")
    print("✓ 数据库已初始化")
    print("✓ 认证系统已启用")
    print("✓ 异步任务系统已启用")


def on_batch_start(event):
    """批量处理开始"""
    with status_lock:
        processing_status['is_processing'] = True
        processing_status['total_files'] = event.data['total_files']
        processing_status['processed_files'] = 0
        processing_status['progress'] = 0
        processing_status['results'] = []


def on_batch_progress(event):
    """批量处理进度"""
    with status_lock:
        processing_status['progress'] = event.data['progress']
        processing_status['current_file'] = event.data['current_file']
        processing_status['processed_files'] = event.data['stats']['processed_files']
        
        # 添加结果
        if event.data['result']:
            result = event.data['result']
            processing_status['results'].append(result)
            
            # 保存到历史记录
            try:
                history_manager = get_history_manager()
                history_manager.add_record(result)
            except Exception as e:
                print(f"保存历史记录失败: {e}")


def on_batch_complete(event):
    """批量处理完成"""
    with status_lock:
        processing_status['is_processing'] = False
        processing_status['progress'] = 1.0


# ==================== 路由 ====================

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
    env = get_environment()
    
    return jsonify({
        'success': True,
        'data': {
            'version': '2.5.0',
            'environment': env.type,
            'config': env.config,
            'features': {
                'chinese_number': True,
                'queue_management': True,
                'rate_limit': True,
                'custom_words': True,
                'templates': True
            }
        }
    })


@app.route('/api/recognize', methods=['POST'])
def api_recognize():
    """识别文件"""
    try:
        data = request.json
        filename = data.get('filename', '')
        
        if not filename:
            return jsonify({'success': False, 'error': '文件名不能为空'})
        
        # 识别文件
        info = recognizer.recognize_with_chinese_title(filename)
        
        return jsonify({
            'success': True,
            'data': info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/process', methods=['POST'])
def api_process():
    """处理文件"""
    try:
        data = request.json
        files = data.get('files', [])
        template = data.get('template', 'movie_default')
        use_queue = data.get('use_queue', True)
        priority = data.get('priority', Priority.NORMAL)
        
        if not files:
            return jsonify({'success': False, 'error': '文件列表不能为空'})
        
        # 检查是否正在处理
        with status_lock:
            if processing_status['is_processing']:
                return jsonify({'success': False, 'error': '正在处理中，请稍候'})
        
        # 异步处理
        def process_files():
            total = len(files)
            
            # 发送开始处理的进度
            emit_progress(0, total, '', '开始处理...')
            
            if use_queue:
                # 使用队列处理时，逐个处理并发送进度
                for i, file in enumerate(files, 1):
                    emit_progress(i-1, total, file, f'正在处理 {i}/{total}')
                    time.sleep(0.1)  # 模拟处理时间，实际应该在处理完成后更新
                
                result = processor.process_batch_with_queue(
                    files,
                    template_name=template,
                    priority=priority
                )
            else:
                # 不使用队列时，逐个处理并发送进度
                for i, file in enumerate(files, 1):
                    emit_progress(i-1, total, file, f'正在处理 {i}/{total}')
                    time.sleep(0.1)  # 模拟处理时间
                
                result = processor.process_batch(
                    files,
                    template_name=template
                )
            
            # 发送完成进度
            emit_progress(total, total, '', '处理完成！')
        
        thread = threading.Thread(target=process_files)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '处理已开始'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/status')
def api_status():
    """获取处理状态"""
    with status_lock:
        return jsonify({
            'success': True,
            'data': processing_status.copy()
        })


@app.route('/api/templates')
def api_templates():
    """获取模板列表"""
    try:
        templates = template_engine.list_templates()
        
        return jsonify({
            'success': True,
            'data': templates
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/templates/<name>')
def api_template_detail(name):
    """获取模板详情"""
    try:
        template = template_engine.get_template(name)
        
        if template:
            return jsonify({
                'success': True,
                'data': {
                    'name': name,
                    'template': template
                }
            })
        else:
            return jsonify({'success': False, 'error': '模板不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/custom-words')
def api_custom_words_list():
    """获取自定义识别词列表"""
    try:
        words = custom_words.get_words()
        
        return jsonify({
            'success': True,
            'data': words
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/custom-words', methods=['POST'])
def api_custom_words_add():
    """添加自定义识别词"""
    try:
        data = request.json
        
        success = custom_words.add_word(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '添加成功'
            })
        else:
            return jsonify({'success': False, 'error': '添加失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/custom-words/<int:index>', methods=['DELETE'])
def api_custom_words_delete(index):
    """删除自定义识别词"""
    try:
        success = custom_words.remove_word(index)
        
        if success:
            return jsonify({
                'success': True,
                'message': '删除成功'
            })
        else:
            return jsonify({'success': False, 'error': '删除失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/custom-words/<int:index>/toggle', methods=['POST'])
def api_custom_words_toggle(index):
    """切换自定义识别词状态"""
    try:
        success = custom_words.toggle_word(index)
        
        if success:
            return jsonify({
                'success': True,
                'message': '切换成功'
            })
        else:
            return jsonify({'success': False, 'error': '切换失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    try:
        stats = processor.get_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/history')
def api_history_list():
    """获取历史记录列表"""
    try:
        history_manager = get_history_manager()
        
        # 获取查询参数
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        search = request.args.get('search')
        
        records = history_manager.get_records(
            limit=limit,
            offset=offset,
            status=status,
            search=search
        )
        
        return jsonify({
            'success': True,
            'data': records
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/history/<int:record_id>')
def api_history_detail(record_id):
    """获取历史记录详情"""
    try:
        history_manager = get_history_manager()
        record = history_manager.get_record(record_id)
        
        if record:
            return jsonify({
                'success': True,
                'data': record
            })
        else:
            return jsonify({'success': False, 'error': '记录不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/history/<int:record_id>', methods=['DELETE'])
def api_history_delete(record_id):
    """删除历史记录"""
    try:
        history_manager = get_history_manager()
        success = history_manager.delete_record(record_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '删除成功'
            })
        else:
            return jsonify({'success': False, 'error': '记录不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/history/clear', methods=['POST'])
def api_history_clear():
    """清空历史记录"""
    try:
        history_manager = get_history_manager()
        data = request.json or {}
        before_date = data.get('before_date')
        
        count = history_manager.clear_history(before_date)
        
        return jsonify({
            'success': True,
            'message': f'已删除 {count} 条记录'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/history/stats')
def api_history_stats():
    """获取历史统计"""
    try:
        history_manager = get_history_manager()
        stats = history_manager.get_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs')
def api_configs_list():
    """获取配置列表"""
    try:
        config_manager = get_config_manager()
        configs = config_manager.get_all_configs()
        
        return jsonify({
            'success': True,
            'data': configs
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/defaults')
def api_configs_defaults():
    """获取默认配置模板"""
    try:
        config_manager = get_config_manager()
        defaults = config_manager.get_default_configs()
        
        return jsonify({
            'success': True,
            'data': defaults
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs', methods=['POST'])
def api_configs_add():
    """添加配置"""
    try:
        config_manager = get_config_manager()
        data = request.json
        
        config_id = config_manager.add_config(data)
        
        return jsonify({
            'success': True,
            'data': {'id': config_id}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/<config_id>')
def api_configs_get(config_id):
    """获取配置详情"""
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config(config_id)
        
        if config:
            return jsonify({
                'success': True,
                'data': config
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/<config_id>', methods=['PUT'])
def api_configs_update(config_id):
    """更新配置"""
    try:
        config_manager = get_config_manager()
        data = request.json
        
        success = config_manager.update_config(config_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '更新成功'
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/<config_id>', methods=['DELETE'])
def api_configs_delete(config_id):
    """删除配置"""
    try:
        config_manager = get_config_manager()
        success = config_manager.delete_config(config_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '删除成功'
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/<config_id>/export')
def api_configs_export(config_id):
    """导出配置"""
    try:
        config_manager = get_config_manager()
        config_json = config_manager.export_config(config_id)
        
        if config_json:
            return jsonify({
                'success': True,
                'data': config_json
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/configs/import', methods=['POST'])
def api_configs_import():
    """导入配置"""
    try:
        config_manager = get_config_manager()
        data = request.json
        config_json = data.get('config_json', '')
        
        config_id = config_manager.import_config(config_json)
        
        if config_id:
            return jsonify({
                'success': True,
                'data': {'id': config_id}
            })
        else:
            return jsonify({'success': False, 'error': '导入失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


# ==================== WebSocket 事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端已断开')


@socketio.on('request_progress')
def handle_request_progress():
    """客户端请求进度更新"""
    with status_lock:
        emit('progress_update', processing_status.copy())


def emit_progress(current, total, current_file='', message=''):
    """发送进度更新到所有连接的客户端"""
    progress_data = {
        'current': current,
        'total': total,
        'percentage': int((current / total * 100)) if total > 0 else 0,
        'current_file': current_file,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    # 更新全局状态
    with status_lock:
        processing_status['processed_files'] = current
        processing_status['total_files'] = total
        processing_status['current_file'] = current_file
        processing_status['progress'] = progress_data['percentage']
    
    # 广播到所有客户端
    socketio.emit('progress_update', progress_data)


# ==================== 启动应用 ====================

if __name__ == '__main__':
    import argparse
    import os
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Media Renamer Web UI v2.5.0')
    parser.add_argument('--host', type=str, default=None,
                        help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None,
                        help='监听端口 (默认: 8090，可通过环境变量 PORT 设置)')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')
    args = parser.parse_args()
    
    # 初始化
    init_app()
    
    # 获取环境配置
    env = get_environment()
    
    # 优先级: 命令行参数 > 环境变量 > 默认配置
    host = args.host or os.getenv('HOST') or env.config['host']
    port = args.port or int(os.getenv('PORT', 0)) or env.config['port']
    debug_mode = args.debug or os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print("\n" + "="*60)
    print("Media Renamer Web UI v2.5.0")
    print("="*60)
    print(f"环境: {env.type}")
    print(f"监听地址: {host}:{port}")
    print(f"调试模式: {'开启' if debug_mode else '关闭'}")
    print("="*60)
    print(f"\n访问地址:")
    print(f"  本地: http://127.0.0.1:{port}")
    print(f"  局域网: http://<你的IP>:{port}")
    print("\n提示: 使用 --help 查看更多选项")
    print("="*60 + "\n")
    
    # 启动服务
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            allow_unsafe_werkzeug=True
        )
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ 错误: 端口 {port} 已被占用！")
            print(f"\n解决方案:")
            print(f"  1. 使用其他端口: python app_v2.py --port 8091")
            print(f"  2. 设置环境变量: PORT=8091 python app_v2.py")
            print(f"  3. 停止占用端口的进程")
            print(f"\n常见端口建议:")
            print(f"  - 8090 (默认)")
            print(f"  - 8091, 8092, 8093 (备选)")
            print(f"  - 9000, 9001, 9002 (备选)")
            print()
        else:
            raise
