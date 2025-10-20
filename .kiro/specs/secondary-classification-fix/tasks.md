# Implementation Plan

- [x] 1. 实现 MediaLibraryDetector 类


  - 创建 `MediaLibraryDetector` 类，支持检测电影和电视剧目录
  - 实现 `detect_structure()` 方法，检测现有目录结构
  - 支持多种目录名称：`电影`/`Movies`/`Movie`、`电视剧`/`TV Shows`/`TV`/`Series`
  - 实现优先级匹配（中文优先）
  - 实现 `create_default_structure()` 方法，创建默认目录结构
  - 支持语言偏好设置（中文/英文）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_



- [ ] 2. 实现 SecondaryClassificationDetector 类
  - 创建 `SecondaryClassificationDetector` 类，检测二级分类目录
  - 实现 `_scan_existing_categories()` 方法，扫描已存在的分类目录
  - 实现 `get_category_dir()` 方法，获取分类目录名称（支持精确和模糊匹配）
  - 实现 `ensure_category_dir()` 方法，确保分类目录存在



  - 添加目录名称缓存机制，避免重复扫描
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. 实现 PathGenerator 类
  - 创建 `PathGenerator` 类，生成正确的文件路径
  - 集成 `MediaLibraryDetector` 和 `SecondaryClassificationDetector`


  - 实现 `generate_path()` 方法，生成完整路径
  - 正确处理电视剧路径：`分类/剧名/Season X/文件名`
  - 正确处理电影路径：`分类/电影名/文件名`
  - 生成正确的文件名格式（移除多余信息）
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_



- [ ] 4. 修复文件名生成逻辑
  - 修改电视剧文件名模板，移除 Season 信息
  - 格式：`剧名 - S01E01 - 第 01 集.ext`
  - 修改电影文件名模板，确保格式正确
  - 格式：`电影名 (年份).ext`




  - 移除文件名中的父目录信息
  - _Requirements: 2.1, 2.2, 2.3, 2.4_



- [ ] 5. 重构 generate_output_path() 方法
  - 使用新的 `PathGenerator` 类替代现有逻辑
  - 移除旧的模板应用逻辑
  - 确保生成的路径包含正确的二级分类目录
  - 保持 API 接口不变（向后兼容）
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.3_

- [ ] 6. 修改 handle_smart_rename() 方法
  - 更新为使用媒体库路径而不是分离的电影/电视剧路径
  - 支持新旧配置方式（向后兼容）
  - 使用 `PathGenerator` 生成路径
  - 确保批量处理时复用检测器实例（性能优化）
  - _Requirements: 5.1, 5.2, 5.3, 7.1, 7.2_

- [ ] 7. 实现 ConfigManager 类
  - 创建 `ConfigManager` 类，管理配置兼容性
  - 实现 `get_media_library_path()` 方法，支持新旧配置
  - 实现 `migrate_to_new_config()` 方法，迁移旧配置
  - 自动检测并提示用户迁移配置
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 8. 更新前端界面 - 配置部分
  - 修改设置页面，合并电影和电视剧输入框为"媒体库路径"
  - 为"媒体库路径"输入框添加文件夹图标按钮（与"待整理路径"一致）
  - 实现文件夹选择功能（调用 `/api/browse-folders`）
  - 保留"待整理路径"输入框
  - 添加"语言偏好"选项（中文/英文）
  - 添加"检测媒体库结构"按钮
  - 显示检测到的目录结构（电影目录、电视剧目录、分类目录）
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 9. 更新前端界面 - 整理页面
  - 修改整理页面的路径配置
  - 使用新的媒体库路径配置
  - 显示将要使用的目录结构
  - 添加路径预览功能
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 10. 添加配置迁移提示
  - 检测用户是否使用旧配置
  - 显示迁移提示对话框
  - 提供一键迁移功能
  - 保留旧配置作为备份
  - _Requirements: 7.2, 7.4_

- [ ] 11. 单元测试
  - 测试 `MediaLibraryDetector` 的各种场景
  - 测试 `SecondaryClassificationDetector` 的匹配逻辑
  - 测试 `PathGenerator` 的路径生成
  - 测试文件名格式化
  - 测试配置迁移逻辑
  - _Requirements: 所有需求_

- [ ] 12. 集成测试
  - 测试完整的整理流程（新媒体库）
  - 测试完整的整理流程（现有媒体库）
  - 测试向后兼容性（旧配置）
  - 测试混合场景（中英文目录）
  - 测试错误处理（权限、空间等）
  - _Requirements: 所有需求_

- [ ] 13. 性能优化
  - 优化目录扫描性能（缓存）
  - 优化批量处理时的检测器复用
  - 减少重复的文件系统操作
  - 添加性能监控日志
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 14. 文档更新
  - 更新使用指南，说明新的配置方式
  - 添加媒体库结构说明
  - 添加配置迁移指南
  - 更新 API 文档
  - 添加常见问题解答
  - _Requirements: 7.4_
