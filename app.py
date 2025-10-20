#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import cgi
import time
from functools import wraps

PORT = 8090  # 避免与qBittorrent(8080)冲突

# Linux/NAS优化配置
NETWORK_RETRY_COUNT = 3  # 网络操作重试次数
NETWORK_RETRY_DELAY = 2  # 重试延迟（秒）
NETWORK_OP_DELAY = 1.0   # 网络文件系统操作延迟（秒）

# 配置文件路径
CONFIG_FILE = os.path.expanduser('~/.media-renamer/config.json')

# 默认配置（用户需要在Web界面的"设置"中配置自己的API密钥）
DEFAULT_CONFIG = {
    'tmdb_api_key': '',  # 请在Web界面的"设置"中配置你的TMDB API Key
    'tmdb_proxy': '',    # 可选：如果需要代理访问TMDB，在"设置"中配置
    'tmdb_proxy_type': 'http',  # http 或 socks5
    'douban_cookie': '',  # 请在Web界面的"设置"中配置你的豆瓣Cookie
    'update_proxy': '',  # 系统更新代理地址（如：http://127.0.0.1:7890）
    'update_proxy_enabled': False,  # 是否启用更新代理
    'auto_restart_after_update': True  # 更新后是否自动重启
}

# 加载配置
def load_config():
    """加载用户配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并默认配置和用户配置
                config = DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
    except Exception as e:
        print(f"加载配置失败: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存用户配置"""
    try:
        # 确保配置目录存在
        config_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

# 全局配置
USER_CONFIG = load_config()

# TMDB配置
TMDB_API_KEY = USER_CONFIG.get('tmdb_api_key', DEFAULT_CONFIG['tmdb_api_key'])
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_PROXY = USER_CONFIG.get('tmdb_proxy', DEFAULT_CONFIG['tmdb_proxy'])
TMDB_PROXY_TYPE = USER_CONFIG.get('tmdb_proxy_type', DEFAULT_CONFIG['tmdb_proxy_type'])

# 豆瓣配置
DOUBAN_COOKIE = USER_CONFIG.get('douban_cookie', DEFAULT_CONFIG['douban_cookie'])
DOUBAN_BASE_URL = 'https://movie.douban.com'

# 支持的媒体文件格式
MEDIA_EXTENSIONS = ['.mp4', '.mkv', '.ts', '.iso', '.rmvb', '.avi', '.mov', '.mpeg', 
                     '.mpg', '.wmv', '.3gp', '.asf', '.m4v', '.flv', '.m2ts', '.tp', '.f4v']
# 支持的字幕文件格式
SUBTITLE_EXTENSIONS = ['.srt', '.ssa', '.ass']

# 分类策略配置
CATEGORY_CONFIG = {
    'movie': {
        '动画电影': {
            'genre_ids': ['16']
        },
        '华语电影': {
            'original_language': ['zh', 'cn', 'bo', 'za']
        },
        '外语电影': {}  # 默认分类
    },
    'tv': {
        '国漫': {
            'genre_ids': ['16'],
            'origin_country': ['CN', 'TW', 'HK']
        },
        '日番': {
            'genre_ids': ['16'],
            'origin_country': ['JP']
        },
        '纪录片': {
            'genre_ids': ['99']
        },
        '儿童': {
            'genre_ids': ['10762']
        },
        '综艺': {
            'genre_ids': ['10764', '10767']
        },
        '国产剧': {
            'origin_country': ['CN', 'TW', 'HK']
        },
        '欧美剧': {
            'origin_country': ['US', 'FR', 'GB', 'DE', 'ES', 'IT', 'NL', 'PT', 'RU', 'UK']
        },
        '日韩剧': {
            'origin_country': ['JP', 'KP', 'KR', 'TH', 'IN', 'SG']
        },
        '未分类': {}  # 默认分类
    }
}

# 重命名模板（旧配置方式使用，新配置使用 PathGenerator）
MOVIE_TEMPLATE = "{{title}}{% if year %} ({{year}}){% endif %}/{{title}}{% if year %} ({{year}}){% endif %}{% if part %}-{{part}}{% endif %}{% if videoFormat %} - {{videoFormat}}{% endif %}{{fileExt}}"
TV_TEMPLATE = "{{title}}{% if year %} ({{year}}){% endif %}/Season {{season}}/{{title}} - {{season_episode}}{% if part %}-{{part}}{% endif %}{% if episode %} - 第 {{episode}} 集{% endif %}{{fileExt}}"

# ============ 版本管理 ============

