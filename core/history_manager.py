#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录管理模块
使用 SQLite 存储处理历史
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, db_path: str = "data/history.db"):
        """
        初始化历史记录管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                new_name TEXT,
                status TEXT NOT NULL,
                quality_score INTEGER,
                file_type TEXT,
                year INTEGER,
                season INTEGER,
                episode INTEGER,
                template TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON history(created_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status 
            ON history(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_original_name 
            ON history(original_name)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_record(self, record: Dict[str, Any]) -> int:
        """
        添加历史记录
        
        Args:
            record: 记录数据
            
        Returns:
            记录 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 提取字段
        original_name = record.get('original_name', '')
        new_name = record.get('new_name', '')
        status = 'success' if record.get('success') else 'failed'
        quality_score = record.get('quality_score')
        template = record.get('template', '')
        error_message = record.get('error', '')
        
        # 提取文件信息
        info = record.get('info', {})
        file_type = 'tv' if info.get('is_tv') else 'movie'
        year = info.get('year')
        season = info.get('season')
        episode = info.get('episode')
        
        # 存储额外元数据
        metadata = json.dumps({
            'resolution': info.get('resolution'),
            'source': info.get('source'),
            'codec': info.get('codec'),
            'audio': info.get('audio'),
            'subtitle': info.get('subtitle')
        })
        
        cursor.execute('''
            INSERT INTO history (
                original_name, new_name, status, quality_score,
                file_type, year, season, episode, template,
                error_message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            original_name, new_name, status, quality_score,
            file_type, year, season, episode, template,
            error_message, metadata
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_records(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取历史记录
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            status: 状态过滤（success/failed）
            search: 搜索关键词
            
        Returns:
            记录列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询
        query = 'SELECT * FROM history WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if search:
            query += ' AND (original_name LIKE ? OR new_name LIKE ?)'
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            record = dict(row)
            # 解析元数据
            if record['metadata']:
                record['metadata'] = json.loads(record['metadata'])
            records.append(record)
        
        conn.close()
        return records
    
    def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单条记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            记录数据
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM history WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        
        if row:
            record = dict(row)
            if record['metadata']:
                record['metadata'] = json.loads(record['metadata'])
            conn.close()
            return record
        
        conn.close()
        return None
    
    def delete_record(self, record_id: int) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def clear_history(self, before_date: Optional[str] = None) -> int:
        """
        清空历史记录
        
        Args:
            before_date: 清空指定日期之前的记录（可选）
            
        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if before_date:
            cursor.execute(
                'DELETE FROM history WHERE created_at < ?',
                (before_date,)
            )
        else:
            cursor.execute('DELETE FROM history')
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM history')
        total = cursor.fetchone()[0]
        
        # 成功记录数
        cursor.execute('SELECT COUNT(*) FROM history WHERE status = "success"')
        success = cursor.fetchone()[0]
        
        # 失败记录数
        cursor.execute('SELECT COUNT(*) FROM history WHERE status = "failed"')
        failed = cursor.fetchone()[0]
        
        # 今天的记录数
        cursor.execute('''
            SELECT COUNT(*) FROM history 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today = cursor.fetchone()[0]
        
        # 本周的记录数
        cursor.execute('''
            SELECT COUNT(*) FROM history 
            WHERE DATE(created_at) >= DATE('now', '-7 days')
        ''')
        this_week = cursor.fetchone()[0]
        
        # 文件类型统计
        cursor.execute('''
            SELECT file_type, COUNT(*) as count 
            FROM history 
            GROUP BY file_type
        ''')
        file_types = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': success / total if total > 0 else 0,
            'today': today,
            'this_week': this_week,
            'file_types': file_types
        }


# 全局单例
_history_manager = None


def get_history_manager() -> HistoryManager:
    """获取历史记录管理器实例（单例模式）"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


if __name__ == '__main__':
    # 测试
    manager = get_history_manager()
    
    # 添加测试记录
    test_record = {
        'original_name': 'The.Matrix.1999.1080p.BluRay.x264.mkv',
        'new_name': 'The Matrix (1999).mkv',
        'success': True,
        'quality_score': 95,
        'template': 'movie_default',
        'info': {
            'is_tv': False,
            'year': 1999,
            'resolution': '1080p',
            'source': 'BluRay',
            'codec': 'x264'
        }
    }
    
    record_id = manager.add_record(test_record)
    print(f"添加记录 ID: {record_id}")
    
    # 获取记录
    records = manager.get_records(limit=10)
    print(f"\n最近 10 条记录:")
    for record in records:
        print(f"  {record['id']}: {record['original_name']} -> {record['new_name']}")
    
    # 获取统计
    stats = manager.get_stats()
    print(f"\n统计信息:")
    print(f"  总记录数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']*100:.1f}%")
