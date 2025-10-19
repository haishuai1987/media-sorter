#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenList API 封装
用于通过 OpenList 服务访问 115 网盘
API文档: https://doc.oplist.org/ecosystem/official_APIpage
"""

import requests
import time
import json
from typing import Optional, Tuple, Dict, List, Any


class OpenListAPI:
    """OpenList API 封装类"""
    
    # OpenList API 基础URL
    # 根据文档: https://doc.oplist.org/ecosystem/official_APIpage
    BASE_URL = 'https://api.oplist.org.cn/api/v1'
    
    # 文件列表缓存（5分钟TTL）
    _file_cache = {}
    _cache_ttl = 300  # 5分钟
    
    def __init__(self, access_token: str, refresh_token: str = None):
        """初始化 OpenList API
        
        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌（可选）
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.session = self._create_session()
    
    def _create_session(self):
        """创建 HTTP 会话"""
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'MediaSorter/1.0'
        })
        return session
    
    def _handle_response(self, response: requests.Response) -> Tuple[Optional[Dict], Optional[str]]:
        """处理 API 响应
        
        Args:
            response: requests 响应对象
        
        Returns:
            (data, error)
        """
        try:
            if response.status_code == 200:
                data = response.json()
                # OpenList API 通常返回 {code: 0, message: "success", data: {...}}
                if data.get('code') == 0:
                    return data.get('data'), None
                else:
                    error_msg = data.get('message', '未知错误')
                    return None, error_msg
            elif response.status_code == 401:
                return None, 'Token已过期，请重新授权'
            elif response.status_code == 403:
                return None, '权限不足'
            elif response.status_code == 404:
                return None, '资源不存在'
            else:
                return None, f'HTTP错误: {response.status_code}'
        except Exception as e:
            return None, f'解析响应失败: {str(e)}'
    
    def verify_token(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """验证 Token 有效性并获取用户信息
        
        Returns:
            (success, user_info, error)
        """
        try:
            # 根据 OpenList 文档，使用 /user 端点
            url = f'{self.BASE_URL}/user'
            print(f"[OpenList API] 验证Token: {url}")
            
            response = self.session.get(url, timeout=10)
            data, error = self._handle_response(response)
            
            if error:
                return False, None, error
            
            # 提取用户信息
            user_info = {
                'user_id': data.get('user_id', ''),
                'username': data.get('user_name', ''),
                'space_used': data.get('space_info', {}).get('used', 0),
                'space_total': data.get('space_info', {}).get('total', 0)
            }
            
            print(f"[OpenList API] Token验证成功: {user_info.get('username')}")
            return True, user_info, None
            
        except Exception as e:
            print(f"[OpenList API] 验证Token异常: {str(e)}")
            return False, None, str(e)
    
    def list_files(self, folder_id: str = '0', offset: int = 0, limit: int = 1000, 
                   use_cache: bool = True) -> Tuple[Optional[Dict], Optional[str]]:
        """列出文件夹内容
        
        Args:
            folder_id: 文件夹ID，'0'表示根目录
            offset: 偏移量
            limit: 返回数量限制
            use_cache: 是否使用缓存
        
        Returns:
            (result, error)
            result包含: files, count, folder_id
        """
        try:
            # 检查缓存
            cache_key = f"{folder_id}_{offset}_{limit}"
            if use_cache and cache_key in self._file_cache:
                cached_data, cached_time = self._file_cache[cache_key]
                if time.time() - cached_time < self._cache_ttl:
                    return cached_data, None
            
            # 根据 OpenList 文档，使用 /files 端点
            url = f'{self.BASE_URL}/files'
            params = {
                'cid': folder_id,
                'offset': offset,
                'limit': limit,
                'show_dir': 1
            }
            
            print(f"[OpenList API] 请求文件列表: folder_id={folder_id}")
            response = self.session.get(url, params=params, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 获取文件列表失败: {error}")
                return None, error
            
            # 转换为统一格式
            files = []
            for item in data.get('data', []):
                file_info = {
                    'fid': item.get('fid', item.get('cid', '')),
                    'cid': item.get('cid', ''),
                    'name': item.get('n', item.get('name', '')),
                    'size': item.get('s', item.get('size', 0)),
                    'is_dir': bool(item.get('is_dir', False)),
                    'time': item.get('t', item.get('time', '')),
                    'pick_code': item.get('pc', ''),
                    'sha1': item.get('sha', ''),
                    'file_count': item.get('fc', 0)
                }
                files.append(file_info)
            
            result = {
                'files': files,
                'count': data.get('count', len(files)),
                'folder_id': folder_id,
                'offset': offset,
                'limit': limit
            }
            
            # 缓存结果
            if use_cache:
                self._file_cache[cache_key] = (result, time.time())
            
            print(f"[OpenList API] 获取到 {len(files)} 个文件")
            return result, None
            
        except Exception as e:
            print(f"[OpenList API] 列出文件异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    def clear_cache(self):
        """清除文件列表缓存"""
        self._file_cache.clear()
    
    def rename_file(self, file_id: str, new_name: str) -> Tuple[bool, Optional[str]]:
        """重命名文件或文件夹
        
        Args:
            file_id: 文件ID
            new_name: 新文件名
        
        Returns:
            (success, error)
        """
        try:
            url = f'{self.BASE_URL}/files/rename'
            payload = {
                'fid': file_id,
                'name': new_name
            }
            
            print(f"[OpenList API] 重命名文件: {file_id} -> {new_name}")
            response = self.session.post(url, json=payload, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 重命名失败: {error}")
                return False, error
            
            self.clear_cache()
            print(f"[OpenList API] 重命名成功")
            return True, None
            
        except Exception as e:
            print(f"[OpenList API] 重命名异常: {str(e)}")
            return False, str(e)
    
    def move_file(self, file_ids: List[str], target_folder_id: str) -> Tuple[bool, Optional[str]]:
        """移动文件到指定文件夹
        
        Args:
            file_ids: 文件ID列表
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success, error)
        """
        try:
            # 确保file_ids是列表
            if isinstance(file_ids, str):
                file_ids = [file_ids]
            
            url = f'{self.BASE_URL}/files/move'
            payload = {
                'fids': file_ids,
                'pid': target_folder_id
            }
            
            print(f"[OpenList API] 移动文件: {len(file_ids)}个 -> {target_folder_id}")
            response = self.session.post(url, json=payload, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 移动失败: {error}")
                return False, error
            
            self.clear_cache()
            print(f"[OpenList API] 移动成功")
            return True, None
            
        except Exception as e:
            print(f"[OpenList API] 移动异常: {str(e)}")
            return False, str(e)
    
    def delete_file(self, file_ids: List[str]) -> Tuple[bool, Optional[str]]:
        """删除文件或文件夹
        
        Args:
            file_ids: 文件ID列表
        
        Returns:
            (success, error)
        """
        try:
            # 确保file_ids是列表
            if isinstance(file_ids, str):
                file_ids = [file_ids]
            
            url = f'{self.BASE_URL}/files/delete'
            payload = {
                'fids': file_ids
            }
            
            print(f"[OpenList API] 删除文件: {len(file_ids)}个")
            response = self.session.post(url, json=payload, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 删除失败: {error}")
                return False, error
            
            self.clear_cache()
            print(f"[OpenList API] 删除成功")
            return True, None
            
        except Exception as e:
            print(f"[OpenList API] 删除异常: {str(e)}")
            return False, str(e)
    
    def create_folder(self, parent_id: str, folder_name: str) -> Tuple[Optional[str], Optional[str]]:
        """创建文件夹
        
        Args:
            parent_id: 父文件夹ID
            folder_name: 新文件夹名称
        
        Returns:
            (folder_id, error)
        """
        try:
            url = f'{self.BASE_URL}/files/mkdir'
            payload = {
                'pid': parent_id,
                'cname': folder_name
            }
            
            print(f"[OpenList API] 创建文件夹: {folder_name} in {parent_id}")
            response = self.session.post(url, json=payload, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 创建文件夹失败: {error}")
                return None, error
            
            folder_id = data.get('cid', data.get('id', ''))
            self.clear_cache()
            print(f"[OpenList API] 创建文件夹成功: {folder_id}")
            return folder_id, None
            
        except Exception as e:
            print(f"[OpenList API] 创建文件夹异常: {str(e)}")
            return None, str(e)
    
    def batch_rename(self, rename_map: Dict[str, str]) -> Tuple[int, List[str], Optional[str]]:
        """批量重命名文件
        
        Args:
            rename_map: {file_id: new_name} 字典
        
        Returns:
            (success_count, failed_ids, error)
        """
        try:
            if len(rename_map) > 50:
                return 0, list(rename_map.keys()), "批量操作最多支持50个文件"
            
            url = f'{self.BASE_URL}/115cloud/files/batch_rename'
            payload = {
                'files': [{'fid': fid, 'name': name} for fid, name in rename_map.items()]
            }
            
            print(f"[OpenList API] 批量重命名: {len(rename_map)}个文件")
            response = self.session.post(url, json=payload, timeout=30)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 批量重命名失败: {error}")
                return 0, list(rename_map.keys()), error
            
            self.clear_cache()
            print(f"[OpenList API] 批量重命名成功")
            return len(rename_map), [], None
            
        except Exception as e:
            print(f"[OpenList API] 批量重命名异常: {str(e)}")
            return 0, list(rename_map.keys()), str(e)
    
    def batch_move(self, file_ids: List[str], target_folder_id: str) -> Tuple[int, List[str], Optional[str]]:
        """批量移动文件
        
        Args:
            file_ids: 文件ID列表
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success_count, failed_ids, error)
        """
        try:
            if len(file_ids) > 50:
                return 0, file_ids, "批量操作最多支持50个文件"
            
            success, error = self.move_file(file_ids, target_folder_id)
            if success:
                return len(file_ids), [], None
            else:
                return 0, file_ids, error
                
        except Exception as e:
            print(f"[OpenList API] 批量移动异常: {str(e)}")
            return 0, file_ids, str(e)
    
    def refresh_access_token(self) -> Tuple[bool, Optional[str]]:
        """刷新访问令牌
        
        Returns:
            (success, error)
        """
        try:
            if not self.refresh_token:
                return False, "未提供刷新令牌"
            
            url = f'{self.BASE_URL}/auth/refresh'
            payload = {
                'refresh_token': self.refresh_token
            }
            
            print(f"[OpenList API] 刷新访问令牌")
            response = self.session.post(url, json=payload, timeout=10)
            data, error = self._handle_response(response)
            
            if error:
                print(f"[OpenList API] 刷新令牌失败: {error}")
                return False, error
            
            # 更新令牌
            self.access_token = data.get('access_token', '')
            self.refresh_token = data.get('refresh_token', self.refresh_token)
            
            # 更新session
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            print(f"[OpenList API] 刷新令牌成功")
            return True, None
            
        except Exception as e:
            print(f"[OpenList API] 刷新令牌异常: {str(e)}")
            return False, str(e)


# 兼容性包装器：使 OpenListAPI 可以替代 Cloud115API
class Cloud115APIWrapper:
    """Cloud115API 兼容性包装器
    
    使用 OpenList API 但保持与原 Cloud115API 相同的接口
    """
    
    def __init__(self, access_token: str, refresh_token: str = None):
        """初始化包装器
        
        Args:
            access_token: OpenList 访问令牌
            refresh_token: OpenList 刷新令牌
        """
        self.api = OpenListAPI(access_token, refresh_token)
        print("[Cloud115APIWrapper] 使用 OpenList API 后端")
    
    def verify_cookie(self):
        """验证Cookie有效性（兼容接口）"""
        return self.api.verify_token()
    
    def list_files(self, folder_id='0', offset=0, limit=1000, use_cache=True):
        """列出文件夹内容（兼容接口）"""
        return self.api.list_files(folder_id, offset, limit, use_cache)
    
    def clear_cache(self):
        """清除缓存（兼容接口）"""
        self.api.clear_cache()
    
    def rename_file(self, file_id, new_name):
        """重命名文件（兼容接口）"""
        return self.api.rename_file(file_id, new_name)
    
    def move_file(self, file_ids, target_folder_id):
        """移动文件（兼容接口）"""
        return self.api.move_file(file_ids, target_folder_id)
    
    def delete_file(self, file_ids):
        """删除文件（兼容接口）"""
        return self.api.delete_file(file_ids)
    
    def create_folder(self, parent_id, folder_name):
        """创建文件夹（兼容接口）"""
        return self.api.create_folder(parent_id, folder_name)
    
    def batch_rename(self, rename_map):
        """批量重命名（兼容接口）"""
        return self.api.batch_rename(rename_map)
    
    def batch_move(self, file_ids, target_folder_id):
        """批量移动（兼容接口）"""
        return self.api.batch_move(file_ids, target_folder_id)
