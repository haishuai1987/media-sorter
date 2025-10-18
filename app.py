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
    'douban_cookie': ''  # 请在Web界面的"设置"中配置你的豆瓣Cookie
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

# 重命名模板
MOVIE_TEMPLATE = "{{title}}{% if year %} ({{year}}){% endif %}/{{title}}{% if year %} ({{year}}){% endif %}{% if part %}-{{part}}{% endif %}{% if videoFormat %} - {{videoFormat}}{% endif %}{{language}}{{fileExt}}"
TV_TEMPLATE = "{{title}}{% if year %} ({{year}}){% endif %}/Season {{season_no_zero}}/{{title}} - {{season_episode}}{% if part %}-{{part}}{% endif %}{% if episode %} - 第 {{episode}} 集{% endif %}{{language}}{{fileExt}}"

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
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
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
    
    def generate_output_path(self, metadata, movie_output_path, tv_output_path):
        """根据元数据生成输出路径（包含分类）"""
        is_tv = metadata['type'] == 'tv'
        category = metadata.get('category')
        
        # 选择基础输出路径
        output_base = tv_output_path if is_tv else movie_output_path
        
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
        movie_output_path = data.get('movieOutputPath', '')
        tv_output_path = data.get('tvOutputPath', '')
        auto_dedupe = data.get('autoDedupe', True)  # 默认开启去重
        
        if not files:
            self.send_json_response({'error': '没有选择文件'}, 400)
            return
        
        # 如果没有指定输出路径，使用扫描路径
        if not movie_output_path:
            movie_output_path = base_path
        if not tv_output_path:
            tv_output_path = base_path
        
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
                            metadata, movie_output_path, tv_output_path
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
                        metadata, movie_output_path, tv_output_path
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
                    metadata, movie_output_path, tv_output_path
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
                'douban_cookie': USER_CONFIG.get('douban_cookie', '')
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
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    print('=' * 50)
    print('🎬 媒体库文件管理器 V1.3')
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
