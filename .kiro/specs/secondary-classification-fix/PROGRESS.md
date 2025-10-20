# 二级分类修复 - 实施进度

## ✅ 已完成（Tasks 1-7 + 部分 Task 8）

### 后端核心功能（100% 完成）

1. ✅ **MediaLibraryDetector 类** - 自动检测电影/电视剧目录
2. ✅ **SecondaryClassificationDetector 类** - 检测二级分类目录
3. ✅ **PathGenerator 类** - 生成正确的路径结构
4. ✅ **文件名格式修复** - 正确的文件名格式
5. ✅ **generate_output_path() 重构** - 支持新旧配置
6. ✅ **handle_smart_rename() 集成** - 支持媒体库路径
7. ✅ **ConfigManager 类** - 配置管理和迁移

### 前端界面（50% 完成）

8. ⚡ **前端 HTML 更新** - 配置界面 HTML 已完成
   - ✅ 媒体库路径输入框
   - ✅ 文件夹浏览按钮
   - ✅ 检测按钮
   - ✅ 语言偏好选择
   - ✅ 旧配置兼容（隐藏）
   - ❌ JavaScript 函数（待实现）

---

## 🔄 进行中（Task 8 剩余部分）

### 需要实现的 JavaScript 函数

#### 1. detectMediaLibraryStructure()
检测媒体库结构并显示结果

```javascript
async function detectMediaLibraryStructure() {
    const mediaLibraryPath = document.getElementById('mediaLibraryPath').value.trim();
    
    if (!mediaLibraryPath) {
        alert('请先输入媒体库路径');
        return;
    }
    
    try {
        // 调用后端 API 检测结构
        const response = await fetch('/api/detect-media-library', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: mediaLibraryPath })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 显示检测结果
            const infoDiv = document.getElementById('mediaLibraryInfo');
            const structureDiv = document.getElementById('detectedStructure');
            
            let html = '<strong>✓ 检测成功：</strong><br>';
            if (data.movie_dir) {
                html += `📁 电影目录: ${data.movie_dir}<br>`;
            }
            if (data.tv_dir) {
                html += `📁 电视剧目录: ${data.tv_dir}<br>`;
            }
            if (data.movie_categories && data.movie_categories.length > 0) {
                html += `🎬 电影分类: ${data.movie_categories.join(', ')}<br>`;
            }
            if (data.tv_categories && data.tv_categories.length > 0) {
                html += `📺 电视剧分类: ${data.tv_categories.join(', ')}`;
            }
            
            structureDiv.innerHTML = html;
            infoDiv.style.display = 'block';
        } else {
            alert('检测失败: ' + data.error);
        }
    } catch (error) {
        alert('检测失败: ' + error.message);
    }
}
```

#### 2. showNewConfig()
显示新配置，隐藏旧配置

```javascript
function showNewConfig() {
    document.getElementById('legacyConfig').style.display = 'none';
    document.getElementById('mediaLibraryPath').parentElement.parentElement.style.display = 'block';
    document.getElementById('preferredLanguage').parentElement.style.display = 'block';
}
```

#### 3. 更新 openFolderBrowser()
支持 'media' 类型

```javascript
// 在现有的 openFolderBrowser 函数中添加 'media' 类型支持
function openFolderBrowser(type) {
    currentBrowserType = type;
    let inputId = 'folderPath';
    if (type === 'movie') {
        inputId = 'movieOutputPath';
    } else if (type === 'tv') {
        inputId = 'tvOutputPath';
    } else if (type === 'media') {
        inputId = 'mediaLibraryPath';
    }
    // ... 其余代码
}
```

#### 4. 更新 localStorage 保存/加载
保存和加载媒体库路径配置

