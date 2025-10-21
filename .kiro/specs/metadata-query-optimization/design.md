# 元数据查询优化设计文档

## Overview

优化元数据查询系统，通过改进文件名解析、智能查询策略、标题映射表和详细日志，提高TMDB/豆瓣查询的准确率。

## Architecture

```
文件名 → 解析器 → 标题映射检查 → 查询策略引擎 → TMDB/豆瓣API → 结果缓存
                                    ↓
                              查询日志记录
```

## Components and Interfaces

### 1. TitleParser (标题解析器)

**职责**: 从文件名中提取干净的标题

**方法**:
```python
class TitleParser:
    def parse(self, filename: str) -> ParsedTitle:
        """解析文件名，返回结构化标题信息"""
        
    def remove_release_group(self, title: str) -> str:
        """移除Release Group标识"""
        
    def remove_technical_params(self, title: str) -> str:
        """移除技术参数（分辨率、编码等）"""
        
    def extract_year(self, title: str) -> tuple[str, Optional[int]]:
        """提取年份，返回(标题, 年份)"""
        
    def normalize_title(self, title: str) -> str:
        """标准化标题（去除特殊字符、统一空格等）"""
```

**Release Group 列表**:
- ADWeb, CHDWEB, DBTV, NGB, CHDTV
- 常见格式: `-GroupName` 或 `.GroupName` 在文件名末尾

**技术参数模式**:
- 分辨率: `1080p`, `2160p`, `720p`, `4K`
- 编码: `H264`, `H265`, `x264`, `x265`, `AVC`
- 音频: `AAC`, `DDP`, `DDP5.1`, `Atmos`
- 来源: `WEB-DL`, `WEB`, `BluRay`, `HDTV`

### 2. TitleMapper (标题映射器)

**职责**: 管理手动配置的标题映射

**配置文件**: `title_mapping.json`
```json
{
  "mappings": {
    "SAKAMOTO.DAYS": {
      "zh": "坂本日常",
      "en": "Sakamoto Days",
      "tmdb_id": 12345,
      "douban_id": "67890"
    },
    "Spy.x.Family": {
      "zh": "间谍过家家",
      "en": "Spy x Family",
      "tmdb_id": 11111
    }
  }
}
```

**方法**:
```python
class TitleMapper:
    def __init__(self, config_path: str):
        """加载映射配置"""
        
    def get_mapping(self, original_title: str) -> Optional[TitleMapping]:
        """查找标题映射"""
        
    def add_mapping(self, original: str, mapping: TitleMapping):
        """添加新映射"""
        
    def save(self):
        """保存映射到文件"""
        
    def reload(self):
        """热重载配置"""
```

### 3. QueryStrategy (查询策略引擎)

**职责**: 执行多种查询策略直到成功

**查询策略顺序**:
1. 检查标题映射表
2. 完整标题 + 年份查询
3. 完整标题查询（不带年份）
4. 简化标题查询（移除副标题）
5. 中文标题查询（如果文件名包含中文）
6. 英文标题查询（如果文件名包含英文）
7. 分词查询（取前3-5个关键词）

**方法**:
```python
class QueryStrategy:
    def __init__(self, tmdb_client, douban_client, title_mapper):
        """初始化查询策略"""
        
    def query(self, parsed_title: ParsedTitle) -> Optional[Metadata]:
        """执行查询策略，返回元数据"""
        
    def _try_full_title_with_year(self, title: str, year: int) -> Optional[Metadata]:
        """策略1: 完整标题+年份"""
        
    def _try_full_title(self, title: str) -> Optional[Metadata]:
        """策略2: 完整标题"""
        
    def _try_simplified_title(self, title: str) -> Optional[Metadata]:
        """策略3: 简化标题"""
        
    def _try_chinese_title(self, title: str) -> Optional[Metadata]:
        """策略4: 中文标题"""
        
    def _try_english_title(self, title: str) -> Optional[Metadata]:
        """策略5: 英文标题"""
        
    def _try_keyword_query(self, title: str) -> Optional[Metadata]:
        """策略6: 关键词查询"""
```

