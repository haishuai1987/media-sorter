# Design Document

## Overview

本设计文档描述如何修复本地整理模块的二级分类功能，实现正确的目录结构、文件命名，以及自动检测现有分类目录的能力。

## Architecture

### Current Architecture (有问题的实现)

```
当前路径生成逻辑:
1. 选择基础路径 (movie_output_path 或 tv_output_path)
2. 应用模板生成相对路径
3. 如果有分类，添加分类目录
4. 组合成完整路径

问题:
- 模板中包含了父目录名 ({{title}} ({{year}}))
- 分类目录添加在最后，而不是在剧名之前
- Season 目录结构被破坏
```

**当前错误输出**:
```
/vol02/1000-1-b23abde7/115/电视剧/包青天 (1993)_Season 1_包青天 - S01E08 - 第 08 集.mkv
```

### Target Architecture (修复后的实现)

```
新的路径生成逻辑:
1. 检测或创建媒体库结构 (电影/电视剧)
2. 确定二级分类 (国产剧/欧美剧等)
3. 检测已存在的分类目录
4. 生成剧名/电影名目录
5. 对于电视剧，添加 Season 目录
6. 生成最终文件名

目录结构:
<用户选择的路径>/  # 例如: /vol02/1000-1-b23abde7/115 或 /mnt/storage/media
├── 电影/ (或 Movies/)
│   ├── 动画电影/
│   ├── 华语电影/
│   └── 外语电影/
│       └── 电影名 (年份)/
│           └── 电影名 (年份).mkv
└── 电视剧/ (或 TV Shows/)
    ├── 国产剧/
    ├── 欧美剧/
    └── 日韩剧/
        └── 剧名 (年份)/
            └── Season 1/
                └── 剧名 - S01E01 - 第 01 集.mkv

注意: "媒体库路径"是用户在界面中选择的任意路径，不要求目录名称必须是"媒体库"
```

**正确输出**:
```
/vol02/1000-1-b23abde7/115/电视剧/国产剧/包青天 (1993)/Season 1/包青天 - S01E08 - 第 08 集.mkv
```

## Components and Interfaces

### 1. 媒体库目录检测器 (MediaLibraryDetector)

**功能**: 自动检测媒体库中的电影和电视剧目录

```python
class MediaLibraryDetector:
    """媒体库目录结构检测器"""
    
    # 支持的目录名称映射
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
            return result
        
        # 列出所有子目录
        subdirs = [d for d in os.listdir(self.media_library_path) 
                   if os.path.isdir(os.path.join(self.media_library_path, d))]
        
        # 检测电影目录（优先中文）
        for name in self.MOVIE_DIR_NAMES:
            if name in subdirs:
                result['movie_dir'] = name
                result['movie_path'] = os.path.join(self.media_library_path, name)
                break
        
        # 检测电视剧目录（优先中文）
        for name in self.TV_DIR_NAMES:
            if name in subdirs:
                result['tv_dir'] = name
                result['tv_path'] = os.path.join(self.media_library_path, name)
                break
        
        return result
    
    def create_default_structure(self, language='zh'):
        """创建默认目录结构
        
        Args:
            language: 'zh' for Chinese, 'en' for English
        """
        if language == 'zh':
            movie_dir = '电影'
            tv_dir = '电视剧'
        else:
            movie_dir = 'Movies'
            tv_dir = 'TV Shows'
        
        movie_path = os.path.join(self.media_library_path, movie_dir)
        tv_path = os.path.join(self.media_library_path, tv_dir)
        
        os.makedirs(movie_path, exist_ok=True)
        os.makedirs(tv_path, exist_ok=True)
        
        return {
            'movie_dir': movie_dir,
            'tv_dir': tv_dir,
            'movie_path': movie_path,
            'tv_path': tv_path
        }
```

### 2. 二级分类目录检测器 (SecondaryClassificationDetector)

**功能**: 检测已存在的二级分类目录

