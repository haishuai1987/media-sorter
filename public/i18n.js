// 多语言支持 - i18n

const translations = {
    'zh-CN': {
        // 导航
        'nav.process': '批量处理',
        'nav.recognize': '文件识别',
        'nav.batchEdit': '批量编辑',
        'nav.history': '历史记录',
        'nav.configs': '配置管理',
        'nav.templates': '模板管理',
        'nav.words': '识别词',
        'nav.stats': '统计信息',
        
        // 按钮
        'btn.process': '🚀 开始处理',
        'btn.preview': '👁️ 预览',
        'btn.import': '📥 导入列表',
        'btn.export': '📤 导出结果',
        'btn.clear': '🗑️ 清空',
        'btn.recognize': '🔍 识别',
        'btn.save': '💾 保存',
        'btn.apply': '✅ 应用',
        'btn.cancel': '取消',
        'btn.close': '关闭',
        'btn.delete': '删除',
        'btn.add': '➕ 添加',
        'btn.use': '使用',
        'btn.loadMore': '加载更多',
        
        // 标题
        'title.process': '📦 批量处理',
        'title.recognize': '🔍 文件识别',
        'title.batchEdit': '✏️ 批量编辑',
        'title.history': '📜 历史记录',
        'title.configs': '⚙️ 配置管理',
        'title.templates': '📝 模板管理',
        'title.words': '📚 自定义识别词',
        'title.stats': '📊 统计信息',
        
        // 描述
        'desc.process': '智能识别并重命名媒体文件',
        'desc.recognize': '测试单个文件的识别效果',
        'desc.batchEdit': '高级批量编辑功能',
        'desc.history': '查看和管理处理历史',
        'desc.configs': '保存和管理常用配置',
        'desc.templates': '管理文件命名模板',
        'desc.words': '管理屏蔽词和替换词',
        'desc.stats': '系统运行统计',
        
        // 表单
        'form.fileList': '文件列表（每行一个文件名）',
        'form.template': '模板',
        'form.priority': '优先级',
        'form.useQueue': '使用队列管理',
        'form.filename': '文件名',
        'form.configName': '配置名称',
        'form.description': '描述',
        
        // 消息
        'msg.processing': '处理中...',
        'msg.success': '成功',
        'msg.error': '错误',
        'msg.warning': '警告',
        'msg.noFiles': '请输入文件列表',
        'msg.noResults': '没有可导出的结果',
        'msg.confirmDelete': '确定要删除吗？',
        
        // 快捷键
        'shortcut.saveConfig': '保存配置',
        'shortcut.preview': '预览结果',
        'shortcut.process': '开始处理',
        'shortcut.clear': '清空内容',
        'shortcut.toggleTheme': '切换主题',
        'shortcut.showHistory': '查看历史',
        'shortcut.showHelp': '显示帮助',
        'shortcut.closeModal': '关闭弹窗',
        
        // 其他
        'theme.light': '亮色主题',
        'theme.dark': '暗色主题',
        'theme.highContrast': '高对比度',
        'language': '语言',
        'version': '版本'
    },
    
    'en-US': {
        // Navigation
        'nav.process': 'Batch Process',
        'nav.recognize': 'File Recognition',
        'nav.batchEdit': 'Batch Edit',
        'nav.history': 'History',
        'nav.configs': 'Configurations',
        'nav.templates': 'Templates',
        'nav.words': 'Custom Words',
        'nav.stats': 'Statistics',
        
        // Buttons
        'btn.process': '🚀 Start Processing',
        'btn.preview': '👁️ Preview',
        'btn.import': '📥 Import List',
        'btn.export': '📤 Export Results',
        'btn.clear': '🗑️ Clear',
        'btn.recognize': '🔍 Recognize',
        'btn.save': '💾 Save',
        'btn.apply': '✅ Apply',
        'btn.cancel': 'Cancel',
        'btn.close': 'Close',
        'btn.delete': 'Delete',
        'btn.add': '➕ Add',
        'btn.use': 'Use',
        'btn.loadMore': 'Load More',
        
        // Titles
        'title.process': '📦 Batch Processing',
        'title.recognize': '🔍 File Recognition',
        'title.batchEdit': '✏️ Batch Edit',
        'title.history': '📜 History',
        'title.configs': '⚙️ Configuration Management',
        'title.templates': '📝 Template Management',
        'title.words': '📚 Custom Words',
        'title.stats': '📊 Statistics',
        
        // Descriptions
        'desc.process': 'Intelligently recognize and rename media files',
        'desc.recognize': 'Test recognition effect of a single file',
        'desc.batchEdit': 'Advanced batch editing features',
        'desc.history': 'View and manage processing history',
        'desc.configs': 'Save and manage common configurations',
        'desc.templates': 'Manage file naming templates',
        'desc.words': 'Manage block words and replacement words',
        'desc.stats': 'System operation statistics',
        
        // Forms
        'form.fileList': 'File List (one file per line)',
        'form.template': 'Template',
        'form.priority': 'Priority',
        'form.useQueue': 'Use Queue Management',
        'form.filename': 'Filename',
        'form.configName': 'Configuration Name',
        'form.description': 'Description',
        
        // Messages
        'msg.processing': 'Processing...',
        'msg.success': 'Success',
        'msg.error': 'Error',
        'msg.warning': 'Warning',
        'msg.noFiles': 'Please enter file list',
        'msg.noResults': 'No results to export',
        'msg.confirmDelete': 'Are you sure to delete?',
        
        // Shortcuts
        'shortcut.saveConfig': 'Save Configuration',
        'shortcut.preview': 'Preview Results',
        'shortcut.process': 'Start Processing',
        'shortcut.clear': 'Clear Content',
        'shortcut.toggleTheme': 'Toggle Theme',
        'shortcut.showHistory': 'Show History',
        'shortcut.showHelp': 'Show Help',
        'shortcut.closeModal': 'Close Modal',
        
        // Others
        'theme.light': 'Light Theme',
        'theme.dark': 'Dark Theme',
        'theme.highContrast': 'High Contrast',
        'language': 'Language',
        'version': 'Version'
    }
};

class I18n {
    constructor() {
        this.currentLang = this.detectLanguage();
        this.translations = translations;
    }

    // 检测浏览器语言
    detectLanguage() {
        const saved = localStorage.getItem('language');
        if (saved && translations[saved]) {
            return saved;
        }

        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang.startsWith('zh')) {
            return 'zh-CN';
        }
        return 'en-US';
    }

    // 设置语言
    setLanguage(lang) {
        if (translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('language', lang);
            return true;
        }
        return false;
    }

    // 获取翻译
    t(key) {
        const lang = translations[this.currentLang];
        return lang[key] || key;
    }

    // 获取当前语言
    getCurrentLanguage() {
        return this.currentLang;
    }

    // 获取所有语言
    getLanguages() {
        return {
            'zh-CN': '简体中文',
            'en-US': 'English'
        };
    }
}

// 导出单例
const i18n = new I18n();
