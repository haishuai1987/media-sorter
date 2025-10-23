# 多语言使用示例

## 🌍 如何使用多语言

### 1. 在 HTML 中添加 data-i18n 属性

```html
<!-- 文本内容 -->
<h2 data-i18n="title.process">批量处理</h2>
<p data-i18n="desc.process">智能识别并重命名媒体文件</p>

<!-- 按钮 -->
<button data-i18n="btn.process">🚀 开始处理</button>

<!-- 占位符 -->
<input type="text" data-i18n-placeholder="form.filename" placeholder="文件名">

<!-- 标题提示 -->
<button data-i18n-title="shortcut.showHelp" title="显示帮助">⌨️</button>
```

### 2. 在 i18n.js 中添加翻译

```javascript
const translations = {
    'zh-CN': {
        'title.process': '批量处理',
        'btn.process': '🚀 开始处理'
    },
    'en-US': {
        'title.process': 'Batch Process',
        'btn.process': '🚀 Start Processing'
    }
};
```

### 3. 切换语言

```javascript
// 点击按钮切换
document.getElementById('language-toggle').click();

// 或编程方式
i18n.setLanguage('en-US');
app.updateLanguage();
```

## 📝 翻译键命名规范

- `nav.*` - 导航菜单
- `title.*` - 页面标题
- `desc.*` - 描述文字
- `btn.*` - 按钮文字
- `form.*` - 表单标签
- `msg.*` - 提示消息
- `shortcut.*` - 快捷键描述

## 🎯 已支持的语言

- 🇨🇳 简体中文 (zh-CN)
- 🇺🇸 English (en-US)

## 🔄 自动检测

系统会自动检测浏览器语言：
- 中文浏览器 → 简体中文
- 其他语言 → English

## 💾 持久化

语言选择会保存到 LocalStorage，下次访问自动应用。

## 🚀 使用方式

1. 点击导航栏的 🌍 按钮
2. 自动切换语言
3. 界面立即更新

## 📊 当前状态

- ✅ 核心框架完成
- ✅ 中英文翻译
- ✅ 自动检测
- ✅ 持久化存储
- ⏳ 界面元素标记（需要逐步添加）

## 🔮 未来扩展

可以轻松添加更多语言：
- 🇯🇵 日本語
- 🇰🇷 한국어
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇪🇸 Español
