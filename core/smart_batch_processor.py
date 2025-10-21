#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能批量处理器
借鉴 media-renamer-2 的设计，但保持简单无依赖
"""

import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path


class ProcessingStats:
    """处理统计"""
    
    def __init__(self):
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "chinese_title_queries": 0,
            "template_renders": 0,
            "start_time": None,
            "end_time": None,
            "duration": 0,
        }
        self.errors = []
    
    def start(self, total_files: int):
        """开始处理"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()
    
    def update(self, success: bool, error: str = None):
        """更新统计"""
        self.stats["processed_files"] += 1
        
        if success:
            self.stats["success"] += 1
        else:
            self.stats["failed"] += 1
            if error:
                self.errors.append(error)
    
    def skip(self):
        """跳过文件"""
        self.stats["skipped"] += 1
        self.stats["processed_files"] += 1
    
    def finish(self):
        """完成处理"""
        self.stats["end_time"] = time.time()
        if self.stats["start_time"]:
            self.stats["duration"] = self.stats["end_time"] - self.stats["start_time"]
    
    def get_progress(self) -> float:
        """获取进度（0-1）"""
        if self.stats["total_files"] == 0:
            return 0.0
        return self.stats["processed_files"] / self.stats["total_files"]
    
    def get_eta(self) -> float:
        """获取预计剩余时间（秒）"""
        if self.stats["processed_files"] == 0:
            return 0.0
        
        elapsed = time.time() - self.stats["start_time"]
        avg_time = elapsed / self.stats["processed_files"]
        remaining = self.stats["total_files"] - self.stats["processed_files"]
        
        return avg_time * remaining
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            **self.stats,
            "progress": self.get_progress(),
            "eta": self.get_eta(),
            "success_rate": self.stats["success"] / self.stats["processed_files"] if self.stats["processed_files"] > 0 else 0,
            "errors": self.errors,
        }


class SmartBatchProcessor:
    """智能批量处理器"""
    
    def __init__(self, tmdb_api_key: str = None, douban_cookie: str = None):
        from core.chinese_title_resolver import IntegratedRecognizer
        from core.template_engine import get_template_engine
        from core.events import get_event_bus, EventTypes
        
        self.recognizer = IntegratedRecognizer(tmdb_api_key, douban_cookie)
        self.template_engine = get_template_engine()
        self.event_bus = get_event_bus()
        self.stats = ProcessingStats()
        
        # 默认配置
        self.default_template = {
            'movie': 'movie_default',
            'tv': 'tv_default',
        }
    
    def process_batch(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable] = None,
        template_name: str = None
    ) -> Dict[str, Any]:
        """
        批量处理文件
        
        Args:
            file_paths: 文件路径列表
            progress_callback: 进度回调函数 callback(progress, current_file, result)
            template_name: 模板名称（可选）
            
        Returns:
            处理结果
        """
        # 初始化统计
        self.stats.start(len(file_paths))
        
        # 发布开始事件
        self.event_bus.emit('batch.process.start', {
            'total_files': len(file_paths)
        })
        
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                # 处理单个文件
                result = self._process_single_file(file_path, template_name)
                
                # 更新统计
                self.stats.update(result['success'], result.get('error'))
                
                # 记录结果
                results.append(result)
                
                # 计算进度
                progress = (i + 1) / len(file_paths)
                
                # 进度回调
                if progress_callback:
                    progress_callback(progress, file_path, result)
                
                # 发布进度事件
                self.event_bus.emit('batch.process.progress', {
                    'progress': progress,
                    'current_file': file_path,
                    'result': result,
                    'stats': self.stats.get_summary()
                })
                
            except Exception as e:
                error_msg = f"处理失败: {file_path} - {e}"
                self.stats.update(False, error_msg)
                
                results.append({
                    'file_path': file_path,
                    'success': False,
                    'error': str(e),
                    'message': error_msg
                })
                
                print(error_msg)
        
        # 完成处理
        self.stats.finish()
        
        # 发布完成事件
        self.event_bus.emit('batch.process.complete', {
            'results': results,
            'stats': self.stats.get_summary()
        })
        
        return {
            'results': results,
            'stats': self.stats.get_summary()
        }
    
    def _process_single_file(self, file_path: str, template_name: str = None) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            # 1. 识别文件（自动获取中文标题）
            print(f"识别文件: {Path(file_path).name}")
            info = self.recognizer.recognize_with_chinese_title(Path(file_path).name)
            
            # 统计中文标题查询
            if info.get('original_title'):
                self.stats.stats["chinese_title_queries"] += 1
            
            # 2. 确定模板
            if not template_name:
                template_name = self.default_template['tv'] if info['is_tv'] else self.default_template['movie']
            
            # 3. 生成新文件名
            context = {
                'title': info['title'],
                'year': info['year'],
                'season': info['season'],
                'episode': info['episode'],
                'resolution': info['resolution'],
                'video_codec': info['video_codec'],
                'audio_codec': info['audio_codec'],
                'source': info['source'],
                'ext': Path(file_path).suffix[1:],  # 移除点号
            }
            
            new_name = self.template_engine.render(template_name, context)
            self.stats.stats["template_renders"] += 1
            
            # 4. 返回结果
            return {
                'file_path': file_path,
                'success': True,
                'original_name': Path(file_path).name,
                'new_name': new_name,
                'info': info,
                'template': template_name,
                'quality_score': self.recognizer.advanced_recognizer.get_quality_score(info),
                'message': f"成功: {Path(file_path).name} → {new_name}"
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'error': str(e),
                'message': f"失败: {e}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.get_summary()


# 全局实例
_smart_batch_processor = None


def get_smart_batch_processor(tmdb_api_key: str = None, douban_cookie: str = None) -> SmartBatchProcessor:
    """获取智能批量处理器实例"""
    global _smart_batch_processor
    if _smart_batch_processor is None:
        _smart_batch_processor = SmartBatchProcessor(tmdb_api_key, douban_cookie)
    return _smart_batch_processor