```javascript
// 在页面加载时
const savedMediaLibraryPath = localStorage.getItem('mediaLibraryPath');
if (savedMediaLibraryPath) {
    document.getElementById('mediaLibraryPath').value = savedMediaLibraryPath;
}

const savedLanguage = localStorage.getItem('preferredLanguage');
if (savedLanguage) {
    document.getElementById('preferredLanguage').value = savedLanguage;
}

// 在保存时
localStorage.setItem('mediaLibraryPath', mediaLibraryPath);
localStorage.setItem('preferredLanguage', language);
```

#### 5. 更新 smartRename()
传递新的参数

```javascript
// 在 smartRename 函数中
const mediaLibraryPath = document.getElementById('mediaLibraryPath').value.trim();
const language = document.getElementById('preferredLanguage').value;

// 发送请求时
body: JSON.stringify({
    files: filtered,
    basePath: currentFolder,
    mediaLibraryPath: mediaLibraryPath,
    language: language,
    // 旧配置（向后兼容）
    movieOutputPath: movieOutputPath,
    tvOutputPath: tvOutputPath,
    autoDedupe
})
```

---

## 📋 待完成（Tasks 9-14）

### Task 9: 更新前端界面 - 整理页面
- 修改整理页面的路径配置
- 显示将要使用的目录结构
- 添加路径预览功能

### Task 10: 添加配置迁移提示
- 检测用户是否使用旧配置
- 显示迁移提示对话框
- 提供一键迁移功能

### Task 11: 单元测试
- 测试所有核心类
- 测试路径生成
- 测试配置迁移

### Task 12: 集成测试
- 测试完整流程
- 测试向后兼容性
- 测试错误处理

### Task 13: 性能优化
- 优化目录扫描
- 优化批量处理
- 添加性能监控

### Task 14: 文档更新
- 更新使用指南
- 添加配置说明
- 更新 API 文档

---

## 🚀 后端 API 需要添加

### /api/detect-media-library
检测媒体库结构的 API

```python
def handle_detect_media_library(self, data):
    """检测媒体库结构"""
    try:
        path = data.get('path', '')
        if not path:
            self.send_json_response({'error': '路径不能为空'}, 400)
            return
        
        # 使用 MediaLibraryDetector
        detector = MediaLibraryDetector(path)
        structure = detector.detect_structure()
        
        # 获取分类目录
        movie_categories = []
        tv_categories = []
        
        if structure['movie_path']:
            classifier = SecondaryClassificationDetector(structure['movie_path'])
            movie_categories = list(classifier.existing_categories.keys())
        
        if structure['tv_path']:
            classifier = SecondaryClassificationDetector(structure['tv_path'])
            tv_categories = list(classifier.existing_categories.keys())
        
        self.send_json_response({
            'success': True,
            'movie_dir': structure['movie_dir'],
            'tv_dir': structure['tv_dir'],
            'movie_path': structure['movie_path'],
            'tv_path': structure['tv_path'],
            'movie_categories': movie_categories,
            'tv_categories': tv_categories
        })
    except Exception as e:
        self.send_json_response({'error': str(e)}, 500)
```

需要在 `do_POST` 中添加路由：
```python
elif self.path == '/api/detect-media-library':
    self.handle_detect_media_library(data)
```

---

## 📝 下一步操作

1. **添加后端 API** - `/api/detect-media-library`
2. **实现 JavaScript 函数** - 上述 5 个函数
3. **同步到 public/index.html** - 复制修改后的文件
4. **测试功能** - 验证检测和整理功能
5. **完成剩余任务** - Tasks 9-14

---

## 💡 提示

- 所有后端核心功能已完成，可以直接使用
- 前端只需要调用现有的后端功能
- 重点是实现 JavaScript 函数和 API 调用
- 测试时注意新旧配置的兼容性

---

## 🎯 预期效果

完成后，用户可以：
1. 输入媒体库路径
2. 点击"检测"按钮查看目录结构
3. 选择语言偏好
4. 执行整理，文件自动保存到正确的二级分类目录
5. 文件名格式正确：`剧名 - S01E08 - 第 08 集.mkv`
