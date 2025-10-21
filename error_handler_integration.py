#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理集成示例 (v1.7.0)

展示如何在现有代码中集成错误处理模块
"""

from error_handler import (
    ErrorHandler, retry_on_error, safe_execute, ErrorRecovery
)


# ============ 示例1: 网络请求错误处理 ============

class TMDBClientExample:
    """TMDB客户端示例（带错误处理）"""
    
    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    def search_movie(self, title, year=None):
        """搜索电影（自动重试）"""
        # 原有的网络请求代码
        # 如果失败会自动重试
        pass
    
    def get_movie_details(self, movie_id):
        """获取电影详情（安全执行）"""
        success, result, error = safe_execute(
            lambda: self._fetch_movie_details(movie_id),
            default_value=None,
            operation='获取电影详情'
        )
        
        if not success:
            print(f"获取失败: {error}")
            return None
        
        return result
    
    def _fetch_movie_details(self, movie_id):
        """实际的网络请求"""
        # 原有代码
        pass


# ============ 示例2: 115网盘API错误处理 ============

class Cloud115APIExample:
    """115网盘API示例（带错误处理）"""
    
    def rename_file(self, file_id, new_name):
        """重命名文件（带错误恢复）"""
        success, result = ErrorRecovery.recover_from_network_error(
            self._do_rename,
            file_id,
            new_name
        )
        
        if not success:
            return False, "重命名失败，请稍后重试"
        
        return True, "重命名成功"
    
    def _do_rename(self, file_id, new_name):
        """实际的重命名操作"""
        # 原有代码
        pass
    
    def batch_rename(self, rename_map):
        """批量重命名（带详细错误处理）"""
        success_count = 0
        failed_files = []
        
        for file_id, new_name in rename_map.items():
            try:
                success, msg = self.rename_file(file_id, new_name)
                if success:
                    success_count += 1
                else:
                    failed_files.append((file_id, msg))
            except Exception as e:
                # 统一错误处理
                error_msg = ErrorHandler.get_friendly_message(e, '重命名文件')
                failed_files.append((file_id, error_msg))
                
                # 记录错误但继续处理其他文件
                ErrorHandler.log_error(e, f'重命名文件 {file_id}', verbose=False)
        
        return success_count, failed_files


# ============ 示例3: 文件操作错误处理 ============

class LocalOrganizerExample:
    """本地整理器示例（带错误处理）"""
    
    def scan_directory(self, path):
        """扫描目录（安全执行）"""
        success, files, error = safe_execute(
            lambda: self._scan_dir(path),
            default_value=[],
            operation=f'扫描目录 {path}'
        )
        
        if not success:
            print(f"扫描失败: {error}")
            return []
        
        return files
    
    def _scan_dir(self, path):
        """实际的扫描操作"""
        import os
        # 可能抛出 PermissionError, FileNotFoundError 等
        return os.listdir(path)
    
    def move_file(self, src, dst):
        """移动文件（带错误恢复）"""
        success, result = ErrorRecovery.recover_from_file_error(
            self._do_move,
            src,
            dst
        )
        
        if not success:
            return False, f"移动失败: {src} -> {dst}"
        
        return True, "移动成功"
    
    def _do_move(self, src, dst):
        """实际的移动操作"""
        import shutil
        shutil.move(src, dst)
        return True


# ============ 示例4: 配置加载错误处理 ============

def load_config_safe(config_file):
    """安全加载配置文件"""
    import json
    
    success, config, error = safe_execute(
        lambda: json.load(open(config_file, 'r', encoding='utf-8')),
        default_value={},
        operation='加载配置文件',
        log_error=True
    )
    
    if not success:
        print(f"使用默认配置: {error}")
        return get_default_config()
    
    return config


def get_default_config():
    """获取默认配置"""
    return {
        'tmdb_api_key': '',
        'douban_cookie': '',
    }


# ============ 示例5: 更新管理器错误处理 ============

class UpdateManagerExample:
    """更新管理器示例（带错误处理）"""
    
    @retry_on_error(max_retries=2, delay=2.0)
    def check_for_updates(self):
        """检查更新（自动重试）"""
        # Git fetch 操作
        # 网络错误会自动重试
        pass
    
    def pull_updates(self):
        """拉取更新（带详细错误处理）"""
        try:
            # 执行 git pull
            success = self._do_pull()
            
            if success:
                return True, "更新成功"
            else:
                return False, "更新失败"
                
        except Exception as e:
            # 分类错误并给出友好提示
            error_type, severity = ErrorHandler.classify_error(e)
            friendly_msg = ErrorHandler.get_friendly_message(e, '更新系统')
            
            # 根据错误类型给出建议
            if error_type.value == 'network':
                suggestion = "建议：检查网络连接或配置代理"
            elif error_type.value == 'permission':
                suggestion = "建议：检查文件权限或使用管理员权限"
            else:
                suggestion = "建议：查看日志获取详细信息"
            
            return False, f"{friendly_msg}\n{suggestion}"
    
    def _do_pull(self):
        """实际的pull操作"""
        # 原有代码
        pass


# ============ 使用示例 ============

def example_usage():
    """使用示例"""
    
    print("=== 错误处理集成示例 ===\n")
    
    # 示例1: TMDB搜索（自动重试）
    print("1. TMDB搜索（自动重试）")
    tmdb = TMDBClientExample()
    # tmdb.search_movie("肖申克的救赎", 1994)
    print("   - 网络错误会自动重试3次\n")
    
    # 示例2: 115网盘操作（错误恢复）
    print("2. 115网盘批量重命名（错误恢复）")
    cloud = Cloud115APIExample()
    # success_count, failed = cloud.batch_rename({...})
    print("   - 单个文件失败不影响其他文件\n")
    
    # 示例3: 文件操作（安全执行）
    print("3. 扫描目录（安全执行）")
    organizer = LocalOrganizerExample()
    # files = organizer.scan_directory("/path/to/dir")
    print("   - 权限错误会返回空列表而不是崩溃\n")
    
    # 示例4: 配置加载（默认值）
    print("4. 加载配置（默认值）")
    # config = load_config_safe("config.json")
    print("   - 文件不存在时使用默认配置\n")
    
    # 示例5: 系统更新（友好提示）
    print("5. 系统更新（友好提示）")
    updater = UpdateManagerExample()
    # success, msg = updater.pull_updates()
    print("   - 错误消息包含可操作的建议\n")


if __name__ == '__main__':
    example_usage()
