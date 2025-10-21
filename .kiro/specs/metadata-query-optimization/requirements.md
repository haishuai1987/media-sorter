# 元数据查询优化需求文档

## Introduction

当前系统在查询TMDB和豆瓣时，对于很多影视作品无法正确识别，导致使用原始文件名而不是正确的中文标题。需要优化查询算法，提高识别准确率。

## Glossary

- **System**: 媒体库文件管理器
- **TMDB**: The Movie Database，国际电影数据库
- **豆瓣**: 豆瓣电影，中文电影数据库
- **Release Group**: 发布组标识（如ADWeb、CHDWEB等）
- **Query String**: 用于查询的搜索关键词

## Requirements

### Requirement 1: 改进文件名解析

**User Story:** 作为用户，我希望系统能够从复杂的文件名中准确提取影视作品标题，以便正确查询元数据

#### Acceptance Criteria

1. WHEN System解析包含Release Group的文件名时，System SHALL移除Release Group标识后再查询
2. WHEN System解析包含技术参数的文件名时，System SHALL移除所有技术参数（分辨率、编码格式等）
3. WHEN System解析包含年份的文件名时，System SHALL同时尝试带年份和不带年份的查询
4. WHEN System解析包含季数标识的文件名时，System SHALL移除季数标识后查询剧集基础信息
5. WHEN System解析失败时，System SHALL记录详细的解析日志以便调试

### Requirement 2: 智能查询策略

**User Story:** 作为用户，我希望系统能够使用多种查询策略，提高查询成功率

#### Acceptance Criteria

1. WHEN 完整标题查询失败时，System SHALL尝试使用简化标题查询
2. WHEN 英文标题查询失败时，System SHALL尝试使用中文标题查询（如果存在）
3. WHEN 带年份查询失败时，System SHALL尝试不带年份查询
4. WHEN 所有自动查询失败时，System SHALL提供手动匹配选项
5. WHEN 查询成功时，System SHALL缓存查询结果避免重复查询

### Requirement 3: 标题映射表

**User Story:** 作为用户，我希望能够为常见的影视作品配置标题映射，确保查询准确性

#### Acceptance Criteria

1. WHEN System启动时，System SHALL加载标题映射配置文件
2. WHEN System查询元数据前，System SHALL首先检查标题映射表
3. WHEN 映射表中存在匹配项时，System SHALL直接使用映射的标题
4. WHEN 用户添加新映射时，System SHALL保存到配置文件
5. WHEN 映射配置更新时，System SHALL支持热重载无需重启

### Requirement 4: 查询日志和调试

**User Story:** 作为开发者，我希望能够看到详细的查询过程日志，以便优化查询算法

#### Acceptance Criteria

1. WHEN System执行查询时，System SHALL记录原始文件名
2. WHEN System提取查询关键词时，System SHALL记录提取的关键词
3. WHEN System执行每次查询尝试时，System SHALL记录查询URL和参数
4. WHEN 查询失败时，System SHALL记录失败原因
5. WHEN 查询成功时，System SHALL记录匹配的结果和置信度