```python
class SecondaryClassificationDetector:
    """二级分类目录检测器"""
    
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
            return {}
        
        existing = {}
        subdirs = [d for d in os.listdir(self.base_path) 
                   if os.path.isdir(os.path.join(self.base_path, d))]
        
        # 建立映射关系
        for subdir in subdirs:
            # 精确匹配
            existing[subdir] = subdir
            
            # 模糊匹配（去除常见后缀）
            normalized = subdir.replace('电视剧', '').replace('电影', '').strip()
            if normalized:
                existing[normalized] = subdir
        
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
            return self.existing_categories[category_name]
        
        # 模糊匹配
        for key, value in self.existing_categories.items():
            if category_name in key or key in category_name:
                return value
        
        # 不存在，返回配置名称
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
            os.makedirs(dir_path, exist_ok=True)
            # 更新缓存
            self.existing_categories[category_name] = dir_name
        
        return dir_path
```

### 3. 路径生成器重构 (PathGenerator)

**功能**: 生成正确的文件路径

```python
class PathGenerator:
    """路径生成器"""
    
    def __init__(self, media_library_path):
        self.media_library_path = media_library_path
        self.detector = MediaLibraryDetector(media_library_path)
        self.structure = self.detector.detect_structure()
        
        # 如果没有检测到，创建默认结构
        if not self.structure['movie_path'] or not self.structure['tv_path']:
            self.structure = self.detector.create_default_structure()
        
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
                - episode: 集数 (仅电视剧)
                - category: 二级分类
                - fileExt: 文件扩展名
        
        Returns:
            tuple: (完整路径, 相对路径)
        """
        is_tv = metadata['type'] == 'tv'
        category = metadata.get('category', '未分类')
        
        # 1. 选择基础路径
        if is_tv:
            base_path = self.structure['tv_path']
            classifier = self.tv_classifier
        else:
            base_path = self.structure['movie_path']
            classifier = self.movie_classifier
        
        # 2. 确定二级分类目录
        category_path = classifier.ensure_category_dir(category)
        
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
            season = metadata.get('season', '1')
            season_dir = f"Season {season}"
            
            # 生成文件名
            episode = metadata.get('episode', '')
            season_episode = metadata.get('season_episode', f"S{season:02d}E01")
            
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
                self.structure['tv_dir'],
                classifier.get_category_dir(category),
                title_dir,
                season_dir,
                filename
            )
        else:
            # 电影: 分类/电影名/文件名
            filename = title_dir + metadata.get('fileExt', '.mkv')
            
            full_path = os.path.join(
                category_path,
                title_dir,
                filename
            )
            
            relative_path = os.path.join(
                self.structure['movie_dir'],
                classifier.get_category_dir(category),
                title_dir,
                filename
            )
        
        return full_path, relative_path
```

### 4. 配置管理器 (ConfigManager)

**功能**: 管理新旧配置的兼容性

```python
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config):
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
                return movie_parent
        
        return None
    
    def migrate_to_new_config(self):
        """迁移旧配置到新配置
        
        Returns:
            dict: 新配置
        """
        new_config = self.config.copy()
        
        media_library_path = self.get_media_library_path()
        if media_library_path:
            new_config['media_library_path'] = media_library_path
            
            # 可选：移除旧配置
            # new_config.pop('movie_output_path', None)
            # new_config.pop('tv_output_path', None)
        
        return new_config
```

## Data Models

### 文件元数据结构

```python
{
    'type': 'tv',  # 'movie' or 'tv'
    'title': '包青天',
    'year': '1993',
    'season': 1,
    'season_no_zero': '1',
    'episode': '08',
    'season_episode': 'S01E08',
    'category': '国产剧',
    'genre_ids': [18],
    'origin_country': ['CN'],
    'original_language': 'zh',
    'fileExt': '.mkv'
}
```

### 媒体库结构

