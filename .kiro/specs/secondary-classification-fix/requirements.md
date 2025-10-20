# Requirements Document

## Introduction

修复本地整理模块的二级分类功能，实现正确的目录结构和文件命名，支持自动检测现有分类目录，优化界面配置。

## Glossary

- **Secondary Classification**: 二级分类，在一级分类（电影/电视剧）下的细分类别（如国产剧、欧美剧、动画电影等）
- **Media Library**: 媒体库，统一的媒体文件存储根目录
- **Classification Config**: 分类配置，基于 YAML 的分类规则配置文件
- **Auto Detection**: 自动检测，自动识别媒体库中已存在的分类目录
- **System**: media-sorter 系统

## Requirements

### Requirement 1: 实现正确的二级分类目录结构

**User Story:** 作为用户，我希望整理后的文件按照二级分类规则保存到正确的目录结构中，以便更好地组织媒体库。

#### Acceptance Criteria

1. WHEN THE System organizes a TV show file, THE System SHALL create the path structure as `媒体库/电视剧/二级分类/剧名/Season X/文件名`
2. WHEN THE System organizes a movie file, THE System SHALL create the path structure as `媒体库/电影/二级分类/电影名 (年份)/文件名`
3. WHEN a secondary classification directory already exists, THE System SHALL use the existing directory
4. WHEN a secondary classification directory does not exist, THE System SHALL create the directory automatically
5. THE System SHALL preserve the Season directory structure for TV shows

### Requirement 2: 修复文件命名格式

**User Story:** 作为用户，我希望整理后的文件名格式正确，不包含多余的信息，以便文件名清晰易读。

#### Acceptance Criteria

1. THE System SHALL NOT include season information in the filename for TV shows
2. THE System SHALL format TV show filenames as `剧名 - S01E01 - 第 01 集.ext`
3. THE System SHALL format movie filenames as `电影名 (年份).ext`
4. THE System SHALL remove redundant parent folder names from filenames
5. THE System SHALL preserve the original file extension

### Requirement 3: 自动检测媒体库目录结构

**User Story:** 作为用户，我希望系统能自动检测媒体库中的电影和电视剧文件夹，无论使用中文还是英文命名，以便适应不同的使用习惯。

#### Acceptance Criteria

1. WHEN THE System scans the media library path, THE System SHALL detect directories named `电影` or `Movies` or `Movie`
2. WHEN THE System scans the media library path, THE System SHALL detect directories named `电视剧` or `TV Shows` or `TV` or `Series`
3. WHEN both Chinese and English directories exist, THE System SHALL prioritize Chinese directories
4. WHEN neither directory exists, THE System SHALL create directories using the user's preferred language
5. THE System SHALL support case-insensitive directory name matching

### Requirement 4: 自动检测二级分类目录

**User Story:** 作为用户，我希望系统能自动检测已存在的二级分类目录，以便将新文件整理到现有的分类中。

#### Acceptance Criteria

1. WHEN THE System determines the secondary classification for a file, THE System SHALL check if the classification directory already exists
2. WHEN a classification directory exists, THE System SHALL use the existing directory name (preserving case and language)
3. WHEN multiple matching directories exist, THE System SHALL use the first match
4. WHEN no matching directory exists, THE System SHALL create a new directory using the classification name from config
5. THE System SHALL support fuzzy matching for directory names (e.g., "国产剧" matches "国产剧", "国产电视剧", etc.)

### Requirement 5: 优化界面配置

**User Story:** 作为用户，我希望界面配置更简洁，只需要配置媒体库路径和待整理路径，以便快速开始整理工作。

#### Acceptance Criteria

1. THE System SHALL provide a single "媒体库路径" input field instead of separate movie and TV paths
2. THE System SHALL retain the "待整理路径" input field for source files
3. THE System SHALL automatically detect movie and TV directories under the media library path
4. THE System SHALL display detected directory structure to the user
5. THE System SHALL allow users to configure preferred language for new directories (Chinese/English)

### Requirement 6: 支持 YAML 分类配置

**User Story:** 作为用户，我希望系统能正确读取和应用 YAML 分类配置文件，以便按照我的分类规则整理文件。

#### Acceptance Criteria

1. THE System SHALL load classification rules from a YAML configuration file
2. THE System SHALL support all classification conditions: `original_language`, `production_countries`, `origin_country`, `genre_ids`, `release_year`
3. THE System SHALL match files against classification rules in order
4. WHEN multiple conditions are specified, THE System SHALL require all conditions to match
5. WHEN a condition value is prefixed with `!`, THE System SHALL exclude files matching that value
6. WHEN no rules match, THE System SHALL use the default classification (e.g., "未分类")

### Requirement 7: 保持向后兼容

**User Story:** 作为用户，我希望更新后的系统仍然支持旧的配置方式，以便不影响现有的使用流程。

#### Acceptance Criteria

1. WHEN users have separate movie and TV paths configured, THE System SHALL continue to support them
2. THE System SHALL provide a migration path from old configuration to new configuration
3. THE System SHALL not break existing API interfaces
4. THE System SHALL maintain compatibility with existing file organization workflows