class VersionManager:
    """版本号管理器"""
    
    VERSION_FILE = 'version.txt'
    
    @staticmethod
    def get_current_version():
        """获取当前版本号"""
        try:
            if os.path.exists(VersionManager.VERSION_FILE):
                with open(VersionManager.VERSION_FILE, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    return version if version else 'v1.0.0'
        except Exception as e:
            print(f"读取版本号失败: {e}")
        return 'v1.0.0'
    
    @staticmethod
    def parse_version(version_str):
        """解析版本号字符串为元组 (major, minor, patch)"""
        try:
            # 移除 'v' 前缀
            version_str = version_str.lstrip('v')
            parts = version_str.split('.')
            if len(parts) == 3:
                return tuple(int(p) for p in parts)
        except:
            pass
        return (1, 0, 0)
    
    @staticmethod
    def compare_versions(v1, v2):
        """比较两个版本号
        返回: -1 (v1<v2), 0 (v1==v2), 1 (v1>v2)
        """
        v1_tuple = VersionManager.parse_version(v1)
        v2_tuple = VersionManager.parse_version(v2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0
    
    @staticmethod
    def increment_version(version_str, level='patch'):
        """递增版本号
        level: 'major', 'minor', 'patch'
        """
        major, minor, patch = VersionManager.parse_version(version_str)
        
        if level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif level == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"v{major}.{minor}.{patch}"
    
    @staticmethod
    def save_version(version_str):
        """保存版本号到文件"""
        try:
            with open(VersionManager.VERSION_FILE, 'w', encoding='utf-8') as f:
                f.write(version_str)
            return True
        except Exception as e:
            print(f"保存版本号失败: {e}")
            return False
    
    @staticmethod
    def get_git_info():
        """获取Git信息（提交哈希和分支）"""
        import subprocess
        try:
            # 获取当前提交哈希
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            commit_hash = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # 获取当前分支
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            return {
                'commit': commit_hash,
                'branch': branch
            }
        except Exception as e:
            print(f"获取Git信息失败: {e}")
            return {
                'commit': 'unknown',
                'branch': 'unknown'
            }

# ============================================

class UpdateManager:
    """系统更新管理器"""
    
    def __init__(self, script_dir=None, config=None):
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
        self.config = config or USER_CONFIG
        self.update_lock = False  # 更新锁，防止并发更新
    
    def check_git_repository(self):
        """检查是否是Git仓库"""
        git_dir = os.path.join(self.script_dir, '.git')
        return os.path.exists(git_dir)
    
    def execute_git_command(self, cmd, use_proxy=False, timeout=30):
        """执行Git命令
        
        Args:
            cmd: Git命令列表，如 ['git', 'fetch']
            use_proxy: 是否使用代理
            timeout: 超时时间（秒）
        
        Returns:
            (success, stdout, stderr)
        """
        import subprocess
        
        try:
            # 获取代理配置
            proxy_url = self.config.get('update_proxy', '')
            
            # 构建环境变量
            env = os.environ.copy()
            
            if use_proxy and proxy_url:
                # 设置Git代理
                env['http_proxy'] = proxy_url
                env['https_proxy'] = proxy_url
                print(f"  使用代理: {proxy_url}")
            
            # 禁用SSL验证（针对某些网络环境）
            cmd_with_config = cmd.copy()
            if 'git' in cmd[0]:
                cmd_with_config.insert(1, '-c')
                cmd_with_config.insert(2, 'http.sslVerify=false')
            
            # 执行命令
            result = subprocess.run(
                cmd_with_config,
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, '', '命令执行超时'
        except Exception as e:
            return False, '', str(e)
    
    def fetch_remote(self, use_proxy=False):
        """获取远程更新"""
        print("正在获取远程更新...")
        success, stdout, stderr = self.execute_git_command(
            ['git', 'fetch', 'origin'],
            use_proxy=use_proxy,
            timeout=60
        )
        
        if success:
            print("✓ 远程更新获取成功")
        else:
            print(f"✗ 获取失败: {stderr}")
        
        return success, stderr
    
    def check_for_updates(self, use_proxy=False):
        """检查是否有可用更新
        
        Returns:
            dict: {
                'has_update': bool,
                'current_version': str,
                'latest_version': str,
                'commits_behind': int,
                'error': str or None
            }
        """
        if not self.check_git_repository():
            return {
                'has_update': False,
                'error': '当前不是Git仓库，无法检查更新'
            }
        
        # 获取当前版本
        current_version = VersionManager.get_current_version()
        
        # 获取远程更新
        success, error = self.fetch_remote(use_proxy)
        if not success:
            # 如果直连失败且未使用代理，尝试使用代理
            if not use_proxy and self.config.get('update_proxy'):
                print("  直连失败，尝试使用代理...")
                success, error = self.fetch_remote(use_proxy=True)
            
            if not success:
                return {
                    'has_update': False,
                    'current_version': current_version,
                    'error': f'无法连接到GitHub: {error}'
                }
        
        # 检查本地和远程的差异
        success, stdout, stderr = self.execute_git_command(
            ['git', 'rev-list', 'HEAD...origin/main', '--count'],
            timeout=10
        )
        
        if not success:
            return {
                'has_update': False,
                'current_version': current_version,
                'error': f'无法比较版本: {stderr}'
            }
        
        try:
            commits_behind = int(stdout.strip() or 0)
        except:
            commits_behind = 0
        
        return {
            'has_update': commits_behind > 0,
            'current_version': current_version,
            'commits_behind': commits_behind,
            'error': None
        }
    
    def pull_updates(self, use_proxy=False, skip_check=False):
        """拉取更新
        
        Args:
            use_proxy: 是否使用代理
            skip_check: 是否跳过本地修改检查（用于force-update）
        
        Returns:
            (success, message)
        """
        print("正在拉取更新...")
        
        # 检查是否有本地修改（除非skip_check=True）
        if not skip_check:
            success, stdout, stderr = self.execute_git_command(
                ['git', 'status', '--porcelain'],
                timeout=10
            )
            
            if success and stdout.strip():
                return False, '检测到本地有未提交的修改，请先提交或重置'
        
        # 执行pull
        success, stdout, stderr = self.execute_git_command(
            ['git', 'pull', 'origin', 'main'],
            use_proxy=use_proxy,
            timeout=60
        )
        
        if success:
            print("✓ 更新成功")
            return True, '更新成功'
        else:
            print(f"✗ 更新失败: {stderr}")
            
            # 如果直连失败且未使用代理，尝试使用代理
            if not use_proxy and self.config.get('update_proxy'):
                print("  直连失败，尝试使用代理...")
                success, stdout, stderr = self.execute_git_command(
                    ['git', 'pull', 'origin', 'main'],
                    use_proxy=True,
                    timeout=60
                )
                
                if success:
                    print("✓ 使用代理更新成功")
                    return True, '使用代理更新成功'
            
            return False, f'更新失败: {stderr}'
    
    def restart_service(self):
        """重启服务"""
        import subprocess
        import threading
        
        def do_restart():
            try:
                time.sleep(3)  # 延迟3秒，让响应返回给前端
                
                # 查找并终止当前进程
                pid_file = os.path.join(self.script_dir, 'media-renamer.pid')
                if os.path.exists(pid_file):
                    try:
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        os.kill(pid, 15)  # SIGTERM
                    except:
                        pass
                
                # 启动新进程
                log_file = os.path.join(self.script_dir, 'media-renamer.log')
                subprocess.Popen(
                    ['python3', 'app.py'],
                    cwd=self.script_dir,
                    stdout=open(log_file, 'a'),
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                print("✓ 服务重启成功")
            except Exception as e:
                print(f"✗ 服务重启失败: {e}")
        
        # 在后台线程中重启
        threading.Thread(target=do_restart, daemon=True).start()
        return True
    
    def rollback(self, steps=1):
        """回滚到之前的版本
        
        Args:
            steps: 回滚步数，默认1（回滚到上一个提交）
        
        Returns:
            (success, message)
        """
        print(f"正在回滚 {steps} 个版本...")
        
        success, stdout, stderr = self.execute_git_command(
            ['git', 'reset', '--hard', f'HEAD~{steps}'],
            timeout=30
        )
        
        if success:
            print("✓ 回滚成功")
            return True, f'成功回滚 {steps} 个版本'
        else:
            print(f"✗ 回滚失败: {stderr}")
            return False, f'回滚失败: {stderr}'

# ============================================

# ============ 115网盘模块 ============

class SecurityHelper:
    """安全辅助工具类"""
    
    @staticmethod
    def mask_cookie(cookie):
        """脱敏Cookie用于日志显示
        
        Args:
            cookie: 原始Cookie字符串
        
        Returns:
            脱敏后的Cookie字符串
        """
        if not cookie or len(cookie) < 20:
            return '***'
        
        # 只显示前8个和后8个字符
        return f"{cookie[:8]}...{cookie[-8:]}"
    
    @staticmethod
    def validate_cookie(cookie):
        """验证Cookie格式
        
        Args:
            cookie: Cookie字符串
        
        Returns:
            (valid: bool, error: str)
        """
        if not cookie:
            return False, "Cookie不能为空"
        
        if not isinstance(cookie, str):
            return False, "Cookie必须是字符串"
        
        cookie = cookie.strip()
        
        if len(cookie) < 10:
            return False, "Cookie长度过短，可能不完整"
        
        # 检查是否包含必要的字段
        required_fields = ['UID', 'CID', 'SEID']
        has_required = any(field in cookie for field in required_fields)
        
        if not has_required:
            return False, "Cookie格式不正确，缺少必要字段（UID/CID/SEID）"
        
        return True, None
    
    @staticmethod
    def validate_folder_id(folder_id):
        """验证文件夹ID
        
        Args:
            folder_id: 文件夹ID
        
        Returns:
            (valid: bool, error: str)
        """
        if not folder_id:
            return False, "文件夹ID不能为空"
        
        # 文件夹ID应该是数字或'0'
        if not str(folder_id).isdigit():
            return False, "文件夹ID格式不正确"
        
        return True, None
    
    @staticmethod
    def validate_filename(filename):
        """验证文件名安全性
        
        Args:
            filename: 文件名
        
        Returns:
            (valid: bool, error: str)
        """
        if not filename:
            return False, "文件名不能为空"
        
        # 检查危险字符
        dangerous_chars = ['..', '/', '\\', '\0', '<', '>', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False, f"文件名包含非法字符: {char}"
        
        # 检查文件名长度
        if len(filename) > 255:
            return False, "文件名过长（最大255字符）"
        
        return True, None
    
    @staticmethod
    def sanitize_log_message(message):
        """清理日志消息中的敏感信息
        
        Args:
            message: 原始日志消息
        
        Returns:
            清理后的日志消息
        """
        import re
        
        # 脱敏Cookie
        message = re.sub(r'(UID|CID|SEID)=[^;]+', r'\1=***', message)
        
        # 脱敏长字符串（可能是Cookie）
        message = re.sub(r'[a-zA-Z0-9]{50,}', lambda m: m.group(0)[:8] + '...' + m.group(0)[-8:], message)
        
        return message


class CookieEncryption:
    """Cookie加密工具"""
    
    KEY_FILE = '.encryption_key'
    
    def __init__(self):
        self.key = self._load_or_create_key()
        try:
            from cryptography.fernet import Fernet
            self.cipher = Fernet(self.key)
        except ImportError:
            print("警告: cryptography未安装，Cookie将不加密存储")
            self.cipher = None
    
    def _load_or_create_key(self):
        """加载或创建加密密钥"""
        try:
            if os.path.exists(self.KEY_FILE):
                with open(self.KEY_FILE, 'rb') as f:
                    return f.read()
            else:
                from cryptography.fernet import Fernet
                key = Fernet.generate_key()
                with open(self.KEY_FILE, 'wb') as f:
                    f.write(key)
                return key
        except ImportError:
            return b'dummy_key_for_no_encryption'
    
    def encrypt(self, cookie):
        """加密Cookie"""
        if self.cipher:
            try:
                return self.cipher.encrypt(cookie.encode()).decode()
            except:
                return cookie
        return cookie
    
    def decrypt(self, encrypted_cookie):
        """解密Cookie"""
        if self.cipher:
            try:
                return self.cipher.decrypt(encrypted_cookie.encode()).decode()
            except:
                return encrypted_cookie
        return encrypted_cookie


class Cloud115API:
    """115网盘API封装"""
    
    BASE_URL = 'https://webapi.115.com'
    
    # 文件列表缓存（5分钟TTL）
    _file_cache = {}
    _cache_ttl = 300  # 5分钟
    
    def __init__(self, cookie):
        # 验证Cookie
        valid, error = SecurityHelper.validate_cookie(cookie)
        if not valid:
            print(f"[Cloud115API] Cookie验证失败: {error}")
        
        self.cookie = cookie
        self.session = self._create_session()
        self.last_error = None
        self.error_count = 0
        self.request_count = 0
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 最小请求间隔（秒）
        
        # 日志中使用脱敏Cookie
        masked_cookie = SecurityHelper.mask_cookie(cookie)
        print(f"[Cloud115API] 初始化API客户端: Cookie={masked_cookie}")
    
    def _handle_api_error(self, error, operation='操作'):
        """统一处理API错误
        
        Args:
            error: 错误对象或错误消息
            operation: 操作名称
        
        Returns:
            用户友好的错误消息
        """
        self.last_error = str(error)
        self.error_count += 1
        
        error_msg = str(error).lower()
        
        # Cookie相关错误
        if 'cookie' in error_msg or 'unauthorized' in error_msg or '401' in error_msg:
            return f"Cookie已过期或无效，请重新登录"
        
        # 网络错误
        if 'timeout' in error_msg or 'connection' in error_msg:
            return f"网络连接超时，请检查网络后重试"
        
        # 速率限制
        if 'rate limit' in error_msg or 'too many' in error_msg or '429' in error_msg:
            return f"请求过于频繁，请稍后再试"
        
        # 权限错误
        if 'permission' in error_msg or 'forbidden' in error_msg or '403' in error_msg:
            return f"没有权限执行此操作"
        
        # 文件不存在
        if 'not found' in error_msg or '404' in error_msg:
            return f"文件或文件夹不存在"
        
        # 服务器错误
        if '500' in error_msg or '502' in error_msg or '503' in error_msg:
            return f"115服务器暂时不可用，请稍后重试"
        
        # 其他错误
        return f"{operation}失败: {error}"
    
    def get_error_stats(self):
        """获取错误统计信息"""
        return {
            'last_error': self.last_error,
            'error_count': self.error_count
        }
    
    def _throttle_request(self):
        """请求节流：确保请求间隔不小于最小间隔"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'min_request_interval': self.min_request_interval
        }
    
    def _create_session(self):
        """创建HTTP会话"""
        try:
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': self.cookie,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://115.com/',
                'Origin': 'https://115.com',
                'X-Requested-With': 'XMLHttpRequest'
            })
            return session
        except ImportError:
            print("错误: requests库未安装")
            return None
    
    def verify_cookie(self):
        """验证Cookie有效性并获取用户信息"""
        try:
            if not self.session:
                return False, None, "requests库未安装，请运行: pip install requests"
            
            if not self.cookie or len(self.cookie.strip()) < 10:
                return False, None, "Cookie为空或格式不正确"
            
            # 尝试多个API端点
            endpoints = [
                ('/files/index_info', 'index_info'),  # 首页信息API
                ('/user/info', 'user_info'),  # 用户信息API
            ]
            
            last_error = None
            for endpoint, name in endpoints:
                try:
                    url = f'{self.BASE_URL}{endpoint}'
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('state'):
                            # 成功获取数据
                            user_data = data.get('data', {})
                            user_info = {
                                'user_id': user_data.get('user_id', user_data.get('uid', '')),
                                'username': user_data.get('user_name', user_data.get('username', '未知用户')),
                                'space_used': user_data.get('space_info', {}).get('all_use', {}).get('size', 0),
                                'space_total': user_data.get('space_info', {}).get('all_total', {}).get('size', 0)
                            }
                            return True, user_info, None
                        else:
                            last_error = data.get('error', 'API返回失败')
                            continue
                    elif response.status_code == 401:
                        return False, None, "Cookie已过期，请重新登录"
                    elif response.status_code == 403:
                        return False, None, "Cookie无效或没有权限"
                    else:
                        last_error = f"HTTP {response.status_code}"
                        continue
                except Exception as e:
                    last_error = str(e)
                    continue
            
            # 所有端点都失败
            error_msg = self._handle_api_error(last_error or "未知错误", "验证Cookie")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "验证Cookie")
            return False, None, error_msg
    
    def list_files(self, folder_id='0', offset=0, limit=1000, use_cache=True):
        """列出文件夹内容
        
        Args:
            folder_id: 文件夹ID，'0'表示根目录
            offset: 偏移量
            limit: 返回数量限制
            use_cache: 是否使用缓存
        
        Returns:
            (result: dict, error: str)
            result包含: files, count, folder_id
        """
        try:
            if not self.session:
                return None, "requests库未安装"
            
            # 检查缓存
            cache_key = f"{folder_id}_{offset}_{limit}"
            if use_cache and cache_key in self._file_cache:
                cached_data, cached_time = self._file_cache[cache_key]
                if time.time() - cached_time < self._cache_ttl:
                    return cached_data, None
            
            # 请求节流
            self._throttle_request()
            
            # 使用webapi端点，最简参数
            url = f'{self.BASE_URL}/files'
            
            # 构建查询字符串（不使用params，直接拼接）
            query_params = f"?aid=1&cid={folder_id}&offset={offset}&limit={limit}&show_dir=1"
            full_url = url + query_params
            
            print(f"[115 API] 请求文件列表: folder_id={folder_id}, url={full_url}")
            response = self.session.get(full_url, timeout=30)
            print(f"[115 API] 响应状态: {response.status_code}")
            print(f"[115 API] 响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[115 API] JSON解析成功, state={data.get('state')}")
                if data.get('state'):
                    files = []
                    for item in data.get('data', []):
                        # 判断是否为文件夹：有cid但没有fid的是文件夹
                        has_cid = bool(item.get('cid'))
                        has_fid = bool(item.get('fid'))
                        is_directory = has_cid and not has_fid
                        
                        file_info = {
                            'fid': item.get('fid', item.get('cid', '')),  # 文件夹用cid作为fid
                            'cid': item.get('cid', ''),
                            'name': item.get('n', ''),
                            'size': item.get('s', 0),
                            'is_dir': is_directory,
                            'time': item.get('t', ''),
                            'pick_code': item.get('pc', ''),
                            'sha1': item.get('sha', ''),
                            'file_count': item.get('fc', 0)
                        }
                        files.append(file_info)
                    
                    result = {
                        'files': files,
                        'count': data.get('count', 0),
                        'folder_id': folder_id,
                        'offset': offset,
                        'limit': limit
                    }
                    
                    # 缓存结果
                    if use_cache:
                        self._file_cache[cache_key] = (result, time.time())
                    
                    return result, None
                else:
                    error_msg = data.get('error', '获取文件列表失败')
                    print(f"[115 API] API返回失败: {error_msg}")
                    return None, error_msg
            else:
                print(f"[115 API] HTTP错误: {response.status_code}")
                return None, f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    def clear_cache(self, folder_id=None):
        """清除文件列表缓存
        
        Args:
            folder_id: 指定文件夹ID，None表示清除全部
        """
        if folder_id is None:
            cleared = len(self._file_cache)
            self._file_cache.clear()
            print(f"[Cloud115API] 清除全部缓存: {cleared} 项")
        else:
            # 清除指定文件夹的缓存
            keys_to_remove = [k for k in self._file_cache.keys() if k.startswith(f"{folder_id}_")]
            for key in keys_to_remove:
                del self._file_cache[key]
            print(f"[Cloud115API] 清除文件夹 {folder_id} 缓存: {len(keys_to_remove)} 项")
    
    def get_cache_stats(self):
        """获取缓存统计信息
        
        Returns:
            {
                'total_items': 缓存项数量,
                'cache_size': 缓存大小（估算）,
                'hit_rate': 缓存命中率（如果有统计）
            }
        """
        import sys
        
        total_items = len(self._file_cache)
        cache_size = sum(sys.getsizeof(v) for v in self._file_cache.values())
        
        # 清理过期缓存
        current_time = time.time()
        expired_keys = []
        for key, (data, cached_time) in self._file_cache.items():
            if current_time - cached_time > self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._file_cache[key]
        
        if expired_keys:
            print(f"[Cloud115API] 清理过期缓存: {len(expired_keys)} 项")
        
        return {
            'total_items': total_items,
            'expired_items': len(expired_keys),
            'cache_size_bytes': cache_size,
            'cache_size_mb': cache_size / (1024 * 1024),
            'ttl_seconds': self._cache_ttl
        }
    
    def rename_file(self, file_id, new_name):
        """重命名文件或文件夹
        
        Args:
            file_id: 文件ID
            new_name: 新文件名
        
        Returns:
            (success: bool, error: str)
        """
        try:
            if not self.session:
                return False, "requests库未安装"
            
            # 验证文件名
            valid, error = SecurityHelper.validate_filename(new_name)
            if not valid:
                return False, error
            
            # 请求节流
            self._throttle_request()
            
            url = f'{self.BASE_URL}/files/batch_rename'
            
            # 115 API需要的参数格式
            data = {
                'files_new_name': json.dumps({file_id: new_name})
            }
            
            print(f"[115 API] 重命名文件: file_id={file_id}, new_name={new_name}")
            response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('state'):
                    self.clear_cache()  # 清除缓存
                    return True, None
                else:
                    error_msg = result.get('error', '重命名失败')
                    return False, error_msg
            else:
                return False, f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 重命名异常: {str(e)}")
            return False, str(e)
    
    def move_file(self, file_ids, target_folder_id):
        """移动文件到指定文件夹
        
        Args:
            file_ids: 文件ID列表（字符串或列表）
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success: bool, error: str)
        """
        try:
            if not self.session:
                return False, "requests库未安装"
            
            # 确保file_ids是列表
            if isinstance(file_ids, str):
                file_ids = [file_ids]
            
            url = f'{self.BASE_URL}/files/move'
            
            # 115 API需要的参数格式
            data = {
                'pid': target_folder_id,
                'fid[0]': ','.join(file_ids)
            }
            
            print(f"[115 API] 移动文件: file_ids={file_ids}, target={target_folder_id}")
            response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('state'):
                    self.clear_cache()  # 清除缓存
                    return True, None
                else:
                    error_msg = result.get('error', '移动失败')
                    return False, error_msg
            else:
                return False, f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 移动异常: {str(e)}")
            return False, str(e)
    
    def delete_file(self, file_ids):
        """删除文件或文件夹
        
        Args:
            file_ids: 文件ID列表（字符串或列表）
        
        Returns:
            (success: bool, error: str)
        """
        try:
            if not self.session:
                return False, "requests库未安装"
            
            # 确保file_ids是列表
            if isinstance(file_ids, str):
                file_ids = [file_ids]
            
            url = f'{self.BASE_URL}/rb/delete'
            
            # 115 API需要的参数格式
            data = {
                'fid[0]': ','.join(file_ids)
            }
            
            print(f"[115 API] 删除文件: file_ids={file_ids}")
            response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('state'):
                    self.clear_cache()  # 清除缓存
                    return True, None
                else:
                    error_msg = result.get('error', '删除失败')
                    return False, error_msg
            else:
                return False, f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 删除异常: {str(e)}")
            return False, str(e)
    
    def create_folder(self, parent_id, folder_name):
        """创建文件夹
        
        Args:
            parent_id: 父文件夹ID
            folder_name: 新文件夹名称
        
        Returns:
            (folder_id: str, error: str)
        """
        try:
            if not self.session:
                return None, "requests库未安装"
            
            url = f'{self.BASE_URL}/files/add'
            
            # 115 API需要的参数格式
            data = {
                'pid': parent_id,
                'cname': folder_name
            }
            
            print(f"[115 API] 创建文件夹: parent={parent_id}, name={folder_name}")
            response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('state'):
                    folder_id = result.get('cid', result.get('id', ''))
                    self.clear_cache()  # 清除缓存
                    return folder_id, None
                else:
                    error_msg = result.get('error', '创建文件夹失败')
                    return None, error_msg
            else:
                return None, f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 创建文件夹异常: {str(e)}")
            return None, str(e)
    
    def batch_rename(self, rename_map):
        """批量重命名文件
        
        Args:
            rename_map: {file_id: new_name} 字典，最多50个
        
        Returns:
            (success_count: int, failed: list, error: str)
        """
        try:
            if not self.session:
                return 0, [], "requests库未安装"
            
            # 限制批量操作数量
            if len(rename_map) > 50:
                return 0, [], "批量操作最多支持50个文件"
            
            url = f'{self.BASE_URL}/files/batch_rename'
            
            data = {
                'files_new_name': json.dumps(rename_map)
            }
            
            print(f"[115 API] 批量重命名: count={len(rename_map)}")
            response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('state'):
                    self.clear_cache()
                    return len(rename_map), [], None
                else:
                    error_msg = result.get('error', '批量重命名失败')
                    return 0, list(rename_map.keys()), error_msg
            else:
                return 0, list(rename_map.keys()), f"HTTP错误: {response.status_code}"
        except Exception as e:
            print(f"[115 API] 批量重命名异常: {str(e)}")
            return 0, list(rename_map.keys()), str(e)
    
    def batch_move(self, file_ids, target_folder_id):
        """批量移动文件
        
        Args:
            file_ids: 文件ID列表，最多50个
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success_count: int, failed: list, error: str)
        """
        try:
            if not self.session:
                return 0, [], "requests库未安装"
            
            # 限制批量操作数量
            if len(file_ids) > 50:
                return 0, file_ids, "批量操作最多支持50个文件"
            
            success, error = self.move_file(file_ids, target_folder_id)
            if success:
                return len(file_ids), [], None
            else:
                return 0, file_ids, error
        except Exception as e:
            print(f"[115 API] 批量移动异常: {str(e)}")
            return 0, file_ids, str(e)
    
    @staticmethod
    def generate_qrcode(qr_type='wechatmini'):
        """生成115网盘二维码登录（基于Alist/py115正确实现）
        
        Args:
            qr_type: 二维码类型
                - web: 网页版
                - android: 安卓APP
                - ios: iOS APP
                - tv: TV版
                - alipaymini: 支付宝小程序
                - wechatmini: 微信小程序（推荐）
                - qandroid: 安卓TV
        
        Returns:
            (qrcode_url: str, session_id: str, error: str)
        """
        try:
            # 检查requests库
            try:
                import requests
            except ImportError:
                return None, None, "requests库未安装，请运行: pip install requests"
            
            import uuid
            import qrcode
            import io
            import base64
            
            print(f"[115 API] 开始生成二维码: type={qr_type}")
            
            session_id = str(uuid.uuid4())
            
            # 第一步：获取二维码token（参考py115实现）
            url = 'https://qrcodeapi.115.com/api/1.0/web/1.0/token/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[115 API] 请求token: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"[115 API] 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[115 API] 响应数据: {data}")
                
                if data.get('state'):
                    token_data = data.get('data', {})
                    uid = token_data.get('uid', '')
                    time_val = token_data.get('time', 0)
                    sign = token_data.get('sign', '')
                    qrcode_content = token_data.get('qrcode', '')  # 关键！使用API返回的qrcode字段
                    
                    if not uid or not sign or not qrcode_content:
                        return None, None, 'API返回数据不完整'
                    
                    print(f"[115 API] 获取到token: uid={uid}, time={time_val}, sign={sign}")
                    print(f"[115 API] 二维码内容: {qrcode_content[:50]}...")
                    
                    # 使用qrcode库生成二维码图片（使用API返回的qrcode内容）
                    try:
                        qr = qrcode.QRCode(version=1, box_size=10, border=2)
                        qr.add_data(qrcode_content)  # 使用API返回的qrcode内容，不是自己拼接的URL
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        # 转换为base64
                        buffer = io.BytesIO()
                        img.save(buffer, format='PNG')
                        img_base64 = base64.b64encode(buffer.getvalue()).decode()
                        qrcode_url = f'data:image/png;base64,{img_base64}'
                    except ImportError:
                        # 如果qrcode库未安装，返回二维码内容让前端生成
                        qrcode_url = qrcode_content
                    
                    # 保存session信息
                    if not hasattr(Cloud115API, '_qr_sessions'):
                        Cloud115API._qr_sessions = {}
                    
                    Cloud115API._qr_sessions[session_id] = {
                        'uid': uid,
                        'time': time_val,
                        'sign': sign,
                        'app': qr_type,
                        'status': 'waiting',
                        'cookie': None,
                        'timestamp': time.time()
                    }
                    
                    print(f"[115 API] 二维码生成成功")
                    return qrcode_url, session_id, None
                else:
                    error_msg = data.get('error', '生成二维码失败')
                    print(f"[115 API] API返回失败: {error_msg}")
                    return None, None, error_msg
            else:
                error_msg = f"HTTP错误: {response.status_code}"
                print(f"[115 API] {error_msg}")
                return None, None, error_msg
        except Exception as e:
            print(f"[115 API] 生成二维码异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None, str(e)
    
    @staticmethod
    def check_qrcode_status(session_id):
        """检查二维码扫码状态（基于Alist/py115正确实现）
        
        Args:
            session_id: 会话ID
        
        Returns:
            (status: str, cookie: str, error: str)
            status: waiting/scanned/success/expired/cancelled
        """
        try:
            import requests
            from urllib.parse import urlencode
            
            if not hasattr(Cloud115API, '_qr_sessions'):
                return 'expired', None, '会话不存在'
            
            session = Cloud115API._qr_sessions.get(session_id)
            if not session:
                return 'expired', None, '会话不存在'
            
            # 检查是否过期（5分钟）
            if time.time() - session['timestamp'] > 300:
                del Cloud115API._qr_sessions[session_id]
                return 'expired', None, '二维码已过期'
            
            # 如果已经获取到Cookie，直接返回
            if session.get('cookie'):
                cookie = session['cookie']
                del Cloud115API._qr_sessions[session_id]
                return 'success', cookie, None
            
            # 第一步：检查扫码状态（参考py115实现）
            payload = {
                'uid': session['uid'],
                'time': session['time'],
                'sign': session['sign']
            }
            url = f'https://qrcodeapi.115.com/get/status/?{urlencode(payload)}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[115 API] 检查扫码状态: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[115 API] 状态响应: {data}")
                
                status_data = data.get('data', {})
                status_code = status_data.get('status')
                
                if status_code == 0:
                    # 等待扫码
                    return 'waiting', None, None
                elif status_code == 1:
                    # 已扫码，等待确认
                    return 'scanned', None, None
                elif status_code == 2:
                    # 扫码成功，需要POST获取Cookie
                    print(f"[115 API] 扫码确认，开始获取Cookie")
                    
                    # 第二步：POST获取Cookie（关键步骤！）
                    app = session.get('app', 'wechatmini')
                    post_url = f'https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode/'
                    post_data = {
                        'app': app,
                        'account': session['uid']
                    }
                    
                    print(f"[115 API] POST获取Cookie: {post_url}, data={post_data}")
                    post_response = requests.post(
                        post_url,
                        data=post_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if post_response.status_code == 200:
                        result = post_response.json()
                        print(f"[115 API] Cookie响应: {result}")
                        
                        if result.get('state'):
                            # 成功获取Cookie
                            cookie_dict = result.get('data', {}).get('cookie', {})
                            
                            # 构建Cookie字符串
                            cookie_parts = []
                            for key in ['UID', 'CID', 'SEID']:
                                if key in cookie_dict:
                                    cookie_parts.append(f"{key}={cookie_dict[key]}")
                            
                            cookie = '; '.join(cookie_parts)
                            
                            if cookie:
                                print(f"[115 API] 成功获取Cookie")
                                # 保存Cookie到session
                                session['cookie'] = cookie
                                session['status'] = 'success'
                                return 'success', cookie, None
                            else:
                                print(f"[115 API] Cookie数据为空")
                                return 'waiting', None, 'Cookie数据为空'
                        else:
                            error_msg = result.get('error', '获取Cookie失败')
                            print(f"[115 API] 获取Cookie失败: {error_msg}")
                            return 'waiting', None, error_msg
                    else:
                        print(f"[115 API] POST请求失败: {post_response.status_code}")
                        return 'waiting', None, f'HTTP错误: {post_response.status_code}'
                        
                elif status_code == -1:
                    # 二维码过期
                    del Cloud115API._qr_sessions[session_id]
                    return 'expired', None, '二维码已过期'
                elif status_code == -2:
                    # 取消扫码
                    return 'cancelled', None, '用户取消扫码'
                else:
                    print(f"[115 API] 未知状态码: {status_code}")
                    return 'waiting', None, None
            else:
                print(f"[115 API] 检查状态失败: {response.status_code}")
                return 'waiting', None, None
        except Exception as e:
            print(f"[115 API] 检查二维码状态异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return 'waiting', None, str(e)

# ============================================

class CloudScanner:
    """115网盘扫描器"""
    
    # 支持的媒体文件扩展名
    MEDIA_EXTENSIONS = {
        'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.rmvb', '.rm', '.3gp', '.ts', '.m2ts'],
        'subtitle': ['.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt']
    }
    
    def __init__(self, api):
        """
        Args:
            api: Cloud115API实例
        """
        self.api = api
        self.scan_stats = {
            'total_files': 0,
            'total_size': 0,
            'video_files': 0,
            'subtitle_files': 0,
            'folders_scanned': 0
        }
    
    def is_media_file(self, filename):
        """判断是否为媒体文件"""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.MEDIA_EXTENSIONS['video']
    
    def is_subtitle_file(self, filename):
        """判断是否为字幕文件"""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.MEDIA_EXTENSIONS['subtitle']
    
    def filter_media_files(self, files):
        """过滤出媒体文件
        
        Args:
            files: 文件列表
        
        Returns:
            (video_files: list, subtitle_files: list)
        """
        video_files = []
        subtitle_files = []
        
        for file in files:
            if file.get('is_dir'):
                continue
            
            filename = file.get('name', '')
            if self.is_media_file(filename):
                video_files.append(file)
            elif self.is_subtitle_file(filename):
                subtitle_files.append(file)
        
        return video_files, subtitle_files
    
    def scan_folder(self, folder_id='0', recursive=True, max_depth=10):
        """扫描文件夹
        
        Args:
            folder_id: 文件夹ID
            recursive: 是否递归扫描子文件夹
            max_depth: 最大递归深度
        
        Returns:
            {
                'video_files': [...],
                'subtitle_files': [...],
                'stats': {...}
            }
        """
        all_video_files = []
        all_subtitle_files = []
        
        def _scan_recursive(fid, depth=0):
            if depth > max_depth:
                return
            
            # 获取文件列表
            result, error = self.api.list_files(fid, offset=0, limit=1000)
            if error:
                print(f"[CloudScanner] 扫描文件夹 {fid} 失败: {error}")
                return
            
            files = result.get('files', [])
            self.scan_stats['folders_scanned'] += 1
            
            # 过滤媒体文件
            video_files, subtitle_files = self.filter_media_files(files)
            
            # 添加文件夹路径信息
            for vf in video_files:
                vf['folder_id'] = fid
                vf['depth'] = depth
            for sf in subtitle_files:
                sf['folder_id'] = fid
                sf['depth'] = depth
            
            all_video_files.extend(video_files)
            all_subtitle_files.extend(subtitle_files)
            
            self.scan_stats['total_files'] += len(files)
            self.scan_stats['video_files'] += len(video_files)
            self.scan_stats['subtitle_files'] += len(subtitle_files)
            
            for f in files:
                self.scan_stats['total_size'] += f.get('size', 0)
            
            # 递归扫描子文件夹
            if recursive:
                folders = [f for f in files if f.get('is_dir')]
                for folder in folders:
                    _scan_recursive(folder.get('fid'), depth + 1)
        
        # 开始扫描
        print(f"[CloudScanner] 开始扫描文件夹: {folder_id}")
        _scan_recursive(folder_id)
        
        print(f"[CloudScanner] 扫描完成: {self.scan_stats}")
        
        return {
            'video_files': all_video_files,
            'subtitle_files': all_subtitle_files,
            'stats': self.scan_stats.copy()
        }
    
    def group_duplicate_files(self, video_files):
        """识别重复文件并分组
        
        Args:
            video_files: 视频文件列表
        
        Returns:
            {
                'duplicates': [
                    {
                        'name': '基础文件名',
                        'files': [
                            {'file': {...}, 'quality_score': 1500, 'keep': True},
                            {'file': {...}, 'quality_score': 800, 'keep': False}
                        ]
                    }
                ],
                'unique_files': [...],
                'stats': {
                    'total_files': 100,
                    'duplicate_groups': 10,
                    'files_to_delete': 15
                }
            }
        """
        from collections import defaultdict
        
        # 按基础文件名分组
        file_groups = defaultdict(list)
        
        for file in video_files:
            filename = file.get('name', '')
            # 提取基础文件名（去除分辨率、来源等标记）
            base_name = self._extract_base_name(filename)
            file_groups[base_name].append(file)
        
        duplicates = []
        unique_files = []
        files_to_delete = []
        
        for base_name, files in file_groups.items():
            if len(files) > 1:
                # 有重复，计算质量分数并排序
                scored_files = []
                for f in files:
                    score = self._calculate_quality_score(f)
                    scored_files.append({
                        'file': f,
                        'quality_score': score,
                        'keep': False
                    })
                
                # 按质量分数降序排序
                scored_files.sort(key=lambda x: x['quality_score'], reverse=True)
                
                # 标记保留最高质量的文件
                scored_files[0]['keep'] = True
                
                # 其他文件标记为删除
                for sf in scored_files[1:]:
                    files_to_delete.append(sf['file'])
                
                duplicates.append({
                    'name': base_name,
                    'files': scored_files
                })
            else:
                # 唯一文件
                unique_files.append(files[0])
        
        stats = {
            'total_files': len(video_files),
            'duplicate_groups': len(duplicates),
            'files_to_delete': len(files_to_delete),
            'unique_files': len(unique_files)
        }
        
        print(f"[CloudScanner] 去重分析完成: {stats}")
        
        return {
            'duplicates': duplicates,
            'unique_files': unique_files,
            'files_to_delete': files_to_delete,
            'stats': stats
        }
    
    def _extract_base_name(self, filename):
        """提取基础文件名（去除质量标记）
        
        Args:
            filename: 文件名
        
        Returns:
            基础文件名
        """
        import re
        
        # 去除扩展名
        name = os.path.splitext(filename)[0]
        
        # 去除常见的质量标记
        patterns = [
            r'\b(2160p|1080p|720p|480p|4k)\b',
            r'\b(bluray|blu-ray|web-dl|webrip|hdtv|bdrip|dvdrip)\b',
            r'\b(x264|x265|h264|h265|hevc|avc)\b',
            r'\b(aac|ac3|dts|truehd|atmos)\b',
            r'\[\d+p\]',
            r'\[.*?(bluray|web|hdtv).*?\]',
        ]
        
        for pattern in patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # 清理多余的空格、点、横线
        name = re.sub(r'[\s\.\-_]+', ' ', name).strip()
        
        return name
    
    def _calculate_quality_score(self, file):
        """计算文件质量分数（用于去重）
        
        Args:
            file: 文件信息字典
        
        Returns:
            质量分数（整数）
        """
        score = 0
        name = file.get('name', '').lower()
        size = file.get('size', 0)
        
        # 分辨率分数
        if '2160p' in name or '4k' in name:
            score += 1000
        elif '1080p' in name:
            score += 500
        elif '720p' in name:
            score += 200
        elif '480p' in name:
            score += 100
        
        # 来源分数
        if 'bluray' in name or 'blu-ray' in name or 'bdrip' in name:
            score += 300
        elif 'web-dl' in name:
            score += 200
        elif 'webrip' in name:
            score += 150
        elif 'hdtv' in name:
            score += 100
        
        # 编码分数
        if 'hevc' in name or 'x265' in name or 'h265' in name:
            score += 50
        elif 'x264' in name or 'h264' in name:
            score += 30
        
        # 音频分数
        if 'atmos' in name or 'truehd' in name:
            score += 30
        elif 'dts' in name:
            score += 20
        elif 'ac3' in name:
            score += 10
        elif 'aac' in name:
            score += 5
        
        # 文件大小分数（越大越好，但有上限）
        size_gb = size / (1024 * 1024 * 1024)
        size_score = min(size_gb * 10, 100)  # 最多100分
        score += size_score
        
        return score
    
    def group_duplicate_files(self, video_files):
        """识别重复文件（基于文件名和大小）
        
        注意：此方法需要非常谨慎，避免误删文件
        
        Args:
            video_files: 视频文件列表
        
        Returns:
            {
                'duplicates': [
                    {
                        'name': '文件名',
                        'files': [文件列表],
                        'keep': 文件ID,
                        'remove': [文件ID列表]
                    }
                ],
                'unique': [唯一文件列表]
            }
        """
        from collections import defaultdict
        
        # 使用更严格的去重策略：只有文件名几乎完全相同才认为是重复
        name_groups = defaultdict(list)
        for file in video_files:
            name = file.get('name', '')
            base_name = os.path.splitext(name)[0].lower()
            
            # 只移除最常见的质量标记，保留更多信息避免误判
            # 移除前后的空格、点、下划线
            base_name = re.sub(r'[\s\._-]+', ' ', base_name)
            # 只移除明确的质量标记（必须是独立的词）
            base_name = re.sub(r'\s+(1080p|720p|480p|2160p|4k)\s+', ' ', base_name, flags=re.IGNORECASE)
            base_name = re.sub(r'\s+(bluray|blu-ray|web-dl|webrip|hdtv)\s+', ' ', base_name, flags=re.IGNORECASE)
            base_name = re.sub(r'\s+(x264|x265|h264|h265|hevc|avc)\s+', ' ', base_name, flags=re.IGNORECASE)
            base_name = base_name.strip()
            
            # 如果处理后的名称太短（少于5个字符），使用原始名称避免误判
            if len(base_name) < 5:
                base_name = os.path.splitext(name)[0].lower()
            
            name_groups[base_name].append(file)
        
        duplicates = []
        unique = []
        
        for base_name, files in name_groups.items():
            if len(files) > 1:
                # 额外检查：文件大小差异不能太大（避免误判）
                sizes = [f.get('size', 0) for f in files]
                max_size = max(sizes)
                min_size = min(sizes)
                
                # 如果最大和最小文件大小差异超过30%，可能不是重复
                if max_size > 0 and (max_size - min_size) / max_size > 0.3:
                    print(f"[CloudScanner] 跳过可疑重复组: {base_name} (大小差异过大)")
                    unique.extend(files)
                    continue
                
                # 有重复，按质量排序
                sorted_files = sorted(files, key=lambda f: self._calculate_quality_score(f), reverse=True)
                duplicates.append({
                    'name': base_name,
                    'files': sorted_files,
                    'keep': sorted_files[0].get('fid'),
                    'remove': [f.get('fid') for f in sorted_files[1:]]
                })
                print(f"[CloudScanner] 发现重复: {base_name} ({len(files)}个文件)")
            else:
                unique.extend(files)
        
        return {
            'duplicates': duplicates,
            'unique': unique
        }
    
    def _calculate_quality_score(self, file):
        """计算文件质量分数（用于去重）"""
        score = 0
        name = file.get('name', '').lower()
        size = file.get('size', 0)
        
        # 分辨率分数
        if '2160p' in name or '4k' in name:
            score += 1000
        elif '1080p' in name:
            score += 500
        elif '720p' in name:
            score += 200
        elif '480p' in name:
            score += 100
        
        # 来源分数
        if 'bluray' in name or 'blu-ray' in name:
            score += 300
        elif 'web-dl' in name:
            score += 200
        elif 'webrip' in name:
            score += 150
        elif 'hdtv' in name:
            score += 100
        
        # 编码分数
        if 'hevc' in name or 'x265' in name or 'h265' in name:
            score += 50
        elif 'x264' in name or 'h264' in name:
            score += 30
        
        # 文件大小分数（越大越好，但有上限）
        size_score = min(size / (1024 * 1024 * 1024), 50)  # 最多50分
        score += size_score
        
        return score

# ============================================

class RateLimiter:
    """API速率限制处理器"""
    
    def __init__(self, max_retries=3, base_delay=1.0):
        """
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.rate_limit_events = []
    
    def execute_with_retry(self, func, *args, **kwargs):
        """执行函数，遇到速率限制时自动重试
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数执行结果
        
        Raises:
            Exception: 超过最大重试次数后抛出异常
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                
                # 检查结果是否表示速率限制
                if self._is_rate_limited(result):
                    wait_time = self._calculate_backoff(attempt)
                    self._log_rate_limit(attempt, wait_time)
                    time.sleep(wait_time)
                    continue
                
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # 检查是否为速率限制错误
                if 'rate limit' in error_msg or 'too many requests' in error_msg or '429' in error_msg:
                    wait_time = self._calculate_backoff(attempt)
                    self._log_rate_limit(attempt, wait_time)
                    time.sleep(wait_time)
                    continue
                
                # 其他错误，检查是否需要重试
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay
                    print(f"[RateLimiter] 请求失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                
                # 最后一次尝试失败，抛出异常
                raise
        
        # 超过最大重试次数
        if last_error:
            raise last_error
        else:
            raise Exception(f"超过最大重试次数 ({self.max_retries})")
    
    def _is_rate_limited(self, result):
        """检查结果是否表示速率限制
        
        Args:
            result: API返回结果
        
        Returns:
            bool: 是否被限流
        """
        if isinstance(result, tuple) and len(result) >= 2:
            # (success, error) 格式
            success, error = result[0], result[1]
            if not success and error:
                error_lower = str(error).lower()
                return 'rate limit' in error_lower or 'too many' in error_lower or '429' in error_lower
        
        return False
    
    def _calculate_backoff(self, attempt):
        """计算指数退避等待时间
        
        Args:
            attempt: 当前尝试次数（从0开始）
        
        Returns:
            等待时间（秒）
        """
        # 指数退避: 1s, 2s, 4s, 8s...
        wait_time = self.base_delay * (2 ** attempt)
        # 添加随机抖动，避免多个请求同时重试
        import random
        jitter = random.uniform(0, 0.5)
        return wait_time + jitter
    
    def _log_rate_limit(self, attempt, wait_time):
        """记录速率限制事件
        
        Args:
            attempt: 尝试次数
            wait_time: 等待时间
        """
        event = {
            'timestamp': time.time(),
            'attempt': attempt + 1,
            'wait_time': wait_time
        }
        self.rate_limit_events.append(event)
        
        # 只保留最近100条记录
        if len(self.rate_limit_events) > 100:
            self.rate_limit_events = self.rate_limit_events[-100:]
        
        print(f"[RateLimiter] 检测到速率限制，等待 {wait_time:.1f} 秒后重试 (尝试 {attempt + 1}/{self.max_retries})")
    
    def get_stats(self):
        """获取速率限制统计信息
        
        Returns:
            统计信息字典
        """
        if not self.rate_limit_events:
            return {
                'total_events': 0,
                'recent_events': 0,
                'avg_wait_time': 0
            }
        
        # 最近5分钟的事件
        recent_threshold = time.time() - 300
        recent_events = [e for e in self.rate_limit_events if e['timestamp'] > recent_threshold]
        
        avg_wait = sum(e['wait_time'] for e in self.rate_limit_events) / len(self.rate_limit_events)
        
        return {
            'total_events': len(self.rate_limit_events),
            'recent_events': len(recent_events),
            'avg_wait_time': avg_wait
        }

# ============================================

class CloudRenamer:
    """115网盘文件重命名器"""
    
    def __init__(self, api, handler):
        """
        Args:
            api: Cloud115API实例
            handler: RequestHandler实例（用于调用parse_media_filename）
        """
        self.api = api
        self.handler = handler
    
    def parse_filename(self, filename, parent_folder=''):
        """解析文件名，提取媒体信息
        
        Args:
            filename: 文件名
            parent_folder: 父文件夹名称
        
        Returns:
            metadata字典
        """
        return self.handler.parse_media_filename(filename, parent_folder)
    
    def generate_new_name(self, file_info, metadata, naming_template=None):
        """生成新文件名
        
        Args:
            file_info: 文件信息字典
            metadata: 解析出的元数据
            naming_template: 命名模板（可选）
        
        Returns:
            新文件名
        """
        if not naming_template:
            # 默认命名模板
            if metadata.get('type') == 'tv':
                # 电视剧: 标题 (年份) S01E01
                if metadata.get('season_episode'):
                    template = "{title}"
                    if metadata.get('year'):
                        template += " ({year})"
                    template += " {season_episode}{fileExt}"
                else:
                    template = "{title}{fileExt}"
            else:
                # 电影: 标题 (年份)
                template = "{title}"
                if metadata.get('year'):
                    template += " ({year})"
                template += "{fileExt}"
            naming_template = template
        
        # 使用元数据填充模板
        new_name = naming_template.format(**metadata)
        
        # 清理文件名中的非法字符
        new_name = re.sub(r'[<>:"/\\|?*]', '', new_name)
        new_name = new_name.strip()
        
        return new_name
    
    def preview_rename(self, files, naming_template=None):
        """预览重命名结果
        
        Args:
            files: 文件列表
            naming_template: 命名模板（可选）
        
        Returns:
            [
                {
                    'file_id': '...',
                    'old_name': '...',
                    'new_name': '...',
                    'metadata': {...},
                    'changed': True/False
                }
            ]
        """
        preview_results = []
        
        for file in files:
            old_name = file.get('name', '')
            file_id = file.get('fid', '')
            
            # 解析文件名
            metadata = self.parse_filename(old_name)
            
            # 生成新文件名
            new_name = self.generate_new_name(file, metadata, naming_template)
            
            preview_results.append({
                'file_id': file_id,
                'old_name': old_name,
                'new_name': new_name,
                'metadata': metadata,
                'changed': old_name != new_name
            })
        
        return preview_results
    
    def rename_file(self, file_id, new_name):
        """重命名单个文件
        
        Args:
            file_id: 文件ID
            new_name: 新文件名
        
        Returns:
            (success: bool, error: str)
        """
        return self.api.rename_file(file_id, new_name)
    
    def batch_rename(self, rename_list, batch_size=50):
        """批量重命名文件
        
        Args:
            rename_list: [{'file_id': '...', 'new_name': '...'}]
            batch_size: 每批处理数量
        
        Returns:
            {
                'success_count': int,
                'failed_count': int,
                'failed_files': [...]
            }
        """
        success_count = 0
        failed_count = 0
        failed_files = []
        
        # 分批处理
        for i in range(0, len(rename_list), batch_size):
            batch = rename_list[i:i + batch_size]
            
            # 构建重命名映射
            rename_map = {item['file_id']: item['new_name'] for item in batch}
            
            # 调用API批量重命名
            count, failed, error = self.api.batch_rename(rename_map)
            
            success_count += count
            failed_count += len(failed)
            
            if failed:
                for file_id in failed:
                    # 找到对应的文件信息
                    file_info = next((item for item in batch if item['file_id'] == file_id), None)
                    if file_info:
                        failed_files.append({
                            'file_id': file_id,
                            'new_name': file_info['new_name'],
                            'error': error
                        })
            
            # 添加延迟避免API限流
            if i + batch_size < len(rename_list):
                time.sleep(1)
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_files': failed_files
        }

# ============================================

class CloudMover:
    """115网盘文件移动器"""
    
    def __init__(self, api):
        """
        Args:
            api: Cloud115API实例
        """
        self.api = api
        self.folder_cache = {}  # 文件夹ID缓存
    
    def ensure_folder_exists(self, parent_id, folder_name):
        """确保文件夹存在，不存在则创建
        
        Args:
            parent_id: 父文件夹ID
            folder_name: 文件夹名称
        
        Returns:
            (folder_id: str, error: str)
        """
        # 检查缓存
        cache_key = f"{parent_id}/{folder_name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key], None
        
        # 获取父文件夹内容
        result, error = self.api.list_files(parent_id, offset=0, limit=1000)
        if error:
            return None, f"获取文件夹列表失败: {error}"
        
        # 查找是否已存在同名文件夹
        files = result.get('files', [])
        for file in files:
            if file.get('is_dir') and file.get('name') == folder_name:
                folder_id = file.get('fid')
                self.folder_cache[cache_key] = folder_id
                return folder_id, None
        
        # 不存在，创建新文件夹
        folder_id, error = self.api.create_folder(parent_id, folder_name)
        if error:
            return None, f"创建文件夹失败: {error}"
        
        self.folder_cache[cache_key] = folder_id
        return folder_id, None
    
    def create_category_structure(self, base_folder_id, category, title, year=None):
        """创建分类文件夹结构
        
        Args:
            base_folder_id: 基础文件夹ID
            category: 分类（'movie' 或 'tv'）
            title: 标题
            year: 年份（可选）
        
        Returns:
            (target_folder_id: str, error: str)
        """
        try:
            # 第一层：分类文件夹（电影/电视剧）
            category_name = '电影' if category == 'movie' else '电视剧'
            category_id, error = self.ensure_folder_exists(base_folder_id, category_name)
            if error:
                return None, error
            
            # 第二层：标题文件夹
            if year:
                folder_name = f"{title} ({year})"
            else:
                folder_name = title
            
            target_id, error = self.ensure_folder_exists(category_id, folder_name)
            if error:
                return None, error
            
            return target_id, None
        except Exception as e:
            return None, str(e)
    
    def move_file(self, file_id, target_folder_id):
        """移动单个文件
        
        Args:
            file_id: 文件ID
            target_folder_id: 目标文件夹ID
        
        Returns:
            (success: bool, error: str)
        """
        return self.api.move_file(file_id, target_folder_id)
    
    def batch_move(self, file_list, target_folder_id, batch_size=50):
        """批量移动文件
        
        Args:
            file_list: 文件ID列表
            target_folder_id: 目标文件夹ID
            batch_size: 每批处理数量
        
        Returns:
            {
                'success_count': int,
                'failed_count': int,
                'failed_files': [...]
            }
        """
        success_count = 0
        failed_count = 0
        failed_files = []
        
        # 分批处理
        for i in range(0, len(file_list), batch_size):
            batch = file_list[i:i + batch_size]
            
            # 调用API批量移动
            count, failed, error = self.api.batch_move(batch, target_folder_id)
            
            success_count += count
            failed_count += len(failed)
            
            if failed:
                for file_id in failed:
                    failed_files.append({
                        'file_id': file_id,
                        'error': error
                    })
            
            # 添加延迟避免API限流
            if i + batch_size < len(file_list):
                time.sleep(1)
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_files': failed_files
        }
    
    def organize_files(self, files, base_folder_id, metadata_map):
        """整理文件到分类文件夹
        
        Args:
            files: 文件列表
            base_folder_id: 基础文件夹ID
            metadata_map: {file_id: metadata} 元数据映射
        
        Returns:
            {
                'success_count': int,
                'failed_count': int,
                'operations': [...]
            }
        """
        operations = []
        success_count = 0
        failed_count = 0
        
        # 按标题和年份分组
        from collections import defaultdict
        groups = defaultdict(list)
        
        for file in files:
            file_id = file.get('fid')
            metadata = metadata_map.get(file_id, {})
            
            title = metadata.get('title', '未知')
            year = metadata.get('year', '')
            category = metadata.get('type', 'movie')
            
            group_key = f"{category}|{title}|{year}"
            groups[group_key].append(file)
        
        # 为每组创建文件夹并移动文件
        for group_key, group_files in groups.items():
            category, title, year = group_key.split('|')
            
            # 创建目标文件夹
            target_id, error = self.create_category_structure(
                base_folder_id, category, title, year if year else None
            )
            
            if error:
                failed_count += len(group_files)
                for file in group_files:
                    operations.append({
                        'file_id': file.get('fid'),
                        'file_name': file.get('name'),
                        'action': 'move',
                        'target': f"{title} ({year})" if year else title,
                        'success': False,
                        'error': error
                    })
                continue
            
            # 批量移动文件
            file_ids = [f.get('fid') for f in group_files]
            result = self.batch_move(file_ids, target_id)
            
            success_count += result['success_count']
            failed_count += result['failed_count']
            
            # 记录操作
            for file in group_files:
                file_id = file.get('fid')
                is_success = file_id not in [f['file_id'] for f in result['failed_files']]
                
                operations.append({
                    'file_id': file_id,
                    'file_name': file.get('name'),
                    'action': 'move',
                    'target': f"{title} ({year})" if year else title,
                    'target_id': target_id,
                    'success': is_success,
                    'error': None if is_success else '移动失败'
                })
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'operations': operations
        }

# ============================================

class CloudHistoryManager:
    """115网盘操作历史记录管理器"""
    
    HISTORY_FILE = 'cloud_history.json'
    MAX_RECORDS = 100
    
    def __init__(self):
        """初始化历史记录管理器"""
        self.history_file = os.path.join(os.path.expanduser('~/.media-renamer'), self.HISTORY_FILE)
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """确保历史记录文件存在"""
        try:
            # 确保目录存在
            history_dir = os.path.dirname(self.history_file)
            if not os.path.exists(history_dir):
                os.makedirs(history_dir, exist_ok=True)
            
            # 如果文件不存在，创建空文件
            if not os.path.exists(self.history_file):
                self._save_history([])
        except Exception as e:
            print(f"[CloudHistory] 创建历史文件失败: {e}")
    
    def save_operation(self, operation_type, file_info, new_info=None, status='success', error=None):
        """保存操作记录
        
        Args:
            operation_type: 操作类型 (rename|move|delete|scan)
            file_info: 文件信息字典
            new_info: 新文件信息（重命名/移动后）
            status: 操作状态 (success|failed)
            error: 错误信息（如果失败）
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 加载现有历史
            history = self._load_history()
            
            # 创建新记录
            record = {
                'id': self._generate_id(),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'operation_type': operation_type,
                'status': status,
                'file_id': file_info.get('fid', ''),
                'file_name': file_info.get('name', ''),
                'file_size': file_info.get('size', 0),
                'folder_id': file_info.get('folder_id', file_info.get('cid', ''))
            }
            
            # 添加操作特定信息
            if operation_type == 'rename' and new_info:
                record['new_name'] = new_info.get('name', '')
            elif operation_type == 'move' and new_info:
                record['target_folder_id'] = new_info.get('folder_id', '')
                record['target_folder_name'] = new_info.get('folder_name', '')
            
            # 添加错误信息
            if error:
                record['error'] = str(error)
            
            # 添加到历史记录
            history.insert(0, record)  # 最新的在前面
            
            # 限制记录数量
            if len(history) > self.MAX_RECORDS:
                history = history[:self.MAX_RECORDS]
            
            # 保存历史
            self._save_history(history)
            
            return True
            
        except Exception as e:
            print(f"[CloudHistory] 保存操作记录失败: {e}")
            return False
    
    def load_history(self, limit=100, offset=0, operation_type=None, date_from=None, date_to=None):
        """加载历史记录
        
        Args:
            limit: 返回记录数量限制
            offset: 偏移量
            operation_type: 过滤操作类型
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
        
        Returns:
            {
                'records': [...],
                'total': 总数量,
                'filtered': 过滤后数量
            }
        """
        try:
            history = self._load_history()
            total = len(history)
            
            # 过滤
            filtered = history
            
            if operation_type:
                filtered = [r for r in filtered if r.get('operation_type') == operation_type]
            
            if date_from:
                filtered = [r for r in filtered if r.get('timestamp', '') >= date_from]
            
            if date_to:
                # 包含当天的所有记录
                date_to_end = date_to + ' 23:59:59'
                filtered = [r for r in filtered if r.get('timestamp', '') <= date_to_end]
            
            filtered_count = len(filtered)
            
            # 分页
            records = filtered[offset:offset + limit]
            
            return {
                'records': records,
                'total': total,
                'filtered': filtered_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            print(f"[CloudHistory] 加载历史记录失败: {e}")
            return {
                'records': [],
                'total': 0,
                'filtered': 0,
                'limit': limit,
                'offset': offset
            }
    
    def get_statistics(self):
        """获取历史统计信息
        
        Returns:
            统计信息字典
        """
        try:
            history = self._load_history()
            
            stats = {
                'total_operations': len(history),
                'by_type': {},
                'by_status': {},
                'recent_24h': 0,
                'recent_7d': 0
            }
            
            # 统计各类型操作数量
            for record in history:
                op_type = record.get('operation_type', 'unknown')
                status = record.get('status', 'unknown')
                
                stats['by_type'][op_type] = stats['by_type'].get(op_type, 0) + 1
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # 统计最近操作
            now = time.time()
            for record in history:
                timestamp_str = record.get('timestamp', '')
                try:
                    timestamp = time.mktime(time.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'))
                    age = now - timestamp
                    
                    if age < 86400:  # 24小时
                        stats['recent_24h'] += 1
                    if age < 604800:  # 7天
                        stats['recent_7d'] += 1
                except:
                    pass
            
            return stats
            
        except Exception as e:
            print(f"[CloudHistory] 获取统计信息失败: {e}")
            return {
                'total_operations': 0,
                'by_type': {},
                'by_status': {},
                'recent_24h': 0,
                'recent_7d': 0
            }
    
    def clear_history(self, before_date=None):
        """清除历史记录
        
        Args:
            before_date: 清除此日期之前的记录 (YYYY-MM-DD)，None表示清除全部
        
        Returns:
            清除的记录数量
        """
        try:
            if before_date is None:
                # 清除全部
                self._save_history([])
                return -1  # 表示全部清除
            
            history = self._load_history()
            original_count = len(history)
            
            # 保留指定日期之后的记录
            filtered = [r for r in history if r.get('timestamp', '') >= before_date]
            
            self._save_history(filtered)
            
            return original_count - len(filtered)
            
        except Exception as e:
            print(f"[CloudHistory] 清除历史记录失败: {e}")
            return 0
    
    def _load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CloudHistory] 读取历史文件失败: {e}")
        
        return []
    
    def _save_history(self, history):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CloudHistory] 保存历史文件失败: {e}")
    
    def _generate_id(self):
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())[:8]

# ============================================

class DoubanHelper:
    """豆瓣API辅助类"""
    
    # 查询缓存
    _cache = {}
    
    @staticmethod
    def make_request(url):
        """发送豆瓣请求（不使用代理）"""
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Cookie', DOUBAN_COOKIE)
            req.add_header('Referer', 'https://movie.douban.com/')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                return html
        except Exception as e:
            print(f"豆瓣请求失败: {e}")
            return None
    
    @staticmethod
    def clean_title_for_search(title):
        """清理标题用于搜索"""
        # 移除常见的无用词
        noise_words = ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
        
        # 移除特殊字符但保留空格
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', title)
        
        # 移除多余空格
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    @staticmethod
    def search_with_query(query_title):
        """执行单次豆瓣搜索"""
        try:
            query = urllib.parse.quote(query_title)
            url = f"https://movie.douban.com/j/subject_suggest?q={query}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Cookie', DOUBAN_COOKIE)
            req.add_header('Referer', 'https://movie.douban.com/')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data and len(data) > 0:
                    result = data[0]
                    title_cn = result.get('title', '')
                    year = result.get('year', '')
                    
                    return {
                        'title': title_cn,
                        'year': year,
                        'douban_id': result.get('id')
                    }
        except Exception as e:
            print(f"  豆瓣查询出错: {e}")
        
        return None
    
    @staticmethod
    def search(title):
        """搜索豆瓣（多策略智能查询）"""
        # 检查缓存
        cache_key = title.lower()
        if cache_key in DoubanHelper._cache:
            print(f"  使用缓存结果")
            return DoubanHelper._cache[cache_key]
        
        print(f"豆瓣查询: {title}")
        
        # 策略1: 完整标题查询
        result = DoubanHelper.search_with_query(title)
        if result and result['title']:
            if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                print(f"✓ 完整标题匹配: {result['title']}")
                DoubanHelper._cache[cache_key] = result
                return result
        
        # 策略2: 清理后的标题查询
        cleaned_title = DoubanHelper.clean_title_for_search(title)
        if cleaned_title != title:
            print(f"  尝试清理标题: {cleaned_title}")
            result = DoubanHelper.search_with_query(cleaned_title)
            if result and result['title']:
                if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                    print(f"✓ 清理标题匹配: {result['title']}")
                    DoubanHelper._cache[cache_key] = result
                    return result
        
        # 策略3: 渐进式缩短标题（从后往前去掉单词）
        words = title.split()
        if len(words) > 3:
            # 尝试不同长度：80% -> 60% -> 40%
            for ratio in [0.8, 0.6, 0.4]:
                word_count = max(3, int(len(words) * ratio))
                short_title = ' '.join(words[:word_count])
                
                print(f"  尝试缩短标题({word_count}词): {short_title}")
                result = DoubanHelper.search_with_query(short_title)
                if result and result['title']:
                    if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                        print(f"✓ 缩短标题匹配: {result['title']}")
                        DoubanHelper._cache[cache_key] = result
                        return result
        
        # 策略4: 只保留前3个关键词
        if len(words) >= 3:
            key_title = ' '.join(words[:3])
            print(f"  尝试关键词: {key_title}")
            result = DoubanHelper.search_with_query(key_title)
            if result and result['title']:
                if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                    print(f"✓ 关键词匹配: {result['title']}")
                    DoubanHelper._cache[cache_key] = result
                    return result
        
        print(f"✗ 豆瓣未找到")
        DoubanHelper._cache[cache_key] = None
        return None

class TMDBHelper:
    """TMDB API辅助类"""
    
    # 查询缓存
    _cache = {}
    
    @staticmethod
    def make_request(url):
        """通过代理发送TMDB请求"""
        try:
            proxy_handler = urllib.request.ProxyHandler({
                'http': TMDB_PROXY,
                'https': TMDB_PROXY
            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"  TMDB请求失败: {e}")
            return None
    
    @staticmethod
    def search_tv(title, year=None, try_without_year=True):
        """搜索电视剧（支持多策略，返回完整元数据）"""
        query = urllib.parse.quote(title)
        url = f"{TMDB_BASE_URL}/search/tv?api_key={TMDB_API_KEY}&query={query}&language=zh-CN"
        
        if year:
            url += f"&first_air_date_year={year}"
        
        data = TMDBHelper.make_request(url)
        if data and data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            return {
                'title': result.get('name', title),
                'original_title': result.get('original_name', ''),
                'original_language': result.get('original_language', ''),
                'year': result.get('first_air_date', '')[:4] if result.get('first_air_date') else '',
                'tmdb_id': result.get('id'),
                'genre_ids': result.get('genre_ids', []),
                'origin_country': result.get('origin_country', [])
            }
        
        # 如果带年份查询失败，尝试不带年份
        if year and try_without_year:
            print(f"  TMDB尝试不带年份查询")
            return TMDBHelper.search_tv(title, year=None, try_without_year=False)
        
        return None
    
    @staticmethod
    def search_movie(title, year=None, try_without_year=True):
        """搜索电影（支持多策略，返回完整元数据）"""
        query = urllib.parse.quote(title)
        url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={query}&language=zh-CN"
        
        if year:
            url += f"&year={year}"
        
        data = TMDBHelper.make_request(url)
        if data and data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            return {
                'title': result.get('title', title),
                'original_title': result.get('original_title', ''),
                'original_language': result.get('original_language', ''),
                'year': result.get('release_date', '')[:4] if result.get('release_date') else '',
                'tmdb_id': result.get('id'),
                'genre_ids': result.get('genre_ids', [])
            }
        
        # 如果带年份查询失败，尝试不带年份
        if year and try_without_year:
            print(f"  TMDB尝试不带年份查询")
            return TMDBHelper.search_movie(title, year=None, try_without_year=False)
        
        return None
    
    @staticmethod
    def get_chinese_title(title, year=None, is_tv=False):
        """获取中文标题（优先豆瓣，失败后用TMDB，多策略查询）"""
        # 如果已经包含中文，直接返回
        if any('\u4e00' <= c <= '\u9fff' for c in title):
            return title, year
        
        # 检查缓存
        cache_key = f"{title}|{year}|{is_tv}".lower()
        if cache_key in TMDBHelper._cache:
            cached = TMDBHelper._cache[cache_key]
            print(f"使用缓存: {cached[0]}")
            return cached
        
        print(f"\n{'='*60}")
        print(f"查询中文标题: {title} ({year if year else '未知年份'})")
        print(f"类型: {'电视剧' if is_tv else '电影'}")
        print(f"{'='*60}")
        
        # 策略1: 优先尝试豆瓣（多策略）
        douban_result = DoubanHelper.search(title)
        if douban_result and douban_result['title']:
            chinese_title = douban_result['title']
            douban_year = douban_result['year']
            
            if any('\u4e00' <= c <= '\u9fff' for c in chinese_title):
                result = (chinese_title, year or douban_year)
                TMDBHelper._cache[cache_key] = result
                return result
        
        # 策略2: TMDB完整标题查询
        print(f"\nTMDB查询...")
        if is_tv:
            result = TMDBHelper.search_tv(title, year)
        else:
            result = TMDBHelper.search_movie(title, year)
        
        if result and result['title']:
            if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                print(f"✓ TMDB完整标题: {result['title']}")
                final_result = (result['title'], year or result['year'])
                TMDBHelper._cache[cache_key] = final_result
                return final_result
        
        # 策略3: TMDB渐进式缩短标题
        words = title.split()
        if len(words) > 3:
            for ratio in [0.7, 0.5, 0.3]:
                word_count = max(3, int(len(words) * ratio))
                short_title = ' '.join(words[:word_count])
                
                print(f"  TMDB缩短标题({word_count}词): {short_title}")
                
                if is_tv:
                    result = TMDBHelper.search_tv(short_title, year)
                else:
                    result = TMDBHelper.search_movie(short_title, year)
                
                if result and result['title']:
                    if any('\u4e00' <= c <= '\u9fff' for c in result['title']):
                        print(f"✓ TMDB缩短标题匹配: {result['title']}")
                        final_result = (result['title'], year or result['year'])
                        TMDBHelper._cache[cache_key] = final_result
                        return final_result
        
        # 策略4: 尝试原标题（可能TMDB返回了英文但有效）
        if result:
            print(f"⚠ TMDB返回英文标题，使用原标题: {title}")
            final_result = (title, year or result.get('year', year))
            TMDBHelper._cache[cache_key] = final_result
            return final_result
        
        # 所有策略失败
        print(f"✗ 所有查询失败，保留原标题: {title}")
        final_result = (title, year)
        TMDBHelper._cache[cache_key] = final_result
        return final_result
    
    @staticmethod
    def get_metadata_with_category(title, year=None, is_tv=False):
        """获取完整元数据并进行分类"""
        # 如果已经包含中文，直接返回基本信息
        if any('\u4e00' <= c <= '\u9fff' for c in title):
            return {
                'title': title,
                'year': year,
                'category': None,
                'metadata': {}
            }
        
        print(f"\n{'='*60}")
        print(f"查询元数据: {title} ({year if year else '未知年份'})")
        print(f"类型: {'电视剧' if is_tv else '电影'}")
        print(f"{'='*60}")
        
        # 优先尝试TMDB获取完整元数据
        if is_tv:
            result = TMDBHelper.search_tv(title, year)
        else:
            result = TMDBHelper.search_movie(title, year)
        
        if not result:
            # TMDB失败，尝试简化标题
            words = title.split()
            if len(words) > 3:
                for ratio in [0.7, 0.5, 0.3]:
                    word_count = max(3, int(len(words) * ratio))
                    short_title = ' '.join(words[:word_count])
                    print(f"  尝试缩短标题({word_count}词): {short_title}")
                    
                    if is_tv:
                        result = TMDBHelper.search_tv(short_title, year)
                    else:
                        result = TMDBHelper.search_movie(short_title, year)
                    
                    if result:
                        break
        
        if result:
            chinese_title = result['title']
            
            # 如果TMDB返回的还是英文，尝试豆瓣
            if not any('\u4e00' <= c <= '\u9fff' for c in chinese_title):
                print(f"  TMDB返回英文，尝试豆瓣...")
                douban_result = DoubanHelper.search(title)
                if douban_result and douban_result['title']:
                    if any('\u4e00' <= c <= '\u9fff' for c in douban_result['title']):
                        chinese_title = douban_result['title']
                        print(f"✓ 豆瓣找到: {chinese_title}")
            
            # 进行分类
            category = TMDBHelper.classify_media(result, is_tv)
            
            print(f"✓ 标题: {chinese_title}")
            print(f"✓ 分类: {category}")
            
            return {
                'title': chinese_title,
                'year': year or result.get('year', ''),
                'category': category,
                'metadata': result
            }
        
        # 所有查询失败
        print(f"✗ 查询失败，保留原标题")
        return {
            'title': title,
            'year': year,
            'category': '未分类' if is_tv else '外语电影',
            'metadata': {}
        }
    
    @staticmethod
    def classify_media(metadata, is_tv):
        """根据元数据进行分类"""
        media_type = 'tv' if is_tv else 'movie'
        config = CATEGORY_CONFIG.get(media_type, {})
        
        genre_ids = [str(gid) for gid in metadata.get('genre_ids', [])]
        origin_country = metadata.get('origin_country', [])
        original_language = metadata.get('original_language', '').lower()
        
        print(f"  元数据: genre_ids={genre_ids}, origin_country={origin_country}, language={original_language}")
        
        # 按顺序匹配分类规则
        for category_name, rules in config.items():
            if not rules:  # 空规则是默认分类，跳过
                continue
            
            match = True
            
            # 检查 genre_ids
            if 'genre_ids' in rules:
                required_genres = rules['genre_ids']
                if not any(gid in genre_ids for gid in required_genres):
                    match = False
            
            # 检查 origin_country
            if match and 'origin_country' in rules:
                required_countries = rules['origin_country']
                if not any(country in origin_country for country in required_countries):
                    match = False
            
            # 检查 original_language
            if match and 'original_language' in rules:
                required_languages = rules['original_language']
                if original_language not in required_languages:
                    match = False
            
            if match:
                return category_name
        
        # 返回默认分类
        default_category = '未分类' if is_tv else '外语电影'
        for category_name, rules in config.items():
            if not rules:  # 空规则是默认分类
                return category_name
        
        return default_category

# ============ Linux/NAS优化函数 ============

def sanitize_filename(filename):
    """
    清理文件名，确保跨文件系统兼容
    适用于 ext4, btrfs, ZFS, NTFS, FAT32 等
    """
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # 移除首尾空格和点
    filename = filename.strip('. ')
    
    # 限制文件名长度（大多数文件系统限制255字节）
    if len(filename.encode('utf-8')) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext.encode('utf-8')) - 10
        # 按字符截断，确保不会截断UTF-8字符
        while len(name.encode('utf-8')) > max_name_len:
            name = name[:-1]
        filename = name + ext
    
    return filename if filename else 'unnamed'

def check_path_permissions(path):
    """检查路径的读写权限"""
    if not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent and os.path.exists(parent):
            path = parent
        else:
            return True  # 路径不存在，无法检查
    
    if not os.access(path, os.R_OK):
        raise PermissionError(f"无读取权限: {path}")
    
    if os.path.isdir(path) and not os.access(path, os.W_OK):
        raise PermissionError(f"无写入权限: {path}")
    
    return True


# ============================================
# 媒体库管理模块
# ============================================

class MediaLibraryDetector:
    """媒体库目录结构检测器
    
    自动检测媒体库中的电影和电视剧目录，支持中英文命名
    """
    
    # 支持的目录名称映射（优先级从高到低）
    MOVIE_DIR_NAMES = ['电影', 'Movies', 'Movie', '电影库']
    TV_DIR_NAMES = ['电视剧', 'TV Shows', 'TV', 'Series', '剧集', '电视剧库']
    
    def __init__(self, media_library_path):
        """
        Args:
            media_library_path: 用户选择的媒体库根路径（可以是任意名称的目录）
                               例如: /vol02/1000-1-b23abde7/115
                                    /mnt/storage/media
                                    /home/user/videos
        """
        self.media_library_path = media_library_path
        self.movie_dir = None
        self.tv_dir = None
    
    def detect_structure(self):
        """检测媒体库目录结构
        
        Returns:
            dict: {
                'movie_dir': '电影' or 'Movies' or None,
                'tv_dir': '电视剧' or 'TV Shows' or None,
                'movie_path': '/path/to/电影',
                'tv_path': '/path/to/电视剧'
            }
        """
        result = {
            'movie_dir': None,
            'tv_dir': None,
            'movie_path': None,
            'tv_path': None
        }
        
        if not os.path.exists(self.media_library_path):
            print(f"⚠️  媒体库路径不存在: {self.media_library_path}")
            return result
        
        try:
            # 列出所有子目录
            subdirs = [d for d in os.listdir(self.media_library_path) 
                       if os.path.isdir(os.path.join(self.media_library_path, d))]
            
            print(f"📁 扫描媒体库: {self.media_library_path}")
            print(f"   发现子目录: {subdirs}")
            
            # 检测电影目录（优先中文）
            for name in self.MOVIE_DIR_NAMES:
                if name in subdirs:
                    result['movie_dir'] = name
                    result['movie_path'] = os.path.join(self.media_library_path, name)
                    print(f"✓ 检测到电影目录: {name}")
                    break
            
            # 检测电视剧目录（优先中文）
            for name in self.TV_DIR_NAMES:
                if name in subdirs:
                    result['tv_dir'] = name
                    result['tv_path'] = os.path.join(self.media_library_path, name)
                    print(f"✓ 检测到电视剧目录: {name}")
                    break
            
            if not result['movie_dir']:
                print(f"⚠️  未检测到电影目录")
            if not result['tv_dir']:
                print(f"⚠️  未检测到电视剧目录")
                
        except PermissionError:
            print(f"❌ 没有权限访问媒体库目录: {self.media_library_path}")
        except Exception as e:
            print(f"❌ 检测媒体库结构失败: {str(e)}")
        
        return result
    
    def create_default_structure(self, language='zh'):
        """创建默认目录结构
        
        Args:
            language: 'zh' for Chinese, 'en' for English
            
        Returns:
            dict: 创建的目录结构信息
        """
        if language == 'zh':
            movie_dir = '电影'
            tv_dir = '电视剧'
        else:
            movie_dir = 'Movies'
            tv_dir = 'TV Shows'
        
        movie_path = os.path.join(self.media_library_path, movie_dir)
        tv_path = os.path.join(self.media_library_path, tv_dir)
        
        try:
            os.makedirs(movie_path, exist_ok=True)
            os.makedirs(tv_path, exist_ok=True)
            
            print(f"✓ 创建电影目录: {movie_path}")
            print(f"✓ 创建电视剧目录: {tv_path}")
            
            return {
                'movie_dir': movie_dir,
                'tv_dir': tv_dir,
                'movie_path': movie_path,
                'tv_path': tv_path
            }
        except PermissionError:
            raise Exception(f"没有权限创建目录: {self.media_library_path}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                raise Exception(f"磁盘空间不足: {self.media_library_path}")
            raise Exception(f"创建目录失败: {str(e)}")


class SecondaryClassificationDetector:
    """二级分类目录检测器
    
    检测已存在的二级分类目录（如国产剧、欧美剧等），支持精确和模糊匹配
    """
    
    def __init__(self, base_path):
        """
        Args:
            base_path: 电影或电视剧的基础路径
        """
        self.base_path = base_path
        self.existing_categories = self._scan_existing_categories()
    
    def _scan_existing_categories(self):
        """扫描已存在的分类目录
        
        Returns:
            dict: {
                '国产剧': '国产剧',  # 配置名 -> 实际目录名
                '欧美剧': '欧美剧',
                ...
            }
        """
        if not os.path.exists(self.base_path):
            print(f"⚠️  基础路径不存在: {self.base_path}")
            return {}
        
        existing = {}
        
        try:
            subdirs = [d for d in os.listdir(self.base_path) 
                       if os.path.isdir(os.path.join(self.base_path, d))]
            
            print(f"📂 扫描分类目录: {self.base_path}")
            print(f"   发现分类: {subdirs}")
            
            # 建立映射关系
            for subdir in subdirs:
                # 精确匹配
                existing[subdir] = subdir
                
                # 模糊匹配（去除常见后缀）
                normalized = subdir.replace('电视剧', '').replace('电影', '').strip()
                if normalized and normalized != subdir:
                    existing[normalized] = subdir
            
            print(f"✓ 建立分类映射: {len(existing)} 个")
            
        except PermissionError:
            print(f"❌ 没有权限访问目录: {self.base_path}")
        except Exception as e:
            print(f"❌ 扫描分类目录失败: {str(e)}")
        
        return existing
    
    def get_category_dir(self, category_name):
        """获取分类目录名称
        
        Args:
            category_name: 配置中的分类名称（如 '国产剧'）
        
        Returns:
            str: 实际的目录名称，如果不存在则返回配置名称
        """
        # 精确匹配
        if category_name in self.existing_categories:
            actual_name = self.existing_categories[category_name]
            print(f"✓ 找到分类目录: {category_name} -> {actual_name}")
            return actual_name
        
        # 模糊匹配
        for key, value in self.existing_categories.items():
            if category_name in key or key in category_name:
                print(f"✓ 模糊匹配分类目录: {category_name} -> {value}")
                return value
        
        # 不存在，返回配置名称
        print(f"⚠️  分类目录不存在，将创建: {category_name}")
        return category_name
    
    def ensure_category_dir(self, category_name):
        """确保分类目录存在
        
        Args:
            category_name: 分类名称
        
        Returns:
            str: 分类目录的完整路径
        """
        dir_name = self.get_category_dir(category_name)
        dir_path = os.path.join(self.base_path, dir_name)
        
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✓ 创建分类目录: {dir_path}")
                # 更新缓存
                self.existing_categories[category_name] = dir_name
            except PermissionError:
                raise Exception(f"没有权限创建目录: {dir_path}")
            except OSError as e:
                if e.errno == 28:  # No space left on device
                    raise Exception(f"磁盘空间不足")
                raise Exception(f"创建目录失败: {str(e)}")
        
        return dir_path
    
    def refresh_cache(self):
        """刷新分类目录缓存"""
        self.existing_categories = self._scan_existing_categories()


class PathGenerator:
    """路径生成器
    
    生成正确的媒体文件路径，包含二级分类目录结构
    """
    
    def __init__(self, media_library_path, language='zh'):
        """
        Args:
            media_library_path: 媒体库根路径
            language: 语言偏好 ('zh' 或 'en')
        """
        self.media_library_path = media_library_path
        self.language = language
        self.detector = MediaLibraryDetector(media_library_path)
        self.structure = self.detector.detect_structure()
        
        # 如果没有检测到，创建默认结构
        if not self.structure['movie_path'] or not self.structure['tv_path']:
            print(f"⚠️  媒体库结构不完整，创建默认结构")
            self.structure = self.detector.create_default_structure(language)
        
        # 初始化分类检测器
        self.movie_classifier = SecondaryClassificationDetector(
            self.structure['movie_path']
        )
        self.tv_classifier = SecondaryClassificationDetector(
            self.structure['tv_path']
        )
    
    def generate_path(self, metadata):
        """生成完整的文件路径
        
        Args:
            metadata: 文件元数据，包含:
                - type: 'movie' or 'tv'
                - title: 标题
                - year: 年份
                - season: 季数 (仅电视剧)
                - season_no_zero: 季数（无前导零）
                - episode: 集数 (仅电视剧)
                - season_episode: 季集编号 (如 S01E08)
                - category: 二级分类
                - fileExt: 文件扩展名
        
        Returns:
            tuple: (完整路径, 相对路径)
        """
        is_tv = metadata.get('type') == 'tv'
        category = metadata.get('category', '未分类' if is_tv else '外语电影')
        
        # 1. 选择基础路径
        if is_tv:
            base_path = self.structure['tv_path']
            classifier = self.tv_classifier
            base_dir_name = self.structure['tv_dir']
        else:
            base_path = self.structure['movie_path']
            classifier = self.movie_classifier
            base_dir_name = self.structure['movie_dir']
        
        # 2. 确定二级分类目录
        category_path = classifier.ensure_category_dir(category)
        category_dir_name = classifier.get_category_dir(category)
        
        # 3. 生成剧名/电影名目录
        title = metadata.get('title', 'Unknown')
        year = metadata.get('year', '')
        if year:
            title_dir = f"{title} ({year})"
        else:
            title_dir = title
        
        # 4. 构建路径
        if is_tv:
            # 电视剧: 分类/剧名/Season X/文件名
            season = metadata.get('season_no_zero', metadata.get('season', '1'))
            season_dir = f"Season {season}"
            
            # 生成文件名: 剧名 - S01E08 - 第 08 集.mkv
            episode = metadata.get('episode', '')
            season_episode = metadata.get('season_episode', f"S{int(season):02d}E01")
            
            filename = f"{title} - {season_episode}"
            if episode:
                filename += f" - 第 {episode} 集"
            filename += metadata.get('fileExt', '.mkv')
            
            # 完整路径
            full_path = os.path.join(
                category_path,
                title_dir,
                season_dir,
                filename
            )
            
            # 相对路径（相对于媒体库）
            relative_path = os.path.join(
                base_dir_name,
                category_dir_name,
                title_dir,
                season_dir,
                filename
            )
        else:
            # 电影: 分类/电影名/文件名
            # 文件名: 电影名 (年份).mkv
            filename = title_dir + metadata.get('fileExt', '.mkv')
            
            full_path = os.path.join(
                category_path,
                title_dir,
                filename
            )
            
            relative_path = os.path.join(
                base_dir_name,
                category_dir_name,
                title_dir,
                filename
            )
        
        print(f"✓ 生成路径: {relative_path}")
        
        return full_path, relative_path


class ConfigManager:
    """配置管理器
    
    管理新旧配置的兼容性，支持配置迁移
    """
    
    def __init__(self, config):
        """
        Args:
            config: 配置字典
        """
        self.config = config
    
    def get_media_library_path(self):
        """获取媒体库路径
        
        Returns:
            str: 媒体库路径，如果没有配置则返回 None
        """
        # 新配置方式
        if 'media_library_path' in self.config:
            return self.config['media_library_path']
        
        # 旧配置方式（兼容）
        movie_path = self.config.get('movie_output_path', '')
        tv_path = self.config.get('tv_output_path', '')
        
        if movie_path and tv_path:
            # 尝试找到共同的父目录
            movie_parent = os.path.dirname(movie_path)
            tv_parent = os.path.dirname(tv_path)
            
            if movie_parent == tv_parent:
                print(f"✓ 从旧配置推断媒体库路径: {movie_parent}")
                return movie_parent
        
        return None
    
    def has_new_config(self):
        """检查是否使用新配置方式
        
        Returns:
            bool: True 如果使用新配置
        """
        return 'media_library_path' in self.config
    
    def has_old_config(self):
        """检查是否使用旧配置方式
        
        Returns:
            bool: True 如果使用旧配置
        """
        return ('movie_output_path' in self.config and 
                'tv_output_path' in self.config)
    
    def migrate_to_new_config(self):
        """迁移旧配置到新配置
        
        Returns:
            dict: 新配置
        """
        new_config = self.config.copy()
        
        media_library_path = self.get_media_library_path()
        if media_library_path and not self.has_new_config():
            new_config['media_library_path'] = media_library_path
            print(f"✓ 配置已迁移到新格式")
            print(f"   媒体库路径: {media_library_path}")
            
            # 可选：保留旧配置作为备份
            # new_config['_backup_movie_output_path'] = self.config.get('movie_output_path')
            # new_config['_backup_tv_output_path'] = self.config.get('tv_output_path')
        
        return new_config
    
    def get_language_preference(self):
        """获取语言偏好
        
        Returns:
            str: 'zh' 或 'en'
        """
        return self.config.get('preferred_language', 'zh')
    
    def should_migrate(self):
        """检查是否应该提示用户迁移配置
        
        Returns:
            bool: True 如果应该迁移
        """
        # 如果有旧配置但没有新配置，建议迁移
        return self.has_old_config() and not self.has_new_config()


def retry_on_error(max_retries=NETWORK_RETRY_COUNT, delay=NETWORK_RETRY_DELAY):
    """
    网络/文件系统操作重试装饰器
    适用于 NFS, SMB/CIFS 等网络文件系统
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OSError, IOError, PermissionError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        print(f"⚠️  操作失败，{delay}秒后重试... ({attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(delay)
                    else:
                        print(f"❌ 操作失败，已达最大重试次数: {str(e)}")
            raise last_error
        return wrapper
    return decorator

@retry_on_error()
def safe_rename(old_path, new_path):
    """
    安全的文件重命名/移动操作
    支持跨文件系统移动，自动处理网络延迟
    """
    # 确保目标目录存在
    target_dir = os.path.dirname(new_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        time.sleep(0.3)  # 等待目录创建同步
    
    # 执行重命名/移动
    os.rename(old_path, new_path)
    
    # 网络文件系统延迟
    time.sleep(NETWORK_OP_DELAY)
    
    # 验证操作成功
    if not os.path.exists(new_path):
        raise IOError(f"文件移动后未找到: {new_path}")
    
    return True

@retry_on_error()
def safe_remove(file_path):
    """
    安全的文件删除操作
    自动处理网络延迟和权限问题
    """
    if not os.path.exists(file_path):
        return True  # 文件已不存在
    
    os.remove(file_path)
    time.sleep(0.5)  # 等待删除同步
    
    return not os.path.exists(file_path)

def resolve_symlink(path):
    """
    解析符号链接，返回真实路径
    NAS系统常用符号链接管理存储
    """
    try:
        return os.path.realpath(path)
    except (OSError, ValueError):
        return path

def get_filesystem_type(path):
    """
    获取文件系统类型（Linux）
    用于针对不同文件系统优化操作
    """
    try:
        import subprocess
        result = subprocess.run(
            ['df', '-T', path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 1:
                    return parts[1]  # 文件系统类型
    except:
        pass
    return 'unknown'

# ============================================

class MediaHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('public/index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/style.css':
            try:
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                with open('public/style.css', 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404)
        elif self.path == '/logo.svg':
            try:
                self.send_response(200)
                self.send_header('Content-type', 'image/svg+xml')
                self.end_headers()
                with open('public/logo.svg', 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404)
        elif self.path == '/favicon.svg':
            try:
                self.send_response(200)
                self.send_header('Content-type', 'image/svg+xml')
                self.end_headers()
                with open('public/favicon.svg', 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404)
        else:
            super().do_GET()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/api/scan':
                self.handle_scan(data)
            elif self.path == '/api/rename':
                self.handle_rename(data)
            elif self.path == '/api/smart-rename':
                self.handle_smart_rename(data)
            elif self.path == '/api/parse-filename':
                self.handle_parse_filename(data)
            elif self.path == '/api/delete':
                self.handle_delete(data)
            elif self.path == '/api/scan-all':
                self.handle_scan_all(data)
            elif self.path == '/api/browse-folders':
                self.handle_browse_folders(data)
            elif self.path == '/api/cleanup':
                self.handle_cleanup(data)
            elif self.path == '/api/get-settings':
                self.handle_get_settings(data)
            elif self.path == '/api/save-settings':
                self.handle_save_settings(data)
            elif self.path == '/api/get-version':
                self.handle_get_version(data)
            elif self.path == '/api/check-update':
                self.handle_check_update(data)
            elif self.path == '/api/update':
                self.handle_update(data)
            elif self.path == '/api/force-update':
                self.handle_force_update(data)
            elif self.path == '/api/rollback':
                self.handle_rollback(data)
            elif self.path == '/api/update-history':
                self.handle_update_history(data)
            elif self.path == '/api/cloud/verify-cookie':
                self.handle_cloud_verify_cookie(data)
            elif self.path == '/api/cloud/list-files':
                self.handle_cloud_list_files(data)
            elif self.path == '/api/cloud/scan':
                self.handle_cloud_scan(data)
            elif self.path == '/api/cloud/smart-organize':
                self.handle_cloud_smart_organize(data)
            elif self.path == '/api/cloud/generate-qrcode':
                self.handle_cloud_generate_qrcode(data)
            elif self.path == '/api/cloud/check-qrcode':
                self.handle_cloud_check_qrcode(data)
            elif self.path == '/api/cloud/history':
                self.handle_cloud_history(data)
            elif self.path == '/api/cloud/history/stats':
                self.handle_cloud_history_stats(data)
            elif self.path == '/api/qrcode/start':
                self.handle_qrcode_start(data)
            elif self.path == '/api/qrcode/check':
                self.handle_qrcode_check(data)
            elif self.path == '/api/qrcode/finish':
                self.handle_qrcode_finish(data)
            else:
                self.send_error(404)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_scan(self, data):
        """扫描文件夹，只返回支持的媒体和字幕文件"""
        folder_path = data.get('folderPath', '')
        
        if not folder_path:
            self.send_json_response({'error': '请提供文件夹路径'}, 400)
            return
        
        if not os.path.isdir(folder_path):
            self.send_json_response({'error': '路径不是有效的文件夹'}, 400)
            return
        
        files = []
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    file_type = None
                    
                    if ext in MEDIA_EXTENSIONS:
                        file_type = 'media'
                    elif ext in SUBTITLE_EXTENSIONS:
                        file_type = 'subtitle'
                    
                    if file_type:
                        stat = os.stat(file_path)
                        files.append({
                            'name': filename,
                            'path': file_path,
                            'type': file_type,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        })
            
            self.send_json_response({'files': files, 'folderPath': folder_path})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def scan_directory_recursive(self, folder_path, auto_delete=True):
        """递归扫描文件夹（针对网盘挂载优化）"""
        supported_files = []
        unsupported_files = []
        deleted_files = []
        delete_errors = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    try:
                        # 网盘文件可能需要更长的超时时间
                        stat = os.stat(file_path)
                        
                        file_info = {
                            'name': filename,
                            'path': file_path,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        }
                        
                        if ext in MEDIA_EXTENSIONS:
                            file_info['type'] = 'media'
                            supported_files.append(file_info)
                        elif ext in SUBTITLE_EXTENSIONS:
                            file_info['type'] = 'subtitle'
                            supported_files.append(file_info)
                        else:
                            # 不支持的文件
                            file_info['type'] = 'unsupported'
                            unsupported_files.append(file_info)
                            
                            # 自动删除不支持的文件
                            if auto_delete:
                                try:
                                    os.remove(file_path)
                                    deleted_files.append(filename)
                                except Exception as e:
                                    delete_errors.append({
                                        'file': filename,
                                        'error': str(e)
                                    })
                    except OSError as e:
                        # 网盘挂载可能出现临时不可访问的情况
                        delete_errors.append({
                            'file': filename,
                            'error': f'文件访问失败（可能是网盘连接问题）: {str(e)}'
                        })
                    except Exception as e:
                        delete_errors.append({
                            'file': filename,
                            'error': str(e)
                        })
        except Exception as e:
            # 扫描过程中的错误
            delete_errors.append({
                'file': 'scan_error',
                'error': f'扫描失败: {str(e)}'
            })
        
        return supported_files, unsupported_files, deleted_files, delete_errors
    
    def handle_scan_all(self, data):
        """扫描文件夹，自动删除不支持的文件，返回支持的文件"""
        folder_path = data.get('folderPath', '')
        auto_delete = data.get('autoDelete', True)  # 默认自动删除
        recursive = data.get('recursive', True)  # 默认递归扫描
        
        if not folder_path:
            self.send_json_response({'error': '请提供文件夹路径'}, 400)
            return
        
        if not os.path.isdir(folder_path):
            self.send_json_response({'error': '路径不是有效的文件夹'}, 400)
            return
        
        try:
            if recursive:
                supported_files, unsupported_files, deleted_files, delete_errors = \
                    self.scan_directory_recursive(folder_path, auto_delete)
            else:
                # 原有的单层扫描逻辑
                supported_files = []
                unsupported_files = []
                deleted_files = []
                delete_errors = []
                
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(filename)[1].lower()
                        stat = os.stat(file_path)
                        
                        file_info = {
                            'name': filename,
                            'path': file_path,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        }
                        
                        if ext in MEDIA_EXTENSIONS:
                            file_info['type'] = 'media'
                            supported_files.append(file_info)
                        elif ext in SUBTITLE_EXTENSIONS:
                            file_info['type'] = 'subtitle'
                            supported_files.append(file_info)
                        else:
                            # 不支持的文件
                            file_info['type'] = 'unsupported'
                            unsupported_files.append(file_info)
                            
                            # 自动删除不支持的文件
                            if auto_delete:
                                try:
                                    os.remove(file_path)
                                    deleted_files.append(filename)
                                except Exception as e:
                                    delete_errors.append({
                                        'file': filename,
                                        'error': str(e)
                                    })
            
            self.send_json_response({
                'supported': supported_files,
                'unsupported': unsupported_files,
                'deleted': deleted_files,
                'deleteErrors': delete_errors,
                'folderPath': folder_path
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_browse_folders(self, data):
        """浏览文件夹"""
        folder_path = data.get('folderPath', '/')
        
        try:
            if not os.path.exists(folder_path):
                self.send_json_response({'error': '路径不存在'}, 400)
                return
            
            if not os.path.isdir(folder_path):
                self.send_json_response({'error': '不是有效的文件夹'}, 400)
                return
            
            folders = []
            try:
                items = os.listdir(folder_path)
                for item in sorted(items):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isdir(item_path):
                        folders.append({
                            'name': item,
                            'path': item_path
                        })
            except PermissionError:
                pass  # 跳过没有权限的文件夹
            
            # 获取父目录
            parent_path = os.path.dirname(folder_path) if folder_path != '/' else None
            
            self.send_json_response({
                'currentPath': folder_path,
                'parentPath': parent_path,
                'folders': folders
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_delete(self, data):
        """删除文件（针对网络文件系统优化，支持重试）"""
        file_path = data.get('filePath', '')
        
        if not file_path:
            self.send_json_response({'error': '请提供文件路径'}, 400)
            return
        
        try:
            if not os.path.exists(file_path):
                self.send_json_response({'error': '文件不存在'}, 400)
                return
            
            # 使用优化的删除函数（支持网络文件系统和重试）
            safe_remove(file_path)
            
            self.send_json_response({'success': True, 'message': '文件已删除'})
                
        except PermissionError as e:
            self.send_json_response({'error': f'权限不足: {str(e)}'}, 500)
        except OSError as e:
            self.send_json_response({'error': f'文件系统操作失败: {str(e)}'}, 500)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def compare_files(self, file1_path, file2_path):
        """比较两个文件，返回更好的文件路径
        
        返回值:
        1 = file1更好（新文件）
        2 = file2更好（旧文件）
        0 = 完全相同或无法比较
        """
        try:
            stat1 = os.stat(file1_path)
            stat2 = os.stat(file2_path)
            
            # 提取文件名中的清晰度信息
            name1 = os.path.basename(file1_path).lower()
            name2 = os.path.basename(file2_path).lower()
            
            # 计算质量分数
            score1 = 0
            score2 = 0
            
            # 分辨率评分
            resolution_scores = {
                '4k': 2160, '2160p': 2160,
                '1080p': 1080, '720p': 720, '480p': 480
            }
            for res, score in resolution_scores.items():
                if res in name1:
                    score1 += score
                if res in name2:
                    score2 += score
            
            # 来源质量评分
            source_scores = {
                'remux': 100, 'bluray': 80, 'blu-ray': 80, 'bd': 80,
                'web-dl': 60, 'webdl': 60, 'webrip': 40, 'hdrip': 20
            }
            for source, score in source_scores.items():
                if source in name1:
                    score1 += score
                if source in name2:
                    score2 += score
            
            # 编码评分
            if 'h265' in name1 or 'hevc' in name1 or 'x265' in name1:
                score1 += 10
            if 'h265' in name2 or 'hevc' in name2 or 'x265' in name2:
                score2 += 10
            
            print(f"    质量评分: 新文件={score1}分, 旧文件={score2}分")
            
            # 如果评分不同，返回评分高的
            if score1 > score2:
                return 1
            elif score2 > score1:
                return 2
            
            # 评分相同，比较文件大小
            size_diff = abs(stat1.st_size - stat2.st_size)
            size_threshold = 1024 * 1024  # 1MB差异阈值
            
            print(f"    文件大小: 新文件={stat1.st_size / (1024*1024):.1f}MB, 旧文件={stat2.st_size / (1024*1024):.1f}MB")
            
            if size_diff < size_threshold:
                # 文件大小差异小于1MB，认为是相同文件
                print(f"    判断: 文件质量和大小基本相同（差异<1MB）")
                return 0
            elif stat1.st_size > stat2.st_size:
                print(f"    判断: 新文件更大")
                return 1
            else:
                print(f"    判断: 旧文件更大")
                return 2
            
        except Exception as e:
            print(f"  ❌ 文件比较失败: {e}")
            return 0
    
    def handle_rename(self, data):
        old_path = data.get('oldPath', '')
        new_name = data.get('newName', '')
        new_full_path = data.get('newPath', '')  # 支持完整路径（用于移动+重命名）
        conflict_strategy = data.get('conflictStrategy', 'auto')  # auto, skip, replace, keep_both
        
        if not old_path:
            self.send_json_response({'error': '请提供原路径'}, 400)
            return
        
        try:
            # 如果提供了完整路径，使用完整路径（移动+重命名）
            if new_full_path:
                new_path = new_full_path
                # 确保目标目录存在
                target_dir = os.path.dirname(new_path)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
            elif new_name:
                # 只提供新文件名，在同目录重命名
                directory = os.path.dirname(old_path)
                new_path = os.path.join(directory, new_name)
            else:
                self.send_json_response({'error': '请提供新文件名或新路径'}, 400)
                return
            
            # 检查新文件名是否已存在
            if os.path.exists(new_path):
                print(f"⚠️  文件冲突: {new_path}")
                
                # 处理冲突策略
                if conflict_strategy == 'skip':
                    # 跳过，不处理
                    self.send_json_response({
                        'success': True, 
                        'skipped': True,
                        'reason': '目标文件已存在，已跳过'
                    })
                    return
                
                elif conflict_strategy == 'replace':
                    # 直接替换
                    print(f"  策略: 直接替换")
                    os.remove(new_path)
                    
                elif conflict_strategy == 'keep_both':
                    # 保留两个版本，添加后缀
                    base, ext = os.path.splitext(new_path)
                    counter = 1
                    while os.path.exists(f"{base}.v{counter}{ext}"):
                        counter += 1
                    new_path = f"{base}.v{counter}{ext}"
                    print(f"  策略: 保留两个版本，新文件名: {os.path.basename(new_path)}")
                    
                elif conflict_strategy == 'auto':
                    # 自动比较，保留更好的版本
                    print(f"  策略: 自动比较质量")
                    better = self.compare_files(old_path, new_path)
                    
                    if better == 1:
                        # 新文件更好，替换旧文件
                        print(f"  ✓ 决策: 新文件质量更好，替换旧文件")
                        os.remove(new_path)
                    elif better == 2:
                        # 旧文件更好，跳过
                        print(f"  ✓ 决策: 旧文件质量更好，保留旧文件")
                        self.send_json_response({
                            'success': True,
                            'skipped': True,
                            'reason': '旧文件质量更好，已保留旧文件'
                        })
                        return
                    else:
                        # 文件质量完全相同，跳过（避免重复处理）
                        print(f"  ✓ 决策: 文件质量和大小基本相同，保留旧文件（避免重复操作）")
                        self.send_json_response({
                            'success': True,
                            'skipped': True,
                            'reason': '文件质量和大小基本相同，已保留旧文件'
                        })
                        return
                else:
                    # 未知策略，返回错误
                    self.send_json_response({'error': '目标文件已存在'}, 400)
                    return
            
            # 使用优化的重命名函数（支持网络文件系统和重试）
            safe_rename(old_path, new_path)
            
            self.send_json_response({'success': True, 'newPath': new_path})
                
        except PermissionError as e:
            self.send_json_response({'error': f'权限不足: {str(e)}'}, 500)
        except OSError as e:
            self.send_json_response({'error': f'文件系统操作失败: {str(e)}'}, 500)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_parse_filename(self, data):
        """解析文件名，提取元数据"""
        filename = data.get('filename', '')
        parent_folder = data.get('parentFolder', '')
        
        try:
            metadata = self.parse_media_filename(filename, parent_folder)
            self.send_json_response({'metadata': metadata})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def parse_folder_name(self, folder_name):
        """从文件夹名提取标题和年份"""
        original_name = folder_name
        
        # 移除 TMDB ID 标记 {tmdbid-xxxxx}
        folder_name = re.sub(r'\s*\{tmdbid-\d+\}', '', folder_name)
        
        # 移除季数标记 [S1], [S01] 等
        folder_name = re.sub(r'\s*\[S\d+\]', '', folder_name, flags=re.IGNORECASE)
        
        # 移除末尾的制作组标记 [xxx]
        folder_name = re.sub(r'\s*\[[^\]]+\]\s*$', '', folder_name)
        
        # 格式1：[标题].其他信息.年份（如：[湖南卫视 去"湘"当有味的地方 第三季].HNSTV...2025）
        # 检查方括号内是否包含中文或空格（真正的标题）
        bracket_title_pattern = r'^\[([^\]]+)\]'
        bracket_title_match = re.match(bracket_title_pattern, folder_name)
        
        if bracket_title_match:
            potential_title = bracket_title_match.group(1).strip()
            
            # 判断是否为真正的标题（包含中文、空格或长度>10）
            # 排除来源标记如：BDrip, BluRay, WEB-DL等
            source_keywords = ['bdrip', 'bluray', 'web-dl', 'webrip', 'hdtv', 'dvdrip', 'hdrip']
            is_source = potential_title.lower() in source_keywords
            
            if not is_source and (len(potential_title) > 10 or ' ' in potential_title or any('\u4e00' <= c <= '\u9fff' for c in potential_title)):
                # 这是真正的标题
                title = potential_title
                # 从剩余部分提取年份
                remaining = folder_name[bracket_title_match.end():]
                year_match = re.search(r'\.(\d{4})\.', remaining)
                year = year_match.group(1) if year_match else ''
                return title, year
            else:
                # 这是来源标记，移除后继续处理
                folder_name = folder_name[bracket_title_match.end():].strip()
        
        # 格式2：[年份][标题][其他信息]
        bracket_pattern = r'^\[(\d{4})\]\[([^\]]+)\]'
        bracket_match = re.match(bracket_pattern, folder_name)
        
        if bracket_match:
            year = bracket_match.group(1)
            title = bracket_match.group(2).strip()
            return title, year
        
        # 格式3：年份.标题.其他信息
        dot_pattern = r'^(\d{4})[\.\s]+([^\.\s]+)'
        dot_match = re.match(dot_pattern, folder_name)
        
        if dot_match:
            year = dot_match.group(1)
            title = dot_match.group(2).strip()
            return title, year
        
        # 格式4：标题 (年份)
        year_match = re.search(r'\((\d{4})\)', folder_name)
        year = year_match.group(1) if year_match else ''
        
        # 提取标题（移除年份部分）
        if year:
            title = re.sub(r'\s*\(\d{4}\)\s*$', '', folder_name).strip()
        else:
            title = folder_name.strip()
        
        # 移除季数标记 S01, S1 等
        title = re.sub(r'\s+S\d{1,2}\s*$', '', title, flags=re.IGNORECASE).strip()
        
        # 如果标题为空，使用原始文件夹名
        if not title:
            title = original_name
        
        return title, year
    
    def find_best_parent_folder(self, file_path, base_path):
        """向上查找最合适的父文件夹（包含年份或TMDB ID的）"""
        current_path = os.path.dirname(file_path)
        best_folder = None
        best_score = 0
        
        # 向上遍历直到base_path
        while current_path and current_path != base_path and len(current_path) >= len(base_path):
            folder_name = os.path.basename(current_path)
            score = 0
            
            # 如果是 Season X 文件夹，跳过，继续向上查找
            if re.match(r'^Season\s+\d+$', folder_name, re.IGNORECASE):
                # 向上一级
                parent = os.path.dirname(current_path)
                if parent == current_path:  # 已到根目录
                    break
                current_path = parent
                continue
            
            # 包含TMDB ID的文件夹优先级最高
            if '{tmdbid-' in folder_name:
                score += 100
            
            # 包含年份的文件夹
            if re.search(r'\((\d{4})\)', folder_name) or re.search(r'^\[(\d{4})\]', folder_name):
                score += 50
            
            # 包含季数标记的文件夹
            if re.search(r'\[S\d+\]', folder_name, re.IGNORECASE):
                score += 10
            
            if score > best_score:
                best_score = score
                best_folder = current_path
            
            # 向上一级
            parent = os.path.dirname(current_path)
            if parent == current_path:  # 已到根目录
                break
            current_path = parent
        
        return best_folder if best_folder else os.path.dirname(file_path)
    
    def parse_media_filename(self, filename, parent_folder=''):
        """从文件名中提取媒体信息"""
        name_without_ext = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        # 检测字幕语言标识（如 .chs, .eng, .chi, .cht等）
        language_suffix = ''
        language_patterns = [
            r'\.(chs|cht|eng|chi|jpn|kor|spa|fre|ger|ita|rus|ara|por|vie|tha|ind|may|简|繁|英|日|韩|中英|简英|繁英|双语)$',
            r'\.(zh-cn|zh-tw|en|ja|ko|zh|chinese|english|japanese|korean)$'
        ]
        
        for pattern in language_patterns:
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                language_suffix = match.group(0)  # 包含点号
                name_without_ext = name_without_ext[:match.start()]
                break
        
        # 尝试从父文件夹获取标题和年份
        folder_title = ''
        folder_year = ''
        season_from_folder = None  # 从文件夹名提取的季数
        
        if parent_folder:
            folder_name = os.path.basename(parent_folder)
            
            # 检查是否是 Season X 文件夹
            season_match = re.match(r'^Season\s+(\d+)$', folder_name, re.IGNORECASE)
            if season_match:
                season_from_folder = int(season_match.group(1))
                # 向上一级获取真正的剧集名
                parent_parent = os.path.dirname(parent_folder)
                if parent_parent:
                    parent_parent_name = os.path.basename(parent_parent)
                    folder_title, folder_year = self.parse_folder_name(parent_parent_name)
            else:
                folder_title, folder_year = self.parse_folder_name(folder_name)
        
        metadata = {
            'title': '',
            'year': '',
            'season': '',
            'season_no_zero': '',  # 不补零的季数
            'episode': '',
            'season_episode': '',
            'part': '',
            'videoFormat': '',
            'language': language_suffix,  # 保存语言标识
            'fileExt': ext,
            'type': 'movie',  # 默认电影
            'isSubtitle': ext.lower() in SUBTITLE_EXTENSIONS,
            'folderTitle': folder_title,  # 保存文件夹标题
            'folderYear': folder_year  # 保存文件夹年份
        }
        
        # 检测视频格式
        formats = ['4K', '2160p', '1080p', '720p', 'BluRay', 'WEB-DL', 'WEBRip', 'HDRip']
        for fmt in formats:
            if fmt.lower() in name_without_ext.lower():
                metadata['videoFormat'] = fmt
                break
        
        # 检测年份
        year_match = re.search(r'\((\d{4})\)|\[(\d{4})\]|\.(\d{4})\.', name_without_ext)
        if year_match:
            metadata['year'] = year_match.group(1) or year_match.group(2) or year_match.group(3)
        
        # 检测季集信息 (S01E01, S01E01-E02, 1x01, E01, Episode 01, 01集等格式)
        season_episode_patterns = [
            r'[Ss](\d{1,2})[Ee](\d{1,2})(?:-[Ee](\d{1,2}))?',  # S01E01 或 S01E01-E02
            r'[Ss]eason[\s\.]?(\d{1,2})[\s\.]?[Ee]pisode[\s\.]?(\d{1,2})',  # Season 1 Episode 1
            r'(\d{1,2})x(\d{1,2})',  # 1x01
            r'[Ee]pisode[\s\.]?(\d{1,3})',  # Episode 01, Episode 1
            r'[Ee][Pp]?[\s\.]?(\d{1,3})',  # E01, EP01, E 01, E001
            r'第(\d{1,3})集',  # 第1集
            r'[\.\s](\d{1,3})集',  # .01集, 01集
        ]
        
        for i, pattern in enumerate(season_episode_patterns):
            match = re.search(pattern, name_without_ext)
            if match:
                metadata['type'] = 'tv'
                
                # 前三种格式有季和集
                if i < 3:
                    season_num = match.group(1)
                    episode_num = match.group(2)
                    metadata['season'] = season_num.zfill(2)
                    metadata['season_no_zero'] = str(int(season_num))  # 不补零
                    metadata['episode'] = episode_num.zfill(2)
                    metadata['season_episode'] = f"S{metadata['season']}E{metadata['episode']}"
                    
                    # 检测多集
                    if len(match.groups()) > 2 and match.group(3):
                        metadata['season_episode'] += f"-E{match.group(3).zfill(2)}"
                else:
                    # E01, EP01, 第1集 格式，默认第1季
                    episode_num = match.group(1)
                    metadata['season'] = '01'
                    metadata['season_no_zero'] = '1'  # 不补零
                    metadata['episode'] = episode_num.zfill(2)
                    metadata['season_episode'] = f"S01E{metadata['episode']}"
                
                break
        
        # 检测Part信息
        part_match = re.search(r'[Pp]art[\s\.]?(\d+|[A-Z])', name_without_ext)
        if part_match:
            metadata['part'] = part_match.group(1)
        
        # 提取标题（移除年份、季集、格式等信息）
        title = name_without_ext
        # 移除季集信息
        title = re.sub(r'[Ss]\d{1,2}[Ee]\d{1,2}(?:-[Ee]\d{1,2})?', '', title)
        title = re.sub(r'[Ss]eason[\s\.]?\d{1,2}[\s\.]?[Ee]pisode[\s\.]?\d{1,2}', '', title)
        title = re.sub(r'\d{1,2}x\d{1,2}', '', title)
        # 移除年份
        title = re.sub(r'\(?\d{4}\)?|\[\d{4}\]', '', title)
        # 移除格式信息
        for fmt in formats:
            title = re.sub(re.escape(fmt), '', title, flags=re.IGNORECASE)
        # 移除Part信息
        title = re.sub(r'[Pp]art[\s\.]?\d+', '', title)
        # 清理特殊字符（但保留冒号等）
        title = re.sub(r'[\.\-_]+', ' ', title)
        title = title.strip()
        
        # 如果有文件夹标题，优先使用文件夹标题
        if folder_title:
            metadata['title'] = folder_title
        else:
            metadata['title'] = title if title else '未知标题'
        
        # 如果有文件夹年份，优先使用文件夹年份
        if folder_year and not metadata['year']:
            metadata['year'] = folder_year
        
        # 处理标题查询（支持续集智能识别）
        final_title = metadata['title']
        is_tv = metadata['type'] == 'tv'
        
        # 如果是电视剧且从Season文件夹检测到季数 > 1，尝试查找续集
        search_title = final_title
        search_year = metadata['year']
        
        if is_tv and season_from_folder and season_from_folder > 1:
            # 尝试添加续集标记查询
            print(f"检测到Season {season_from_folder}文件夹，尝试查询续集...")
            
            # 对于中文标题，尝试添加续集标记
            if any('\u4e00' <= c <= '\u9fff' for c in final_title):
                # 中文续集标记
                if season_from_folder == 2:
                    search_title = f"{final_title}II"  # 如：我和僵尸有个约会II
                elif season_from_folder == 3:
                    search_title = f"{final_title}III"
                elif season_from_folder == 4:
                    search_title = f"{final_title}IV"
                elif season_from_folder == 5:
                    search_title = f"{final_title}V"
            else:
                # 英文续集标记
                if season_from_folder == 2:
                    search_title = f"{final_title} II"
                elif season_from_folder == 3:
                    search_title = f"{final_title} III"
                elif season_from_folder == 4:
                    search_title = f"{final_title} IV"
                elif season_from_folder == 5:
                    search_title = f"{final_title} V"
            
            print(f"续集查询标题: {search_title}")
        
        # 如果标题是英文，尝试从TMDB获取中文标题和分类
        if final_title and not any('\u4e00' <= c <= '\u9fff' for c in final_title):
            result = TMDBHelper.get_metadata_with_category(
                search_title, 
                search_year, 
                is_tv
            )
            metadata['title'] = result['title']
            metadata['category'] = result['category']
            if result['year'] and not metadata['year']:
                metadata['year'] = result['year']
        else:
            # 中文标题，如果检测到续集，更新标题
            if search_title != final_title:
                metadata['title'] = search_title
            # 中文标题，无法自动分类
            metadata['category'] = None
        
        return metadata
    
    def apply_template(self, template, metadata):
        """应用模板生成新文件名（支持跨文件系统兼容）"""
        result = template
        
        # 处理条件语句 {% if xxx %}...{% endif %}
        def replace_condition(match):
            condition = match.group(1).strip()
            content = match.group(2)
            
            # 检查条件是否满足
            if condition in metadata and metadata[condition]:
                return content
            return ''
        
        result = re.sub(r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}', replace_condition, result)
        
        # 替换变量 {{xxx}}
        for key, value in metadata.items():
            result = result.replace('{{' + key + '}}', str(value))
        
        # 清理文件名，确保跨文件系统兼容（ext4, btrfs, ZFS, NTFS等）
        result = sanitize_filename(result)
        
        return result
    
    def extract_resolution(self, format_str):
        """提取分辨率部分（不含来源）"""
        format_lower = format_str.lower() if format_str else ''
        
        if '4k' in format_lower or '2160p' in format_lower:
            return '4K'
        elif '1080p' in format_lower:
            return '1080p'
        elif '720p' in format_lower:
            return '720p'
        elif '480p' in format_lower:
            return '480p'
        elif '360p' in format_lower:
            return '360p'
        
        return '未知'
    
    def get_file_quality_score(self, file_info, metadata):
        """计算文件质量总分
        
        优先级计算：分辨率基础分 + 来源质量加分 + 格式加分 + 编码加分
        - 分辨率：4K=2160, 1080p=1080, 720p=720, 480p=480
        - 来源质量：REMUX=100, BluRay=80, WEB-DL=60, WEBRip=40, HDRip=20
        - 格式加分：MKV=5, MP4=3, AVI=1
        - 编码加分：h265/HEVC=2, h264=1
        """
        format_str = metadata.get('videoFormat', '')
        filename = file_info.get('name', '')
        file_size = file_info.get('size', 0)
        
        format_lower = format_str.lower() if format_str else ''
        filename_lower = filename.lower()
        
        base_score = 0
        quality_bonus = 0
        format_bonus = 0
        codec_bonus = 0
        
        # 分辨率基础分
        resolution_map = {
            '4k': 2160,
            '2160p': 2160,
            '1080p': 1080,
            '720p': 720,
            '480p': 480,
            '360p': 360
        }
        
        for key, value in resolution_map.items():
            if key in format_lower or key in filename_lower:
                base_score = value
                break
        
        # 来源质量加分（REMUX > BluRay > WEB-DL > WEBRip > HDRip）
        quality_map = {
            'remux': 100,
            'bluray': 80,
            'blu-ray': 80,
            'bd': 80,  # BD也是BluRay
            'web-dl': 60,
            'webdl': 60,
            'webrip': 40,
            'hdrip': 20,
            'hdtv': 10
        }
        
        for key, value in quality_map.items():
            if key in format_lower or key in filename_lower:
                quality_bonus = value
                break
        
        # 文件格式加分（MKV > MP4 > AVI）
        if filename_lower.endswith('.mkv'):
            format_bonus = 5
        elif filename_lower.endswith('.mp4'):
            format_bonus = 3
        elif filename_lower.endswith('.avi'):
            format_bonus = 1
        
        # 编码加分（h265/HEVC > h264）
        if 'h265' in filename_lower or 'hevc' in filename_lower or 'x265' in filename_lower:
            codec_bonus = 2
        elif 'h264' in filename_lower or 'x264' in filename_lower:
            codec_bonus = 1
        
        # 总分 = 分辨率基础分 + 来源质量加分 + 格式加分 + 编码加分
        total_score = base_score + quality_bonus + format_bonus + codec_bonus
        
        # 如果没有识别到任何信息，返回0
        return total_score if total_score > 0 else 0
    
    def get_resolution_priority(self, format_str):
        """获取清晰度优先级（向后兼容）"""
        format_lower = format_str.lower() if format_str else ''
        
        base_score = 0
        quality_bonus = 0
        
        # 分辨率基础分
        resolution_map = {
            '4k': 2160,
            '2160p': 2160,
            '1080p': 1080,
            '720p': 720,
            '480p': 480,
            '360p': 360
        }
        
        for key, value in resolution_map.items():
            if key in format_lower:
                base_score = value
                break
        
        # 来源质量加分
        quality_map = {
            'remux': 100,
            'bluray': 80,
            'blu-ray': 80,
            'bd': 80,
            'web-dl': 60,
            'webdl': 60,
            'webrip': 40,
            'hdrip': 20,
            'hdtv': 10
        }
        
        for key, value in quality_map.items():
            if key in format_lower:
                quality_bonus = value
                break
        
        total_score = base_score + quality_bonus
        return total_score if total_score > 0 else 0
    
    def group_duplicate_files(self, files, base_path):
        """将同一影片的不同版本分组"""
        from collections import defaultdict
        
        groups = defaultdict(list)
        
        for file_info in files:
            filename = file_info['name']
            file_path = file_info['path']
            parent_folder = os.path.dirname(file_path)
            
            metadata = self.parse_media_filename(filename, parent_folder)
            
            # 生成唯一标识：标题 + 年份 + 季集信息
            key_parts = [metadata['title']]
            
            if metadata['year']:
                key_parts.append(metadata['year'])
            
            if metadata['type'] == 'tv' and metadata['season_episode']:
                key_parts.append(metadata['season_episode'])
            
            # 只对媒体文件进行去重，字幕文件不参与
            if file_info['type'] == 'media':
                key = '|'.join(key_parts).lower()
                groups[key].append({
                    'file': file_info,
                    'metadata': metadata,
                    'resolution': self.get_file_quality_score(file_info, metadata)
                })
        
        return groups
    
    def generate_output_path(self, metadata, movie_output_path=None, tv_output_path=None, media_library_path=None, language='zh'):
        """根据元数据生成输出路径（包含分类）
        
        Args:
            metadata: 文件元数据
            movie_output_path: 电影输出路径（旧配置方式，向后兼容）
            tv_output_path: 电视剧输出路径（旧配置方式，向后兼容）
            media_library_path: 媒体库路径（新配置方式，推荐）
            language: 语言偏好 ('zh' 或 'en')
        
        Returns:
            tuple: (完整路径, 相对路径)
        """
        # 新配置方式：使用 PathGenerator
        if media_library_path:
            try:
                generator = PathGenerator(media_library_path, language)
                return generator.generate_path(metadata)
            except Exception as e:
                print(f"❌ PathGenerator 失败，回退到旧方法: {str(e)}")
                # 如果失败，回退到旧方法
        
        # 旧配置方式：保持向后兼容
        is_tv = metadata['type'] == 'tv'
        category = metadata.get('category')
        
        # 选择基础输出路径
        output_base = tv_output_path if is_tv else movie_output_path
        
        if not output_base:
            raise Exception("必须提供 media_library_path 或 movie_output_path/tv_output_path")
        
        # 应用模板生成文件名
        template = TV_TEMPLATE if is_tv else MOVIE_TEMPLATE
        new_relative_path = self.apply_template(template, metadata)
        
        # 如果有分类，添加分类目录
        if category:
            new_relative_path = os.path.join(category, new_relative_path)
        
        # 生成完整路径
        new_full_path = os.path.join(output_base, new_relative_path)
        
        return new_full_path, new_relative_path
    
    def handle_smart_rename(self, data):
        """智能重命名，自动去重保留最高清晰度版本，自动分类移动"""
        files = data.get('files', [])
        base_path = data.get('basePath', '')
        
        # 新配置方式：媒体库路径
        media_library_path = data.get('mediaLibraryPath', '')
        language = data.get('language', 'zh')
        
        # 旧配置方式：分离的电影和电视剧路径（向后兼容）
        movie_output_path = data.get('movieOutputPath', '')
        tv_output_path = data.get('tvOutputPath', '')
        
        auto_dedupe = data.get('autoDedupe', True)  # 默认开启去重
        
        if not files:
            self.send_json_response({'error': '没有选择文件'}, 400)
            return
        
        # 配置验证和兼容性处理
        use_new_config = bool(media_library_path)
        
        if not use_new_config:
            # 旧配置方式：如果没有指定输出路径，使用扫描路径
            if not movie_output_path:
                movie_output_path = base_path
            if not tv_output_path:
                tv_output_path = base_path
            
            if not movie_output_path or not tv_output_path:
                self.send_json_response({'error': '请配置媒体库路径或电影/电视剧输出路径'}, 400)
                return
        
        print(f"📁 配置模式: {'新配置（媒体库路径）' if use_new_config else '旧配置（分离路径）'}")
        if use_new_config:
            print(f"   媒体库路径: {media_library_path}")
        else:
            print(f"   电影路径: {movie_output_path}")
            print(f"   电视剧路径: {tv_output_path}")
        
        results = []
        to_delete = []
        
        try:
            # 分离媒体文件和字幕文件
            media_files = [f for f in files if f['type'] == 'media']
            subtitle_files = [f for f in files if f['type'] == 'subtitle']
            
            # 对媒体文件进行去重处理
            if auto_dedupe and media_files:
                groups = self.group_duplicate_files(media_files, base_path)
                
                # 处理每个分组
                for key, group in groups.items():
                    if len(group) > 1:
                        # 按清晰度排序（主要），文件大小排序（次要），保留最高的
                        # 评分相同时，文件越大越好
                        group.sort(key=lambda x: (x['resolution'], x['file']['size']), reverse=True)
                        
                        # 保留第一个（最高清晰度）
                        best = group[0]
                        media_files_to_process = [best['file']]
                        
                        # 其他的标记为删除
                        for item in group[1:]:
                            best_format = best['metadata']['videoFormat'] or '未知'
                            item_format = item['metadata']['videoFormat'] or '未知'
                            
                            # 如果清晰度相同，说明是来源质量不同
                            if item['resolution'] > 0 and best['resolution'] > 0:
                                # 提取分辨率部分
                                best_res = self.extract_resolution(best_format)
                                item_res = self.extract_resolution(item_format)
                                
                                if best_res == item_res:
                                    reason = f"相同清晰度但来源质量较低（{item_format}），保留 {best_format}"
                                else:
                                    reason = f"低清晰度版本（{item_format}），保留 {best_format}"
                            else:
                                reason = f"低清晰度版本（{item_format}），保留 {best_format}"
                            
                            to_delete.append({
                                'path': item['file']['path'],
                                'name': item['file']['name'],
                                'reason': reason
                            })
                    else:
                        media_files_to_process = [group[0]['file']]
                    
                    # 处理保留的文件
                    for file_info in media_files_to_process:
                        old_path = file_info['path']
                        filename = file_info['name']
                        # 查找最合适的父文件夹
                        parent_folder = self.find_best_parent_folder(old_path, base_path)
                        
                        metadata = self.parse_media_filename(filename, parent_folder)
                        new_full_path, new_relative_path = self.generate_output_path(
                            metadata, 
                            movie_output_path=movie_output_path if not use_new_config else None,
                            tv_output_path=tv_output_path if not use_new_config else None,
                            media_library_path=media_library_path if use_new_config else None,
                            language=language
                        )
                        
                        results.append({
                            'oldPath': old_path,
                            'oldName': filename,
                            'newPath': new_full_path,
                            'newName': os.path.basename(new_full_path),
                            'metadata': metadata,
                            'category': metadata.get('category'),
                            'needsFolder': os.path.dirname(new_relative_path) != ''
                        })
            else:
                # 不去重，处理所有媒体文件
                for file_info in media_files:
                    old_path = file_info['path']
                    filename = file_info['name']
                    # 查找最合适的父文件夹
                    parent_folder = self.find_best_parent_folder(old_path, base_path)
                    
                    metadata = self.parse_media_filename(filename, parent_folder)
                    new_full_path, new_relative_path = self.generate_output_path(
                        metadata,
                        movie_output_path=movie_output_path if not use_new_config else None,
                        tv_output_path=tv_output_path if not use_new_config else None,
                        media_library_path=media_library_path if use_new_config else None,
                        language=language
                    )
                    
                    results.append({
                        'oldPath': old_path,
                        'oldName': filename,
                        'newPath': new_full_path,
                        'newName': os.path.basename(new_full_path),
                        'metadata': metadata,
                        'category': metadata.get('category'),
                        'needsFolder': os.path.dirname(new_relative_path) != ''
                    })
            
            # 处理字幕文件（不去重）
            for file_info in subtitle_files:
                old_path = file_info['path']
                filename = file_info['name']
                # 查找最合适的父文件夹
                parent_folder = self.find_best_parent_folder(old_path, base_path)
                
                metadata = self.parse_media_filename(filename, parent_folder)
                new_full_path, new_relative_path = self.generate_output_path(
                    metadata,
                    movie_output_path=movie_output_path if not use_new_config else None,
                    tv_output_path=tv_output_path if not use_new_config else None,
                    media_library_path=media_library_path if use_new_config else None,
                    language=language
                )
                
                results.append({
                    'oldPath': old_path,
                    'oldName': filename,
                    'newPath': new_full_path,
                    'newName': os.path.basename(new_full_path),
                    'metadata': metadata,
                    'needsFolder': os.path.dirname(new_relative_path) != ''
                })
            
            self.send_json_response({
                'results': results,
                'toDelete': to_delete
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cleanup(self, data):
        """清理跳过的文件和空文件夹"""
        skipped_files = data.get('skippedFiles', [])
        base_path = data.get('basePath', '')
        
        if not base_path:
            self.send_json_response({'error': '请提供基础路径'}, 400)
            return
        
        deleted_files = []
        deleted_folders = []
        errors = []
        
        try:
            # 删除跳过的文件
            for file_path in skipped_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files.append(os.path.basename(file_path))
                        print(f"  ✓ 删除跳过的文件: {os.path.basename(file_path)}")
                except Exception as e:
                    errors.append({
                        'file': os.path.basename(file_path),
                        'error': str(e)
                    })
            
            # 清理空文件夹（从深到浅）
            import time
            time.sleep(0.5)  # 等待文件系统同步
            
            deleted_folders = self.remove_empty_folders(base_path)
            
            self.send_json_response({
                'success': True,
                'deletedFiles': deleted_files,
                'deletedFolders': deleted_folders,
                'errors': errors
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def remove_empty_folders(self, base_path):
        """递归删除空文件夹"""
        deleted_folders = []
        
        try:
            # 从底层开始遍历
            for root, dirs, files in os.walk(base_path, topdown=False):
                # 跳过基础路径本身
                if root == base_path:
                    continue
                
                try:
                    # 检查文件夹是否为空
                    if not os.listdir(root):
                        os.rmdir(root)
                        folder_name = os.path.relpath(root, base_path)
                        deleted_folders.append(folder_name)
                        print(f"  ✓ 删除空文件夹: {folder_name}")
                except OSError as e:
                    # 文件夹不为空或无权限，跳过
                    pass
        except Exception as e:
            print(f"  ⚠️  清理空文件夹时出错: {e}")
        
        return deleted_folders
    
    def handle_get_settings(self, data):
        """获取当前设置"""
        try:
            # 返回当前配置
            settings = {
                'tmdb_api_key': USER_CONFIG.get('tmdb_api_key', ''),
                'tmdb_proxy': USER_CONFIG.get('tmdb_proxy', ''),
                'tmdb_proxy_type': USER_CONFIG.get('tmdb_proxy_type', 'http'),
                'douban_cookie': USER_CONFIG.get('douban_cookie', ''),
                'cloud_115_cookie': USER_CONFIG.get('cloud_115_cookie', ''),
                'update_proxy': USER_CONFIG.get('update_proxy', ''),
                'update_proxy_enabled': USER_CONFIG.get('update_proxy_enabled', False),
                'auto_restart_after_update': USER_CONFIG.get('auto_restart_after_update', True)
            }
            self.send_json_response({'success': True, 'settings': settings})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_save_settings(self, data):
        """保存设置"""
        try:
            settings = data.get('settings', {})
            
            # 更新全局配置
            global USER_CONFIG, TMDB_API_KEY, TMDB_PROXY, TMDB_PROXY_TYPE
            global DOUBAN_COOKIE
            
            # 更新配置
            if 'tmdb_api_key' in settings:
                USER_CONFIG['tmdb_api_key'] = settings['tmdb_api_key']
                TMDB_API_KEY = settings['tmdb_api_key']
            
            if 'tmdb_proxy' in settings:
                USER_CONFIG['tmdb_proxy'] = settings['tmdb_proxy']
                TMDB_PROXY = settings['tmdb_proxy']
            
            if 'tmdb_proxy_type' in settings:
                USER_CONFIG['tmdb_proxy_type'] = settings['tmdb_proxy_type']
                TMDB_PROXY_TYPE = settings['tmdb_proxy_type']
            
            if 'douban_cookie' in settings:
                USER_CONFIG['douban_cookie'] = settings['douban_cookie']
                DOUBAN_COOKIE = settings['douban_cookie']
            
            # 更新代理配置
            if 'update_proxy' in settings:
                # 验证代理地址格式
                proxy_url = settings['update_proxy'].strip()
                if proxy_url and not (proxy_url.startswith('http://') or proxy_url.startswith('https://')):
                    self.send_json_response({
                        'error': '代理地址格式错误，应以 http:// 或 https:// 开头'
                    }, 400)
                    return
                USER_CONFIG['update_proxy'] = proxy_url
            
            if 'update_proxy_enabled' in settings:
                USER_CONFIG['update_proxy_enabled'] = bool(settings['update_proxy_enabled'])
            
            if 'auto_restart_after_update' in settings:
                USER_CONFIG['auto_restart_after_update'] = bool(settings['auto_restart_after_update'])
            
            # 保存到文件
            if save_config(USER_CONFIG):
                self.send_json_response({
                    'success': True,
                    'message': '设置已保存'
                })
            else:
                self.send_json_response({
                    'error': '保存设置失败'
                }, 500)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_version(self, data):
        """获取当前版本信息"""
        try:
            current_version = VersionManager.get_current_version()
            git_info = VersionManager.get_git_info()
            
            self.send_json_response({
                'success': True,
                'current_version': current_version,
                'git_commit': git_info['commit'],
                'git_branch': git_info['branch']
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_check_update(self, data):
        """检查是否有可用更新"""
        try:
            use_proxy = data.get('use_proxy', False)
            
            # 创建UpdateManager实例
            update_manager = UpdateManager()
            
            # 检查更新
            result = update_manager.check_for_updates(use_proxy=use_proxy)
            
            if result.get('error'):
                self.send_json_response({
                    'success': False,
                    'error': result['error']
                }, 400)
                return
            
            self.send_json_response({
                'success': True,
                'has_update': result['has_update'],
                'current_version': result['current_version'],
                'commits_behind': result['commits_behind']
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_update(self, data):
        """处理系统更新（增强版）"""
        try:
            use_proxy = data.get('use_proxy', False)
            auto_restart = data.get('auto_restart', True)
            
            # 创建UpdateManager实例
            update_manager = UpdateManager()
            
            # 检查是否是Git仓库
            if not update_manager.check_git_repository():
                self.send_json_response({
                    'error': '当前不是Git仓库，无法自动更新。请手动更新或重新使用git clone安装。'
                }, 400)
                return
            
            # 检查更新锁
            if update_manager.update_lock:
                self.send_json_response({
                    'error': '已有更新操作正在进行中，请稍后再试'
                }, 400)
                return
            
            # 设置更新锁
            update_manager.update_lock = True
            
            try:
                # 获取当前版本
                current_version = VersionManager.get_current_version()
                
                # 检查是否有更新
                check_result = update_manager.check_for_updates(use_proxy=use_proxy)
                
                if check_result.get('error'):
                    self.send_json_response({
                        'error': check_result['error']
                    }, 400)
                    return
                
                if not check_result['has_update']:
                    self.send_json_response({
                        'updated': False,
                        'message': '已是最新版本，无需更新',
                        'current_version': current_version
                    })
                    return
                
                commits_behind = check_result['commits_behind']
                
                # 执行更新
                success, message = update_manager.pull_updates(use_proxy=use_proxy)
                
                if not success:
                    self.send_json_response({
                        'error': message
                    }, 500)
                    return
                
                # 更新成功，读取新版本号
                new_version = VersionManager.get_current_version()
                
                # 记录更新历史
                self.save_update_history({
                    'version': new_version,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'success',
                    'commits': commits_behind,
                    'user': 'admin',  # 可以从session获取
                    'ip': self.client_address[0]
                })
                
                # 发送成功响应
                response = {
                    'updated': True,
                    'new_version': new_version,
                    'commits_updated': commits_behind,
                    'message': f'成功更新 {commits_behind} 个版本'
                }
                
                if auto_restart:
                    response['message'] += '，服务将在3秒后重启'
                    self.send_json_response(response)
                    
                    # 重启服务
                    update_manager.restart_service()
                else:
                    response['message'] += '，请手动重启服务使更新生效'
                    self.send_json_response(response)
                
            finally:
                # 释放更新锁
                update_manager.update_lock = False
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_force_update(self, data):
        """强制更新（重置本地修改）"""
        try:
            import subprocess
            
            use_proxy = data.get('use_proxy', False)
            auto_restart = data.get('auto_restart', True)
            
            # 创建UpdateManager实例
            update_manager = UpdateManager()
            
            # 检查是否是Git仓库
            if not update_manager.check_git_repository():
                self.send_json_response({
                    'error': '当前不是Git仓库，无法自动更新'
                }, 400)
                return
            
            # 检查更新锁
            if update_manager.update_lock:
                self.send_json_response({
                    'error': '已有更新操作正在进行中，请稍后再试'
                }, 400)
                return
            
            # 设置更新锁
            update_manager.update_lock = True
            
            try:
                # 获取当前版本
                current_version = VersionManager.get_current_version()
                
                # 强制重置本地修改
                print("强制重置本地修改...")
                reset_success, _, reset_error = update_manager.execute_git_command(
                    ['git', 'reset', '--hard', 'HEAD'],
                    timeout=30
                )
                
                if not reset_success:
                    self.send_json_response({
                        'error': f'重置失败: {reset_error}'
                    }, 500)
                    return
                
                # 执行更新（跳过本地修改检查，因为已经reset了）
                success, message = update_manager.pull_updates(use_proxy=use_proxy, skip_check=True)
                
                if not success:
                    self.send_json_response({
                        'error': message
                    }, 500)
                    return
                
                # 更新成功，读取新版本号
                new_version = VersionManager.get_current_version()
                
                # 记录更新历史
                self.save_update_history({
                    'version': new_version,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'success',
                    'commits': 1,
                    'user': 'admin',
                    'ip': self.client_address[0],
                    'force': True
                })
                
                # 发送成功响应
                response = {
                    'updated': True,
                    'new_version': new_version,
                    'message': '强制更新成功'
                }
                
                if auto_restart:
                    response['message'] += '，服务将在3秒后重启'
                    self.send_json_response(response)
                    
                    # 重启服务
                    update_manager.restart_service()
                else:
                    response['message'] += '，请手动重启服务使更新生效'
                    self.send_json_response(response)
                
            finally:
                # 释放更新锁
                update_manager.update_lock = False
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_rollback(self, data):
        """处理版本回滚"""
        try:
            steps = data.get('steps', 1)
            
            # 创建UpdateManager实例
            update_manager = UpdateManager()
            
            # 检查是否是Git仓库
            if not update_manager.check_git_repository():
                self.send_json_response({
                    'error': '当前不是Git仓库，无法回滚'
                }, 400)
                return
            
            # 执行回滚
            success, message = update_manager.rollback(steps=steps)
            
            if success:
                # 获取回滚后的版本
                new_version = VersionManager.get_current_version()
                
                self.send_json_response({
                    'success': True,
                    'message': message,
                    'new_version': new_version
                })
            else:
                self.send_json_response({
                    'error': message
                }, 500)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_update_history(self, data):
        """获取更新历史"""
        try:
            history = self.load_update_history()
            self.send_json_response({
                'success': True,
                'history': history
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def save_update_history(self, record):
        """保存更新历史记录"""
        try:
            history_file = 'update_history.json'
            history = []
            
            # 读取现有历史
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history = data.get('updates', [])
            
            # 添加新记录
            history.insert(0, record)
            
            # 只保留最近10条
            history = history[:10]
            
            # 保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({'updates': history}, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存更新历史失败: {e}")
            return False
    
    def load_update_history(self):
        """加载更新历史记录"""
        try:
            history_file = 'update_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('updates', [])
        except Exception as e:
            print(f"加载更新历史失败: {e}")
        return []
    
    def handle_cloud_verify_cookie(self, data):
        """验证115网盘Cookie"""
        try:
            cookie = data.get('cookie', '').strip()
            
            if not cookie:
                self.send_json_response({'error': 'Cookie不能为空'}, 400)
                return
            
            # 创建API实例并验证
            api = Cloud115API(cookie)
            valid, user_info, error = api.verify_cookie()
            
            if valid:
                # 加密存储Cookie
                encryptor = CookieEncryption()
                encrypted_cookie = encryptor.encrypt(cookie)
                
                # 保存到配置
                USER_CONFIG['cloud_115_cookie'] = encrypted_cookie
                save_config(USER_CONFIG)
                
                self.send_json_response({
                    'success': True,
                    'user_info': user_info
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': error or 'Cookie验证失败'
                }, 400)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_list_files(self, data):
        """获取115网盘文件列表"""
        print(f"\n[HANDLER] 收到文件列表请求: {data}")
        try:
            folder_id = data.get('folder_id', '0')
            offset = data.get('offset', 0)
            limit = data.get('limit', 100)
            print(f"[HANDLER] 参数: folder_id={folder_id}, offset={offset}, limit={limit}")
            
            # 获取Cookie
            encrypted_cookie = USER_CONFIG.get('cloud_115_cookie', '')
            print(f"[HANDLER] Cookie存在: {bool(encrypted_cookie)}")
            if not encrypted_cookie:
                print(f"[HANDLER] Cookie未配置")
                self.send_json_response({'error': '请先配置115网盘Cookie'}, 400)
                return
            
            # 解密Cookie
            encryptor = CookieEncryption()
            cookie = encryptor.decrypt(encrypted_cookie)
            print(f"[HANDLER] Cookie解密成功，长度: {len(cookie)}")
            
            # 创建API实例
            api = Cloud115API(cookie)
            print(f"[HANDLER] API实例创建成功")
            
            # 获取文件列表
            print(f"[HANDLER] 开始调用list_files")
            result, error = api.list_files(folder_id, offset, limit)
            print(f"[HANDLER] list_files返回: result={bool(result)}, error={error}")
            
            if result:
                self.send_json_response({
                    'success': True,
                    'data': result
                })
            else:
                print(f"[HANDLER] 返回错误: {error}")
                self.send_json_response({
                    'success': False,
                    'error': error or '获取文件列表失败'
                }, 500)
        except Exception as e:
            print(f"[HANDLER] 异常: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_scan(self, data):
        """扫描115网盘文件夹"""
        try:
            folder_id = data.get('folder_id', '0')
            recursive = data.get('recursive', True)
            max_depth = data.get('max_depth', 10)
            
            # 获取Cookie
            encrypted_cookie = USER_CONFIG.get('cloud_115_cookie', '')
            if not encrypted_cookie:
                self.send_json_response({'error': '请先配置115网盘Cookie'}, 400)
                return
            
            # 解密Cookie
            encryptor = CookieEncryption()
            cookie = encryptor.decrypt(encrypted_cookie)
            
            # 创建API和扫描器实例
            api = Cloud115API(cookie)
            scanner = CloudScanner(api)
            
            # 扫描文件夹
            result = scanner.scan_folder(folder_id, recursive, max_depth)
            
            self.send_json_response({
                'success': True,
                'data': result
            })
        except Exception as e:
            print(f"[HANDLER] 扫描异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_smart_organize(self, data):
        """115网盘智能整理 - 新策略：尊重现有文件夹结构"""
        try:
            folder_id = data.get('folder_id', '0')
            target_folder_id = data.get('target_folder_id', '0')
            
            # 获取Cookie
            encrypted_cookie = USER_CONFIG.get('cloud_115_cookie', '')
            if not encrypted_cookie:
                self.send_json_response({'error': '请先配置115网盘Cookie'}, 400)
                return
            
            # 解密Cookie
            encryptor = CookieEncryption()
            cookie = encryptor.decrypt(encrypted_cookie)
            
            # 创建API实例
            api = Cloud115API(cookie)
            
            print(f"[整理] 开始整理文件夹: {folder_id}")
            
            # 步骤1: 获取第一层文件夹（剧集文件夹）
            result, error = api.list_files(folder_id, offset=0, limit=1000)
            if error:
                raise Exception(f"获取文件夹列表失败: {error}")
            
            folders = [f for f in result.get('files', []) if f.get('is_dir')]
            print(f"[整理] 找到 {len(folders)} 个文件夹")
            
            total_renamed = 0
            total_moved = 0
            operations = []
            
            # 处理每个剧集文件夹
            for show_folder in folders:
                folder_name = show_folder.get('name', '')
                folder_fid = show_folder.get('fid', '')
                
                print(f"[整理] 处理文件夹: {folder_name}")
                
                # 步骤2: 清理文件夹名（去掉{tmdb-xxx}标记）
                clean_name = re.sub(r'\s*\{tmdb-\d+\}', '', folder_name).strip()
                if clean_name != folder_name:
                    print(f"[整理] 重命名文件夹: {folder_name} -> {clean_name}")
                    success, error = api.rename_file(folder_fid, clean_name)
                    if success:
                        total_renamed += 1
                        operations.append({
                            'type': 'rename_folder',
                            'old_name': folder_name,
                            'new_name': clean_name,
                            'success': True
                        })
                    else:
                        print(f"[整理] 重命名失败: {error}")
                
                # 步骤3: 检查第二层（Season文件夹）
                season_result, error = api.list_files(folder_fid, offset=0, limit=1000)
                if error:
                    print(f"[整理] 获取Season文件夹失败: {error}")
                    continue
                
                season_folders = [f for f in season_result.get('files', []) if f.get('is_dir')]
                print(f"[整理] 找到 {len(season_folders)} 个Season文件夹")
                
                # 处理每个Season文件夹
                for season_folder in season_folders:
                    season_name = season_folder.get('name', '')
                    season_fid = season_folder.get('fid', '')
                    
                    # 检查是否是Season文件夹
                    season_match = re.match(r'Season\s+(\d+)', season_name, re.IGNORECASE)
                    if not season_match:
                        print(f"[整理] 跳过非Season文件夹: {season_name}")
                        continue
                    
                    season_num = season_match.group(1).zfill(2)  # 补零，如 "1" -> "01"
                    print(f"[整理] 处理Season {season_num}")
                    
                    # 步骤4: 获取媒体文件
                    files_result, error = api.list_files(season_fid, offset=0, limit=1000)
                    if error:
                        print(f"[整理] 获取文件列表失败: {error}")
                        continue
                    
                    video_files = [f for f in files_result.get('files', []) 
                                 if not f.get('is_dir') and self._is_video_file(f.get('name', ''))]
                    
                    print(f"[整理] 找到 {len(video_files)} 个视频文件")
                    
                    # 步骤5: 检查并重命名文件
                    for video_file in video_files:
                        file_name = video_file.get('name', '')
                        file_fid = video_file.get('fid', '')
                        
                        # 检查文件名是否已经是标准格式
                        # 标准格式: "剧集名 - S01E01 - 第1集.mkv"
                        standard_pattern = rf'^{re.escape(clean_name)}\s*-\s*S{season_num}E\d{{2}}\s*-\s*第\d+集'
                        
                        if re.match(standard_pattern, file_name):
                            print(f"[整理] 文件已是标准格式，跳过: {file_name}")
                            continue
                        
                        # 提取集数
                        episode_match = re.search(r'[Ee](\d{1,3})', file_name)
                        if not episode_match:
                            # 尝试从文件名中提取数字
                            num_match = re.search(r'(\d{1,3})', file_name)
                            if num_match:
                                episode_num = num_match.group(1).zfill(2)
                            else:
                                print(f"[整理] 无法提取集数，跳过: {file_name}")
                                continue
                        else:
                            episode_num = episode_match.group(1).zfill(2)
                        
                        # 获取文件扩展名
                        ext = os.path.splitext(file_name)[1]
                        
                        # 生成新文件名
                        new_name = f"{clean_name} - S{season_num}E{episode_num} - 第{int(episode_num)}集{ext}"
                        
                        if new_name != file_name:
                            print(f"[整理] 重命名: {file_name} -> {new_name}")
                            success, error = api.rename_file(file_fid, new_name)
                            if success:
                                total_renamed += 1
                                operations.append({
                                    'type': 'rename_file',
                                    'old_name': file_name,
                                    'new_name': new_name,
                                    'success': True
                                })
                            else:
                                print(f"[整理] 重命名失败: {error}")
                                operations.append({
                                    'type': 'rename_file',
                                    'old_name': file_name,
                                    'new_name': new_name,
                                    'success': False,
                                    'error': error
                                })
                
                # 步骤6: 移动整个剧集文件夹到目标位置
                # 只有当目标文件夹不是当前文件夹时才移动
                if target_folder_id != folder_id:
                    print(f"[整理] 移动文件夹: {clean_name}")
                    success, error = api.move_file(folder_fid, target_folder_id)
                    if success:
                        total_moved += 1
                        operations.append({
                            'type': 'move_folder',
                            'folder_name': clean_name,
                            'success': True
                        })
                    else:
                        print(f"[整理] 移动失败: {error}")
                        operations.append({
                            'type': 'move_folder',
                            'folder_name': clean_name,
                            'success': False,
                            'error': error
                        })
            
            # 返回结果
            self.send_json_response({
                'success': True,
                'data': {
                    'folders_processed': len(folders),
                    'files_renamed': total_renamed,
                    'folders_moved': total_moved,
                    'operations': operations
                }
            })
        except Exception as e:
            print(f"[HANDLER] 智能整理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def _is_video_file(self, filename):
        """判断是否为视频文件"""
        video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.rmvb', '.rm', '.3gp', '.ts', '.m2ts']
        ext = os.path.splitext(filename.lower())[1]
        return ext in video_exts
    
    def handle_cloud_generate_qrcode(self, data):
        """生成115网盘二维码"""
        try:
            qr_type = data.get('type', 'android')
            
            print(f"[HANDLER] 生成二维码: type={qr_type}")
            
            qrcode_url, session_id, error = Cloud115API.generate_qrcode(qr_type)
            
            if qrcode_url:
                self.send_json_response({
                    'success': True,
                    'qrcode': qrcode_url,
                    'session_id': session_id,
                    'type': qr_type
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': error or '生成二维码失败'
                }, 500)
        except Exception as e:
            print(f"[HANDLER] 生成二维码异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_check_qrcode(self, data):
        """检查二维码扫码状态"""
        try:
            session_id = data.get('session_id', '')
            
            if not session_id:
                self.send_json_response({'error': '缺少session_id'}, 400)
                return
            
            status, cookie, error = Cloud115API.check_qrcode_status(session_id)
            
            if status == 'success' and cookie:
                # 扫码成功，保存Cookie
                encryptor = CookieEncryption()
                encrypted_cookie = encryptor.encrypt(cookie)
                USER_CONFIG['cloud_115_cookie'] = encrypted_cookie
                save_config(USER_CONFIG)
                
                self.send_json_response({
                    'success': True,
                    'status': status,
                    'cookie': cookie
                })
            elif status == 'expired':
                self.send_json_response({
                    'success': False,
                    'expired': True,
                    'status': status
                })
            else:
                self.send_json_response({
                    'success': False,
                    'status': status,
                    'error': error
                })
        except Exception as e:
            print(f"[HANDLER] 检查二维码状态异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_history(self, data):
        """获取115网盘操作历史记录"""
        try:
            limit = data.get('limit', 100)
            offset = data.get('offset', 0)
            operation_type = data.get('operation_type')
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            
            # 创建历史管理器
            history_manager = CloudHistoryManager()
            
            # 加载历史记录
            result = history_manager.load_history(
                limit=limit,
                offset=offset,
                operation_type=operation_type,
                date_from=date_from,
                date_to=date_to
            )
            
            self.send_json_response({
                'success': True,
                'history': result['records'],
                'total': result['total'],
                'filtered': result['filtered'],
                'limit': result['limit'],
                'offset': result['offset']
            })
            
        except Exception as e:
            print(f"[HANDLER] 获取历史记录异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_cloud_history_stats(self, data):
        """获取115网盘操作历史统计信息"""
        try:
            # 创建历史管理器
            history_manager = CloudHistoryManager()
            
            # 获取统计信息
            stats = history_manager.get_statistics()
            
            self.send_json_response({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            print(f"[HANDLER] 获取历史统计异常: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_qrcode_start(self, data):
        """开始二维码登录（优化版：不需要qrcode库）"""
        try:
            import requests
            from urllib.parse import urlencode
            
            app_type = data.get('app', 'android')
            
            # 1. 获取Token
            url = 'https://qrcodeapi.115.com/api/1.0/web/1.0/token/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[QRCode] 开始生成二维码: app={app_type}")
            response = requests.get(url, headers=headers, timeout=10)
            result = response.json()
            
            if not result.get('state'):
                self.send_json_response({'success': False, 'error': '获取Token失败'}, 500)
                return
            
            token_data = result.get('data', {})
            uid = token_data.get('uid')
            time_val = token_data.get('time')
            sign = token_data.get('sign')
            
            # 2. 生成二维码URL（关键：直接使用115的图片URL，不需要qrcode库！）
            qr_url = f'https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid={uid}'
            
            print(f"[QRCode] 二维码生成成功: uid={uid}")
            
            # 3. 返回给前端
            self.send_json_response({
                'success': True,
                'qr_url': qr_url,  # 前端直接显示这个图片
                'uid': uid,
                'time': time_val,
                'sign': sign,
                'app': app_type
            })
        except Exception as e:
            print(f"[QRCode] 生成二维码失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'success': False, 'error': str(e)}, 500)
    
    def handle_qrcode_check(self, data):
        """检查二维码扫码状态（优化版）"""
        try:
            import requests
            from urllib.parse import urlencode
            
            uid = data.get('uid')
            time_val = data.get('time')
            sign = data.get('sign')
            
            if not all([uid, time_val, sign]):
                self.send_json_response({'success': False, 'error': '缺少必要参数'}, 400)
                return
            
            # 检查状态
            params = {'uid': uid, 'time': time_val, 'sign': sign}
            url = f'https://qrcodeapi.115.com/get/status/?{urlencode(params)}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            result = response.json()
            
            status_data = result.get('data', {})
            status_code = status_data.get('status')
            
            # 状态码：
            # 0 - 等待扫码
            # 1 - 已扫码，等待确认
            # 2 - 已确认，登录成功
            # -1 - 二维码过期
            # -2 - 用户取消
            
            self.send_json_response({
                'success': True,
                'status': status_code
            })
        except Exception as e:
            print(f"[QRCode] 检查状态失败: {str(e)}")
            self.send_json_response({'success': False, 'error': str(e)}, 500)
    
    def handle_qrcode_finish(self, data):
        """完成二维码登录，获取Cookie（优化版）"""
        try:
            import requests
            
            uid = data.get('uid')
            app_type = data.get('app', 'android')
            
            if not uid:
                self.send_json_response({'success': False, 'error': '缺少uid参数'}, 400)
                return
            
            # POST获取Cookie
            url = f'https://passportapi.115.com/app/1.0/{app_type}/1.0/login/qrcode/'
            post_data = {'app': app_type, 'account': uid}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[QRCode] 获取Cookie: uid={uid}, app={app_type}")
            response = requests.post(url, data=post_data, headers=headers, timeout=10)
            result = response.json()
            
            if not result.get('state'):
                self.send_json_response({'success': False, 'error': '获取Cookie失败'}, 500)
                return
            
            # 提取Cookie
            cookie_dict = result.get('data', {}).get('cookie', {})
            cookie_parts = []
            for key in ['UID', 'CID', 'SEID']:
                if key in cookie_dict:
                    cookie_parts.append(f"{key}={cookie_dict[key]}")
            
            cookie = '; '.join(cookie_parts)
            
            if not cookie:
                self.send_json_response({'success': False, 'error': 'Cookie数据为空'}, 500)
                return
            
            # 保存Cookie
            encryptor = CookieEncryption()
            encrypted_cookie = encryptor.encrypt(cookie)
            USER_CONFIG['cloud_115_cookie'] = encrypted_cookie
            save_config(USER_CONFIG)
            
            print(f"[QRCode] Cookie保存成功")
            
            self.send_json_response({
                'success': True,
                'cookie': cookie
            })
        except Exception as e:
            print(f"[QRCode] 获取Cookie失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'success': False, 'error': str(e)}, 500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    # 读取版本号
    current_version = VersionManager.get_current_version()
    
    print('=' * 50)
    print(f'🎬 媒体库文件管理器 {current_version}')
    print('=' * 50)
    print(f'服务器运行在: http://localhost:{PORT}')
    print(f'局域网访问: http://你的NAS_IP:{PORT}')
    print('扫描路径: /vol02/1000-1-b23abde7/待整理')
    print('')
    print('🌐 中文标题识别: 已启用')
    print('   优先级: 豆瓣 > TMDB')
    print(f'   豆瓣: 已配置Cookie（不使用代理）')
    print(f'   TMDB: API Key {TMDB_API_KEY[:10]}...（代理: {TMDB_PROXY}）')
    print('   功能: 英文标题自动转中文')
    print('')
    print('按 Ctrl+C 停止服务器')
    print('=' * 50)
    server = HTTPServer(('0.0.0.0', PORT), MediaHandler)
    server.serve_forever()
