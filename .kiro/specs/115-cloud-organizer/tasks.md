# 实现计划 - 115网盘整理模块

- [x] 1. 代码重构：模块化现有功能



  - 将现有功能重构为LocalModule类
  - 提取共享的MediaParser、TMDBHelper、DoubanHelper为独立服务
  - 创建ModuleManager管理本地和云端模块
  - 更新API路由支持/api/local/*和/api/cloud/*




  - _需求: 9.1, 9.2, 9.3_

- [x] 2. 实现Cookie加密存储



  - 安装cryptography依赖

  - 创建CookieEncryption类实现AES-256加密
  - 生成并保存加密密钥到.encryption_key文件
  - 实现encrypt和decrypt方法

  - _需求: 12.1, 12.2_




- [ ] 3. 实现Cloud115API基础类
  - 创建Cloud115API类



  - 实现_create_session方法创建HTTP会话
  - 实现verify_cookie方法验证Cookie有效性
  - 添加请求头和基础URL配置
  - 实现错误处理和日志记录
  - _需求: 1.2, 1.3, 12.2_


- [ ] 4. 实现115网盘文件列表API
  - 实现list_files方法获取文件夹内容
  - 解析API响应并格式化文件信息
  - 实现分页支持（offset和limit）
  - 添加文件类型识别（文件夹/文件）
  - 实现缓存机制（5分钟TTL）
  - _需求: 2.1, 2.2, 2.3_

- [ ] 5. 实现115网盘文件操作API
  - 实现rename_file方法重命名文件
  - 实现move_file方法移动文件
  - 实现delete_file方法删除文件
  - 实现create_folder方法创建文件夹
  - 添加批量操作支持（50个/批次）
  - _需求: 6.1, 6.2, 7.2, 7.3_

- [ ] 6. 实现CloudScanner扫描器
  - 创建CloudScanner类
  - 实现scan_folder方法扫描指定文件夹
  - 实现递归扫描子文件夹功能
  - 实现filter_media_files过滤媒体文件
  - 统计文件数量和总大小
  - _需求: 3.1, 3.2, 3.3, 3.4_

- [ ] 7. 实现CloudRenamer重命名器
  - 创建CloudRenamer类
  - 复用MediaParser解析文件名
  - 实现rename_file方法重命名单个文件
  - 实现batch_rename方法批量重命名
  - 实现preview_rename预览重命名结果
  - _需求: 4.1, 4.2, 6.1, 6.2, 6.3_

- [ ] 8. 实现CloudMover移动器
  - 创建CloudMover类
  - 实现move_file方法移动单个文件
  - 实现batch_move方法批量移动
  - 实现create_category_structure创建分类文件夹
  - 实现ensure_folder_exists确保文件夹存在
  - _需求: 7.1, 7.2, 7.3, 7.4_

- [ ] 9. 实现云端智能去重
  - 在CloudScanner中添加group_duplicate_files方法
  - 复用本地模块的质量评分逻辑
  - 实现基于文件名和大小的去重识别
  - 标记保留和删除的文件
  - 通过API删除低质量版本
  - _需求: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10. 实现API速率限制处理
  - 创建RateLimiter类
  - 实现速率检测和自动等待
  - 实现指数退避重试策略
  - 添加最大重试次数限制（3次）
  - 记录速率限制事件到日志
  - _需求: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 11. 实现云端操作历史记录
  - 创建cloud_history.json文件
  - 实现save_operation方法保存操作记录
  - 实现load_history方法加载历史记录



  - 限制历史记录最多保存100条
  - 实现按日期和类型筛选功能
  - _需求: 11.1, 11.2, 11.3, 11.4_

- [ ] 12. 实现后端API端点
  - 实现POST /api/cloud/verify-cookie验证Cookie
  - 实现POST /api/cloud/list-folders列出文件夹
  - 实现POST /api/cloud/scan扫描文件
  - 实现POST /api/cloud/smart-organize智能整理
  - 实现POST /api/cloud/get-history获取历史
  - _需求: 1.2, 2.1, 3.1, 6.1, 11.3_






- [ ] 13. 实现前端模块切换界面
  - 在index.html添加模块切换选项卡（本地/115网盘）




  - 实现switchModule函数切换模块
  - 保存用户选择的模块到localStorage
  - 根据模块显示不同的配置选项
  - 添加模块切换动画效果
  - _需求: 9.1, 9.2, 9.3_

- [ ] 14. 实现前端115网盘配置界面
  - 在设置中添加"115网盘配置"区域
  - 添加Cookie输入框和验证按钮
  - 实现verifyCookie函数调用验证API
  - 显示用户信息（用户名、空间使用情况）
  - 添加Cookie过期提醒
  - _需求: 1.1, 1.2, 1.3, 1.5_

- [ ] 15. 实现前端云端目录浏览器
  - 创建云端文件夹浏览组件
  - 实现loadCloudFolders函数加载文件夹列表
  - 支持点击展开子文件夹
  - 显示文件夹的文件数量和大小
  - 添加搜索功能快速定位文件夹
  - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 16. 实现前端云端整理流程
  - 创建云端整理界面
  - 实现startCloudOrganize函数启动整理
  - 显示8步处理流程进度
  - 实时更新处理状态和日志
  - 支持取消正在进行的操作
  - _需求: 8.1, 8.2, 8.3, 8.4_

- [ ] 17. 实现前端操作历史显示
  - 创建云端操作历史界面
  - 实现loadCloudHistory函数加载历史
  - 显示最近100条操作记录
  - 支持按日期和类型筛选
  - 添加导出CSV功能
  - _需求: 11.3, 11.4, 11.5_

- [ ] 18. 添加错误处理和用户反馈
  - 实现Cookie过期检测和提示
  - 实现API错误的友好提示
  - 添加网络错误重试提示
  - 实现操作失败的详细错误日志
  - 添加常见问题的一键修复按钮
  - _需求: 10.4, 10.5, 12.5_

- [ ] 19. 性能优化和缓存实现
  - 实现内存缓存系统
  - 添加文件夹列表缓存（5分钟）
  - 添加文件信息缓存（10分钟）
  - 实现缓存失效和刷新机制
  - 添加缓存统计和监控
  - _需求: 性能优化_

- [ ] 20. 安全加固和测试
  - 实现Cookie加密密钥管理
  - 添加敏感信息日志脱敏
  - 实现Cookie清除功能
  - 添加异常访问检测
  - 编写单元测试和集成测试
  - _需求: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 21. 文档和用户指南
  - 更新README添加115网盘模块说明
  - 创建115网盘Cookie获取指南
  - 编写云端整理使用教程
  - 添加常见问题解答
  - 创建API文档
  - _需求: 所有需求_