### 4. QueryLogger (查询日志记录器)

**职责**: 记录详细的查询过程

**日志级别**:
- DEBUG: 每个查询尝试的详细信息
- INFO: 查询成功/失败的摘要
- WARNING: 查询异常或超时
- ERROR: 查询错误

**日志格式**:
```
[2025-10-21 03:40:00] [INFO] 开始查询: SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC-ADWeb
[2025-10-21 03:40:00] [DEBUG] 解析结果: title=SAKAMOTO.DAYS, year=2025, season=1
[2025-10-21 03:40:00] [DEBUG] 移除Release Group: ADWeb
[2025-10-21 03:40:00] [DEBUG] 移除技术参数: 1080p, WEB-DL, H264, AAC
[2025-10-21 03:40:00] [DEBUG] 标准化标题: SAKAMOTO DAYS
[2025-10-21 03:40:01] [DEBUG] 策略1: 查询 "SAKAMOTO DAYS 2025" (TMDB)
[2025-10-21 03:40:01] [DEBUG] TMDB响应: 0 results
[2025-10-21 03:40:02] [DEBUG] 策略2: 查询 "SAKAMOTO DAYS" (TMDB)
[2025-10-21 03:40:02] [DEBUG] TMDB响应: 0 results
[2025-10-21 03:40:03] [DEBUG] 策略3: 查询 "SAKAMOTO DAYS" (豆瓣)
[2025-10-21 03:40:03] [INFO] 查询成功: 坂本日常 (豆瓣ID: 36685803)
```

**方法**:
```python
class QueryLogger:
    def log_start(self, filename: str):
        """记录查询开始"""
        
    def log_parse_result(self, parsed: ParsedTitle):
        """记录解析结果"""
        
    def log_strategy_attempt(self, strategy_name: str, query_string: str, source: str):
        """记录策略尝试"""
        
    def log_api_response(self, source: str, result_count: int, results: list):
        """记录API响应"""
        
    def log_success(self, metadata: Metadata):
        """记录查询成功"""
        
    def log_failure(self, reason: str):
        """记录查询失败"""
```

## Data Models

### ParsedTitle
```python
@dataclass
class ParsedTitle:
    original: str           # 原始文件名
    title: str             # 提取的标题
    chinese_title: Optional[str]  # 中文标题（如果有）
    english_title: Optional[str]  # 英文标题（如果有）
    year: Optional[int]    # 年份
    season: Optional[int]  # 季数
    episode: Optional[int] # 集数
    release_group: Optional[str]  # Release Group
    technical_params: list[str]   # 技术参数列表
```

### TitleMapping
```python
@dataclass
class TitleMapping:
    chinese_title: Optional[str]
    english_title: Optional[str]
    tmdb_id: Optional[int]
    douban_id: Optional[str]
    confidence: float = 1.0  # 映射置信度
```

## Error Handling

1. **解析错误**: 如果文件名无法解析，使用原始文件名作为查询关键词
2. **API超时**: 设置5秒超时，超时后尝试下一个策略
3. **API限流**: 检测429错误，等待后重试
4. **配置文件错误**: 如果映射文件损坏，使用空映射继续运行

## Testing Strategy

1. **单元测试**:
   - TitleParser: 测试各种文件名格式的解析
   - TitleMapper: 测试映射的增删改查
   - QueryStrategy: 测试每个查询策略

2. **集成测试**:
   - 端到端测试：从文件名到元数据的完整流程
   - 测试常见的失败案例

3. **性能测试**:
   - 测试100个文件的查询时间
   - 测试缓存命中率

## Implementation Notes

1. **向后兼容**: 保持现有API接口不变，只优化内部实现
2. **渐进式优化**: 先实现基础解析和映射，再添加高级策略
3. **配置优先**: 标题映射表优先级最高，确保用户配置生效
4. **日志可控**: 提供日志级别配置，避免过多日志影响性能
