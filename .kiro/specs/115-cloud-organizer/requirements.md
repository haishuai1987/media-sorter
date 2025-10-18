# 需求文档 - 115网盘整理模块

## 简介

本模块为媒体库管理器添加115网盘云端整理功能，通过115 API直接在云端操作文件，无需下载到本地。用户只需提供115网盘Cookie，即可实现与本地整理模块相同的智能重命名、分类、去重等功能。

## 术语表

- **System**: 媒体库管理器Web应用程序
- **115 Cloud**: 115网盘云存储服务
- **Cookie**: 115网盘的身份验证凭证
- **Cloud API**: 115网盘的HTTP API接口
- **Cloud File**: 115网盘上的文件对象
- **Cloud Folder**: 115网盘上的文件夹对象
- **File ID**: 115网盘文件的唯一标识符
- **Folder ID**: 115网盘文件夹的唯一标识符
- **Local Module**: 本地文件整理模块（原有功能）
- **Cloud Module**: 115网盘整理模块（新功能）

## 需求

### 需求 1: 115网盘认证

**用户故事:** 作为用户，我希望通过提供115网盘Cookie来连接我的网盘账号，以便系统能够访问和操作我的云端文件。

#### 验收标准

1. THE System SHALL 在设置界面提供115网盘Cookie输入框
2. WHEN 用户保存Cookie, THE System SHALL 验证Cookie的有效性
3. IF Cookie无效或过期, THEN THE System SHALL 显示错误提示并要求重新输入
4. THE System SHALL 将有效的Cookie加密存储到配置文件
5. THE System SHALL 在Cookie过期前7天显示续期提醒

### 需求 2: 云端目录浏览

**用户故事:** 作为用户，我希望能够浏览115网盘的目录结构，以便选择需要整理的文件夹。

#### 验收标准

1. THE System SHALL 通过115 API获取根目录的文件夹列表
2. WHEN 用户点击文件夹, THE System SHALL 展开显示子文件夹和文件
3. THE System SHALL 支持递归加载多级目录结构
4. THE System SHALL 显示每个文件夹的文件数量和总大小
5. THE System SHALL 提供搜索功能快速定位文件夹

### 需求 3: 云端文件扫描

**用户故事:** 作为用户，我希望系统能够扫描指定115网盘文件夹中的媒体文件，以便进行后续整理操作。

#### 验收标准

1. WHEN 用户选择云端文件夹并点击扫描, THE System SHALL 通过API获取该文件夹的所有文件
2. THE System SHALL 递归扫描所有子文件夹
3. THE System SHALL 识别媒体文件（视频）和字幕文件
4. THE System SHALL 过滤不支持的文件格式
5. THE System SHALL 显示扫描进度和文件统计信息

### 需求 4: 云端文件信息提取

**用户故事:** 作为用户，我希望系统能够从115网盘文件名中提取媒体信息，以便进行智能重命名。

#### 验收标准

1. THE System SHALL 从云端文件名中提取标题、年份、季集、分辨率等信息
2. THE System SHALL 复用本地模块的文件名解析逻辑
3. THE System SHALL 通过豆瓣和TMDB API获取中文标题
4. THE System SHALL 缓存查询结果避免重复请求
5. THE System SHALL 支持手动修正识别错误的信息

### 需求 5: 云端智能去重

**用户故事:** 作为用户，我希望系统能够识别115网盘中的重复文件，以便保留最佳质量版本并删除其他版本。

#### 验收标准

1. THE System SHALL 基于文件名和大小识别重复文件
2. THE System SHALL 使用质量评分系统（分辨率+来源+编码）评估文件质量
3. WHEN 检测到重复文件, THE System SHALL 标记保留和删除的文件
4. THE System SHALL 在执行删除前显示确认对话框
5. THE System SHALL 通过115 API删除低质量版本文件

### 需求 6: 云端文件重命名

**用户故事:** 作为用户，我希望系统能够按照标准格式重命名115网盘中的媒体文件，以便文件名规范统一。

#### 验收标准

1. THE System SHALL 使用与本地模块相同的命名模板
2. WHEN 用户确认重命名, THE System SHALL 通过115 API重命名云端文件
3. THE System SHALL 批量处理多个文件的重命名操作
4. THE System SHALL 显示重命名进度和成功/失败状态
5. IF 重命名失败, THEN THE System SHALL 记录错误并继续处理其他文件

### 需求 7: 云端文件分类移动

**用户故事:** 作为用户，我希望系统能够将115网盘中的媒体文件移动到对应的分类文件夹，以便文件组织有序。

#### 验收标准

1. THE System SHALL 根据TMDB元数据确定文件分类（电影/电视剧类型）
2. THE System SHALL 在目标位置自动创建分类文件夹结构
3. WHEN 用户确认移动, THE System SHALL 通过115 API移动文件到目标文件夹
4. THE System SHALL 支持批量移动操作
5. THE System SHALL 处理文件名冲突（跳过、替换、保留两个）

### 需求 8: 云端操作进度跟踪

**用户故事:** 作为用户，我希望能够实时查看115网盘整理操作的进度，以便了解处理状态。

#### 验收标准

1. THE System SHALL 显示8步处理流程的当前步骤
2. THE System SHALL 显示每个步骤的进度百分比
3. THE System SHALL 显示实时日志信息
4. THE System SHALL 允许用户取消正在进行的操作
5. THE System SHALL 在操作完成后显示统计报告

### 需求 9: 模块切换和配置

**用户故事:** 作为用户，我希望能够在本地整理和115网盘整理之间切换，以便根据需要选择不同的整理模式。

#### 验收标准

1. THE System SHALL 在Web界面提供模块切换选项（本地/115网盘）
2. WHEN 切换到115网盘模式, THE System SHALL 显示云端特有的配置选项
3. THE System SHALL 保存每个模块的独立配置
4. THE System SHALL 在模块切换时保留用户的操作历史
5. THE System SHALL 支持同时配置两个模块

### 需求 10: API速率限制和错误处理

**用户故事:** 作为用户，我希望系统能够妥善处理115 API的速率限制和错误，以便操作稳定可靠。

#### 验收标准

1. THE System SHALL 检测115 API的速率限制响应
2. WHEN 遇到速率限制, THE System SHALL 自动等待并重试
3. THE System SHALL 实现指数退避重试策略
4. IF API请求失败, THEN THE System SHALL 记录详细错误信息
5. THE System SHALL 在连续失败3次后暂停操作并提示用户

### 需求 11: 云端操作历史记录

**用户故事:** 作为用户，我希望查看115网盘整理操作的历史记录，以便追踪文件变更。

#### 验收标准

1. THE System SHALL 记录每次云端操作（重命名、移动、删除）
2. THE System SHALL 保存操作前后的文件信息
3. THE System SHALL 在Web界面显示最近100条操作记录
4. THE System SHALL 支持按日期、类型筛选历史记录
5. THE System SHALL 提供导出历史记录为CSV文件的功能

### 需求 12: 安全和隐私保护

**用户故事:** 作为用户，我希望我的115网盘Cookie和数据得到安全保护，以防止未授权访问。

#### 验收标准

1. THE System SHALL 使用AES加密存储115网盘Cookie
2. THE System SHALL 不在日志中记录完整的Cookie信息
3. THE System SHALL 在用户退出登录时清除Cookie
4. THE System SHALL 提供Cookie有效期检查功能
5. THE System SHALL 在检测到异常访问时锁定账号并通知用户
