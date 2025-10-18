# 需求文档

## 简介

本功能为媒体库管理器Web界面添加一键更新按钮，允许用户直接从GitHub仓库拉取最新代码并重启服务，无需手动SSH操作。支持直连和代理两种更新方式，以应对不同网络环境下的GitHub访问问题。

## 术语表

- **System**: 媒体库管理器Web应用程序
- **Update Button**: Web界面上的更新按钮控件
- **Git Repository**: GitHub上的远程代码仓库
- **Proxy Server**: HTTP/HTTPS代理服务器，用于访问GitHub
- **Service Restart**: 应用程序服务的停止和重新启动过程
- **Update Status**: 更新操作的执行状态（进行中、成功、失败）
- **Direct Connection**: 不使用代理直接连接GitHub
- **Proxy Connection**: 通过代理服务器连接GitHub

## 需求

### 需求 1: Web界面更新按钮

**用户故事:** 作为系统管理员，我希望在Web界面上看到一个更新按钮，以便我可以方便地更新系统而无需使用命令行。

#### 验收标准

1. THE System SHALL 在Web界面的设置区域显示一个"检查更新"按钮
2. WHEN 用户点击"检查更新"按钮, THE System SHALL 显示当前版本和最新可用版本信息
3. WHEN 检测到新版本可用, THE System SHALL 显示"立即更新"按钮
4. THE System SHALL 在按钮旁边显示更新状态指示器（空闲、检查中、更新中、成功、失败）

### 需求 2: Git更新执行

**用户故事:** 作为系统管理员，我希望系统能够自动从GitHub拉取最新代码，以便保持系统处于最新状态。

#### 验收标准

1. WHEN 用户点击"立即更新"按钮, THE System SHALL 执行git pull命令从远程仓库获取最新代码
2. WHILE 更新操作执行中, THE System SHALL 显示实时进度信息
3. IF git pull命令执行失败, THEN THE System SHALL 记录错误信息并显示给用户
4. WHEN git pull成功完成, THE System SHALL 显示更新成功消息和变更摘要
5. THE System SHALL 在更新操作超过60秒时显示超时警告

### 需求 3: 代理配置支持

**用户故事:** 作为在受限网络环境中的系统管理员，我希望能够配置代理服务器，以便在直连GitHub失败时通过代理完成更新。

#### 验收标准

1. THE System SHALL 提供代理服务器配置界面，包含代理地址和端口输入框
2. WHEN 用户保存代理配置, THE System SHALL 验证代理地址格式的有效性
3. WHEN 直连更新失败, THE System SHALL 自动尝试使用配置的代理服务器重新执行更新
4. WHERE 代理已配置, THE System SHALL 在更新界面显示"使用代理更新"选项
5. THE System SHALL 将代理配置持久化保存到配置文件中

### 需求 4: 自动服务重启

**用户故事:** 作为系统管理员，我希望系统在更新完成后自动重启服务，以便新代码立即生效而无需手动操作。

#### 验收标准

1. WHEN 代码更新成功完成, THE System SHALL 提示用户即将重启服务
2. THE System SHALL 在5秒倒计时后自动执行服务重启
3. WHEN 服务重启开始, THE System SHALL 向所有连接的客户端发送通知消息
4. THE System SHALL 使用现有的stop.sh和start.sh脚本执行重启操作
5. IF 服务重启失败, THEN THE System SHALL 记录错误日志并保持当前服务运行

### 需求 5: 版本号管理

**用户故事:** 作为系统管理员，我希望系统能够自动管理版本号，以便我能够清楚地看到当前运行的版本和是否有新版本可用。

#### 验收标准

1. THE System SHALL 在version.txt文件中维护语义化版本号（格式：v主版本.次版本.修订号）
2. WHEN 代码上传到GitHub, THE System SHALL 自动递增修订号（如v1.0.1 -> v1.0.2）
3. THE System SHALL 在Web界面首页显著位置显示当前版本号
4. WHEN 检查更新时, THE System SHALL 比较本地版本号与GitHub最新版本号
5. THE System SHALL 在更新完成后自动读取并显示新的版本号

### 需求 6: 更新日志和回滚

**用户故事:** 作为系统管理员，我希望查看更新历史记录，以便了解系统变更情况并在必要时回滚到之前版本。

#### 验收标准

1. THE System SHALL 记录每次更新操作的时间戳、版本号和执行结果
2. THE System SHALL 在Web界面显示最近10次更新历史记录
3. WHEN 更新失败, THE System SHALL 保留失败前的代码状态
4. THE System SHALL 显示当前Git提交哈希值和分支信息
5. WHERE 更新导致问题, THE System SHALL 提供"回滚到上一版本"功能按钮

### 需求 7: 安全性和权限控制

**用户故事:** 作为系统管理员，我希望更新功能有适当的安全控制，以防止未授权的更新操作。

#### 验收标准

1. THE System SHALL 要求管理员权限才能访问更新功能
2. WHEN 执行更新操作, THE System SHALL 记录操作用户和IP地址到审计日志
3. THE System SHALL 在更新前显示确认对话框，要求用户二次确认
4. THE System SHALL 限制同一时间只能有一个更新操作执行
5. IF 检测到本地有未提交的代码修改, THEN THE System SHALL 警告用户并阻止更新操作

### 需求 8: 错误处理和用户反馈

**用户故事:** 作为系统管理员，我希望在更新过程中遇到问题时能够获得清晰的错误信息，以便我能够采取适当的解决措施。

#### 验收标准

1. WHEN 网络连接失败, THE System SHALL 显示"无法连接到GitHub，请检查网络或配置代理"错误消息
2. WHEN Git仓库状态异常, THE System SHALL 显示具体的Git错误信息和建议解决方案
3. THE System SHALL 为常见错误提供一键修复按钮（如重置本地修改、重新克隆仓库）
4. WHEN 更新操作失败, THE System SHALL 保存完整的错误日志到文件供技术支持分析
5. THE System SHALL 在更新过程中显示可取消按钮，允许用户中止长时间运行的操作