```python
{
    'media_library_path': '/vol02/1000-1-b23abde7/115',
    'movie_dir': '电影',
    'tv_dir': '电视剧',
    'movie_path': '/vol02/1000-1-b23abde7/115/电影',
    'tv_path': '/vol02/1000-1-b23abde7/115/电视剧',
    'movie_categories': ['动画电影', '华语电影', '外语电影'],
    'tv_categories': ['国产剧', '欧美剧', '日韩剧', '国漫', '日番']
}
```

## Error Handling

### 目录检测失败

```python
try:
    structure = detector.detect_structure()
    if not structure['movie_path']:
        # 创建默认结构
        structure = detector.create_default_structure()
except PermissionError:
    raise Exception("没有权限访问媒体库目录")
except Exception as e:
    raise Exception(f"检测媒体库结构失败: {str(e)}")
```

### 分类目录创建失败

```python
try:
    category_path = classifier.ensure_category_dir(category)
except OSError as e:
    if e.errno == 28:  # No space left
        raise Exception("磁盘空间不足")
    raise Exception(f"创建分类目录失败: {str(e)}")
```

## Testing Strategy

### 单元测试

1. **MediaLibraryDetector 测试**
   - 测试检测中文目录名
   - 测试检测英文目录名
   - 测试混合目录名
   - 测试不存在的目录

2. **SecondaryClassificationDetector 测试**
   - 测试精确匹配
   - 测试模糊匹配
   - 测试创建新目录
   - 测试缓存更新

3. **PathGenerator 测试**
   - 测试电影路径生成
   - 测试电视剧路径生成
   - 测试 Season 目录结构
   - 测试文件名格式

### 集成测试

1. **完整流程测试**
   - 从扫描到整理的完整流程
   - 测试新媒体库（空目录）
   - 测试现有媒体库（已有分类）
   - 测试混合场景

2. **向后兼容测试**
   - 测试旧配置方式
   - 测试配置迁移
   - 测试 API 兼容性

## Implementation Notes

### 修改的文件

1. **app.py**
   - 添加 `MediaLibraryDetector` 类
   - 添加 `SecondaryClassificationDetector` 类
   - 重构 `generate_output_path()` 方法
   - 修改 `handle_smart_rename()` 方法
   - 添加配置迁移逻辑

2. **index.html / public/index.html**
   - 修改界面，合并输入框
   - 添加媒体库路径配置
   - 显示检测到的目录结构
   - 添加语言偏好设置

### 实施步骤

1. **Phase 1: 核心类实现**
   - 实现 `MediaLibraryDetector`
   - 实现 `SecondaryClassificationDetector`
   - 实现 `PathGenerator`

2. **Phase 2: 集成到现有代码**
   - 修改 `generate_output_path()`
   - 修改 `handle_smart_rename()`
   - 添加配置管理

3. **Phase 3: 界面更新**
   - 修改前端界面
   - 添加配置选项
   - 显示检测结果

4. **Phase 4: 测试和优化**
   - 单元测试
   - 集成测试
   - 性能优化

## Migration Plan

### 用户迁移步骤

1. **自动迁移**
   - 系统自动检测旧配置
   - 提示用户迁移到新配置
   - 保留旧配置作为备份

2. **手动配置**
   - 用户可以手动设置媒体库路径
   - 系统自动检测目录结构
   - 显示检测结果供用户确认

### 配置文件变化

**旧配置**:
```json
{
    "movie_output_path": "/vol02/1000-1-b23abde7/115/电影",
    "tv_output_path": "/vol02/1000-1-b23abde7/115/电视剧"
}
```

**新配置**:
```json
{
    "media_library_path": "/vol02/1000-1-b23abde7/115",
    "preferred_language": "zh"
}
```

## Performance Considerations

### 目录扫描优化

- 缓存检测结果，避免重复扫描
- 只在必要时刷新缓存
- 使用浅层扫描，不递归子目录

### 路径生成优化

- 预先检测并缓存媒体库结构
- 批量处理时复用检测器实例
- 避免重复的文件系统操作
