// Media Renamer v2.5.0 - 前端 JavaScript

class MediaRenamerApp {
    constructor() {
        this.isProcessing = false;
        this.statusInterval = null;
        this.historyOffset = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSystemInfo();
        this.loadTemplates();
        this.loadCustomWords();
        this.loadStats();
    }

    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.dataset.tab);
            });
        });

        // 批量处理
        document.getElementById('preview-btn').addEventListener('click', () => {
            this.previewProcessing();
        });

        document.getElementById('process-btn').addEventListener('click', () => {
            this.startProcessing();
        });

        document.getElementById('clear-btn').addEventListener('click', () => {
            document.getElementById('file-list').value = '';
            this.hideResults();
        });

        // 导入/导出
        document.getElementById('import-btn').addEventListener('click', () => {
            document.getElementById('import-input').click();
        });

        document.getElementById('import-input').addEventListener('change', (e) => {
            this.importFileList(e.target.files[0]);
        });

        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportResults();
        });

        // 文件拖拽上传
        this.initDragDrop();

        // 文件识别
        document.getElementById('recognize-btn').addEventListener('click', () => {
            this.recognizeFile();
        });

        // 识别词管理
        document.getElementById('word-type').addEventListener('change', (e) => {
            this.toggleWordFields(e.target.value);
        });

        document.getElementById('add-word-btn').addEventListener('click', () => {
            this.addCustomWord();
        });

        // 历史记录
        document.getElementById('history-search-btn').addEventListener('click', () => {
            this.historyOffset = 0;
            this.loadHistory();
        });

        document.getElementById('history-clear-btn').addEventListener('click', () => {
            this.clearHistory();
        });

        document.getElementById('history-load-more').addEventListener('click', () => {
            this.historyOffset += 20;
            this.loadHistory(true);
        });

        // 配置管理
        document.getElementById('add-config-btn').addEventListener('click', () => {
            this.addConfig();
        });
    }

    // 初始化拖拽上传
    initDragDrop() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const fileList = document.getElementById('file-list');

        // 点击选择文件
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // 文件选择
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // 拖拽进入
        dropZone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        // 拖拽悬停
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });

        // 拖拽离开
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });

        // 拖拽放下
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });
    }

    // 处理文件
    handleFiles(files) {
        if (files.length === 0) return;

        const fileList = document.getElementById('file-list');
        const fileNames = [];

        for (let i = 0; i < files.length; i++) {
            fileNames.push(files[i].name);
        }

        // 添加到文本框（追加模式）
        const currentValue = fileList.value.trim();
        if (currentValue) {
            fileList.value = currentValue + '\n' + fileNames.join('\n');
        } else {
            fileList.value = fileNames.join('\n');
        }

        this.showToast(`已添加 ${files.length} 个文件`, 'success');
    }

    // 标签页切换
    switchTab(tabName) {
        // 更新导航
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // 加载对应数据
        if (tabName === 'templates') {
            this.loadTemplates();
        } else if (tabName === 'words') {
            this.loadCustomWords();
        } else if (tabName === 'history') {
            this.loadHistory();
        } else if (tabName === 'configs') {
            this.loadConfigs();
        } else if (tabName === 'stats') {
            this.loadStats();
        }
    }

    // 加载系统信息
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/info');
            const data = await response.json();
            
            if (data.success) {
                console.log('系统信息:', data.data);
            }
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    }

    // 预览处理结果
    async previewProcessing() {
        const fileList = document.getElementById('file-list').value.trim();
        if (!fileList) {
            this.showToast('请输入文件列表', 'warning');
            return;
        }

        const files = fileList.split('\n').filter(f => f.trim());
        const template = document.getElementById('template-select').value;

        const previewSection = document.getElementById('preview-section');
        const previewList = document.getElementById('preview-list');
        
        previewSection.style.display = 'block';
        previewList.innerHTML = '<div class="loading-text">正在生成预览...</div>';

        try {
            // 对每个文件进行识别
            const previews = [];
            for (const file of files.slice(0, 10)) { // 最多预览10个
                try {
                    const response = await fetch('/api/recognize', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ filename: file })
                    });

                    const data = await response.json();
                    if (data.success) {
                        previews.push({
                            original: file,
                            info: data.data,
                            success: true
                        });
                    } else {
                        previews.push({
                            original: file,
                            error: data.error,
                            success: false
                        });
                    }
                } catch (error) {
                    previews.push({
                        original: file,
                        error: error.message,
                        success: false
                    });
                }
            }

            // 显示预览
            previewList.innerHTML = '';
            previews.forEach(preview => {
                const item = document.createElement('div');
                item.className = `result-item ${preview.success ? 'success' : 'error'}`;
                
                if (preview.success) {
                    // 生成新文件名（简化版）
                    const info = preview.info;
                    let newName = '';
                    if (info.is_tv) {
                        newName = `${info.title} S${String(info.season).padStart(2, '0')}E${String(info.episode).padStart(2, '0')}`;
                    } else {
                        newName = `${info.title} (${info.year || 'Unknown'})`;
                    }
                    
                    item.innerHTML = `
                        <div class="result-original">原始: ${preview.original}</div>
                        <div class="result-new">预览: ${newName}</div>
                        <div class="result-info">
                            <span>类型: ${info.is_tv ? '电视剧' : '电影'}</span>
                            ${info.year ? `<span>年份: ${info.year}</span>` : ''}
                        </div>
                    `;
                } else {
                    item.innerHTML = `
                        <div class="result-original">文件: ${preview.original}</div>
                        <div class="result-new" style="color: var(--danger-color);">错误: ${preview.error}</div>
                    `;
                }
                
                previewList.appendChild(item);
            });

            if (files.length > 10) {
                const moreInfo = document.createElement('div');
                moreInfo.className = 'result-info';
                moreInfo.style.textAlign = 'center';
                moreInfo.style.marginTop = '1rem';
                moreInfo.innerHTML = `<span>还有 ${files.length - 10} 个文件未预览</span>`;
                previewList.appendChild(moreInfo);
            }

            this.showToast('预览生成完成', 'success');
        } catch (error) {
            previewList.innerHTML = `<div class="error-text">预览失败: ${error.message}</div>`;
            this.showToast('预览失败: ' + error.message, 'error');
        }
    }

    // 开始批量处理
    async startProcessing() {
        const fileList = document.getElementById('file-list').value.trim();
        if (!fileList) {
            this.showToast('请输入文件列表', 'warning');
            return;
        }

        const files = fileList.split('\n').filter(f => f.trim());
        const template = document.getElementById('template-select').value;
        const priority = parseInt(document.getElementById('priority-select').value);
        const useQueue = document.getElementById('use-queue').checked;

        try {
            this.setProcessing(true);
            
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    files,
                    template,
                    priority,
                    use_queue: useQueue
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('处理已开始', 'success');
                this.showProgress();
                this.startStatusPolling();
            } else {
                this.showToast(data.error, 'error');
                this.setProcessing(false);
            }
        } catch (error) {
            this.showToast('请求失败: ' + error.message, 'error');
            this.setProcessing(false);
        }
    }

    // 设置处理状态
    setProcessing(processing) {
        this.isProcessing = processing;
        const btn = document.getElementById('process-btn');
        
        if (processing) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loading"></span> 处理中...';
        } else {
            btn.disabled = false;
            btn.innerHTML = '🚀 开始处理';
        }
    }

    // 显示进度
    showProgress() {
        document.getElementById('progress-section').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
    }

    // 隐藏结果
    hideResults() {
        document.getElementById('progress-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
    }

    // 开始状态轮询
    startStatusPolling() {
        this.statusInterval = setInterval(() => {
            this.checkStatus();
        }, 1000);
    }

    // 停止状态轮询
    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    // 检查处理状态
    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateProgress(data.data);
                
                if (!data.data.is_processing) {
                    this.stopStatusPolling();
                    this.setProcessing(false);
                    this.showResults(data.data.results);
                }
            }
        } catch (error) {
            console.error('状态检查失败:', error);
        }
    }

    // 更新进度
    updateProgress(status) {
        const progress = Math.round(status.progress * 100);
        
        document.getElementById('progress-fill').style.width = progress + '%';
        document.getElementById('progress-percent').textContent = progress + '%';
        
        if (status.current_file) {
            document.getElementById('progress-status').textContent = 
                `正在处理: ${status.current_file}`;
        }
    }

    // 显示结果
    showResults(results) {
        const resultsSection = document.getElementById('results-section');
        const resultsList = document.getElementById('results-list');
        
        // 保存结果以便导出
        this.lastResults = results;
        
        resultsSection.style.display = 'block';
        resultsList.innerHTML = '';
        
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = `result-item ${result.success ? 'success' : 'error'}`;
            
            if (result.success) {
                item.innerHTML = `
                    <div class="result-original">原始: ${result.original_name}</div>
                    <div class="result-new">新名: ${result.new_name}</div>
                    <div class="result-info">
                        <span>质量分数: ${result.quality_score}</span>
                        <span>类型: ${result.info.is_tv ? '电视剧' : '电影'}</span>
                        ${result.info.year ? `<span>年份: ${result.info.year}</span>` : ''}
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="result-original">文件: ${result.file_path}</div>
                    <div class="result-new" style="color: var(--danger-color);">错误: ${result.error}</div>
                `;
            }
            
            resultsList.appendChild(item);
        });
    }

    // 识别文件
    async recognizeFile() {
        const filename = document.getElementById('recognize-input').value.trim();
        if (!filename) {
            this.showToast('请输入文件名', 'warning');
            return;
        }

        const btn = document.getElementById('recognize-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> 识别中...';

        try {
            const response = await fetch('/api/recognize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showRecognizeResult(data.data);
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('识别失败: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '🔍 识别';
        }
    }

    // 显示识别结果
    showRecognizeResult(info) {
        const resultBox = document.getElementById('recognize-result');
        resultBox.style.display = 'block';
        
        resultBox.innerHTML = `
            <h4>识别结果</h4>
            <pre>${JSON.stringify(info, null, 2)}</pre>
        `;
    }

    // 加载模板列表
    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            const data = await response.json();
            
            if (data.success) {
                this.renderTemplates(data.data);
            }
        } catch (error) {
            console.error('加载模板失败:', error);
        }
    }

    // 渲染模板列表
    renderTemplates(templates) {
        const container = document.getElementById('templates-list');
        container.innerHTML = '';
        
        Object.entries(templates).forEach(([name, template]) => {
            const item = document.createElement('div');
            item.className = 'result-item';
            item.innerHTML = `
                <div class="result-original">模板: ${name}</div>
                <div class="result-new">${template}</div>
            `;
            container.appendChild(item);
        });
    }

    // 切换识别词字段
    toggleWordFields(type) {
        const blockFields = document.getElementById('block-fields');
        const replaceFields = document.getElementById('replace-fields');
        
        if (type === 'block') {
            blockFields.style.display = 'block';
            replaceFields.style.display = 'none';
        } else {
            blockFields.style.display = 'none';
            replaceFields.style.display = 'block';
        }
    }

    // 添加自定义识别词
    async addCustomWord() {
        const type = document.getElementById('word-type').value;
        const description = document.getElementById('word-description').value.trim();
        
        let wordData = {
            type,
            description,
            enabled: true
        };
        
        if (type === 'block') {
            const pattern = document.getElementById('word-pattern').value.trim();
            if (!pattern) {
                this.showToast('请输入屏蔽内容', 'warning');
                return;
            }
            wordData.pattern = pattern;
        } else {
            const old = document.getElementById('word-old').value.trim();
            const newText = document.getElementById('word-new').value.trim();
            if (!old || !newText) {
                this.showToast('请输入原文本和新文本', 'warning');
                return;
            }
            wordData.old = old;
            wordData.new = newText;
        }

        try {
            const response = await fetch('/api/custom-words', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(wordData)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('添加成功', 'success');
                this.clearWordForm();
                this.loadCustomWords();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('添加失败: ' + error.message, 'error');
        }
    }

    // 清空识别词表单
    clearWordForm() {
        document.getElementById('word-pattern').value = '';
        document.getElementById('word-old').value = '';
        document.getElementById('word-new').value = '';
        document.getElementById('word-description').value = '';
    }

    // 加载自定义识别词
    async loadCustomWords() {
        try {
            const response = await fetch('/api/custom-words');
            const data = await response.json();
            
            if (data.success) {
                this.renderCustomWords(data.data);
            }
        } catch (error) {
            console.error('加载识别词失败:', error);
        }
    }

    // 渲染自定义识别词
    renderCustomWords(words) {
        const container = document.getElementById('words-list');
        container.innerHTML = '';
        
        if (words.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📝</div>
                    <p>暂无自定义识别词</p>
                </div>
            `;
            return;
        }
        
        words.forEach((word, index) => {
            const item = document.createElement('div');
            item.className = `word-item ${word.enabled ? '' : 'disabled'}`;
            
            let content = '';
            if (word.type === 'block') {
                content = `屏蔽: ${word.pattern}`;
            } else {
                content = `替换: ${word.old} → ${word.new}`;
            }
            
            item.innerHTML = `
                <div class="word-info">
                    <div class="word-type ${word.type}">${word.type.toUpperCase()}</div>
                    <div>${content}</div>
                    <div style="color: var(--text-light); font-size: 0.875rem;">${word.description}</div>
                </div>
                <div class="word-actions">
                    <button class="btn btn-secondary" onclick="app.toggleCustomWord(${index})">
                        ${word.enabled ? '禁用' : '启用'}
                    </button>
                    <button class="btn btn-danger" onclick="app.deleteCustomWord(${index})">
                        删除
                    </button>
                </div>
            `;
            
            container.appendChild(item);
        });
    }

    // 切换识别词状态
    async toggleCustomWord(index) {
        try {
            const response = await fetch(`/api/custom-words/${index}/toggle`, {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('切换成功', 'success');
                this.loadCustomWords();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('切换失败: ' + error.message, 'error');
        }
    }

    // 删除识别词
    async deleteCustomWord(index) {
        if (!confirm('确定要删除这个识别词吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/custom-words/${index}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('删除成功', 'success');
                this.loadCustomWords();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('删除失败: ' + error.message, 'error');
        }
    }

    // 加载历史记录
    async loadHistory(append = false) {
        try {
            if (!append) {
                this.historyOffset = 0;
            }

            const search = document.getElementById('history-search').value.trim();
            const status = document.getElementById('history-status-filter').value;
            
            const params = new URLSearchParams({
                limit: '20',
                offset: this.historyOffset.toString()
            });
            
            if (search) params.append('search', search);
            if (status) params.append('status', status);
            
            const response = await fetch(`/api/history?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderHistory(data.data, append);
                
                // 加载统计
                const statsResponse = await fetch('/api/history/stats');
                const statsData = await statsResponse.json();
                if (statsData.success) {
                    this.renderHistoryStats(statsData.data);
                }
            }
        } catch (error) {
            console.error('加载历史失败:', error);
        }
    }

    // 渲染历史记录
    renderHistory(records, append = false) {
        const container = document.getElementById('history-list');
        
        if (!append) {
            container.innerHTML = '';
        }
        
        if (records.length === 0 && !append) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📜</div>
                    <p>暂无历史记录</p>
                </div>
            `;
            return;
        }
        
        records.forEach(record => {
            const item = document.createElement('div');
            item.className = `result-item ${record.status === 'success' ? 'success' : 'error'}`;
            
            const date = new Date(record.created_at).toLocaleString('zh-CN');
            
            if (record.status === 'success') {
                item.innerHTML = `
                    <div class="result-original">
                        原始: ${record.original_name}
                        <span style="color: var(--text-light); font-size: 0.875rem; margin-left: 1rem;">${date}</span>
                    </div>
                    <div class="result-new">新名: ${record.new_name}</div>
                    <div class="result-info">
                        <span>质量分数: ${record.quality_score || 'N/A'}</span>
                        <span>类型: ${record.file_type === 'tv' ? '电视剧' : '电影'}</span>
                        ${record.year ? `<span>年份: ${record.year}</span>` : ''}
                        <span>模板: ${record.template}</span>
                    </div>
                    <div class="word-actions">
                        <button class="btn btn-danger btn-sm" onclick="app.deleteHistoryRecord(${record.id})">
                            删除
                        </button>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="result-original">
                        文件: ${record.original_name}
                        <span style="color: var(--text-light); font-size: 0.875rem; margin-left: 1rem;">${date}</span>
                    </div>
                    <div class="result-new" style="color: var(--danger-color);">
                        错误: ${record.error_message}
                    </div>
                    <div class="word-actions">
                        <button class="btn btn-danger btn-sm" onclick="app.deleteHistoryRecord(${record.id})">
                            删除
                        </button>
                    </div>
                `;
            }
            
            container.appendChild(item);
        });
    }

    // 渲染历史统计
    renderHistoryStats(stats) {
        const container = document.getElementById('history-stats');
        
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.total || 0}</div>
                <div class="stat-label">总记录数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.success || 0}</div>
                <div class="stat-label">成功</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.failed || 0}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${((stats.success_rate || 0) * 100).toFixed(1)}%</div>
                <div class="stat-label">成功率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.today || 0}</div>
                <div class="stat-label">今天</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.this_week || 0}</div>
                <div class="stat-label">本周</div>
            </div>
        `;
    }

    // 删除历史记录
    async deleteHistoryRecord(id) {
        if (!confirm('确定要删除这条记录吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/history/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('删除成功', 'success');
                this.loadHistory();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('删除失败: ' + error.message, 'error');
        }
    }

    // 清空历史记录
    async clearHistory() {
        if (!confirm('确定要清空所有历史记录吗？此操作不可恢复！')) {
            return;
        }

        try {
            const response = await fetch('/api/history/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                this.loadHistory();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('清空失败: ' + error.message, 'error');
        }
    }

    // 加载配置
    async loadConfigs() {
        try {
            // 加载默认配置
            const defaultsResponse = await fetch('/api/configs/defaults');
            const defaultsData = await defaultsResponse.json();
            if (defaultsData.success) {
                this.renderDefaultConfigs(defaultsData.data);
            }

            // 加载用户配置
            const response = await fetch('/api/configs');
            const data = await response.json();
            if (data.success) {
                this.renderConfigs(data.data);
            }
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    // 渲染默认配置
    renderDefaultConfigs(configs) {
        const container = document.getElementById('default-configs-list');
        container.innerHTML = '';

        configs.forEach(config => {
            const item = document.createElement('div');
            item.className = 'result-item';
            item.innerHTML = `
                <div class="result-original">
                    <strong>${config.name}</strong>
                    <span style="color: var(--text-light); margin-left: 1rem;">${config.description}</span>
                </div>
                <div class="result-info">
                    <span>模板: ${config.template}</span>
                    <span>优先级: ${config.priority}</span>
                    <span>队列: ${config.use_queue ? '是' : '否'}</span>
                </div>
                <div class="word-actions">
                    <button class="btn btn-primary btn-sm" onclick='app.useConfig(${JSON.stringify(config)})'>
                        使用
                    </button>
                </div>
            `;
            container.appendChild(item);
        });
    }

    // 渲染用户配置
    renderConfigs(configs) {
        const container = document.getElementById('configs-list');
        container.innerHTML = '';

        if (configs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚙️</div>
                    <p>暂无保存的配置</p>
                </div>
            `;
            return;
        }

        configs.forEach(config => {
            const item = document.createElement('div');
            item.className = 'result-item';
            const date = new Date(config.created_at).toLocaleString('zh-CN');
            
            item.innerHTML = `
                <div class="result-original">
                    <strong>${config.name}</strong>
                    <span style="color: var(--text-light); margin-left: 1rem;">${config.description || ''}</span>
                    <span style="color: var(--text-light); font-size: 0.875rem; margin-left: 1rem;">${date}</span>
                </div>
                <div class="result-info">
                    <span>模板: ${config.template}</span>
                    <span>优先级: ${config.priority}</span>
                    <span>队列: ${config.use_queue ? '是' : '否'}</span>
                </div>
                <div class="word-actions">
                    <button class="btn btn-primary btn-sm" onclick='app.useConfig(${JSON.stringify(config)})'>
                        使用
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="app.exportConfig('${config.id}')">
                        导出
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteConfig('${config.id}')">
                        删除
                    </button>
                </div>
            `;
            container.appendChild(item);
        });
    }

    // 添加配置
    async addConfig() {
        const name = document.getElementById('config-name').value.trim();
        const description = document.getElementById('config-description').value.trim();
        const template = document.getElementById('config-template').value;
        const priority = parseInt(document.getElementById('config-priority').value);
        const useQueue = document.getElementById('config-use-queue').checked;

        if (!name) {
            this.showToast('请输入配置名称', 'warning');
            return;
        }

        const config = {
            name,
            description,
            template,
            priority,
            use_queue: useQueue,
            settings: {}
        };

        try {
            const response = await fetch('/api/configs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('配置保存成功', 'success');
                this.clearConfigForm();
                this.loadConfigs();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('保存失败: ' + error.message, 'error');
        }
    }

    // 清空配置表单
    clearConfigForm() {
        document.getElementById('config-name').value = '';
        document.getElementById('config-description').value = '';
        document.getElementById('config-template').value = 'movie_default';
        document.getElementById('config-priority').value = '5';
        document.getElementById('config-use-queue').checked = true;
    }

    // 使用配置
    useConfig(config) {
        // 切换到批量处理标签页
        this.switchTab('process');

        // 应用配置
        document.getElementById('template-select').value = config.template;
        document.getElementById('priority-select').value = config.priority;
        document.getElementById('use-queue').checked = config.use_queue;

        this.showToast(`已应用配置: ${config.name}`, 'success');
    }

    // 导出配置
    async exportConfig(configId) {
        try {
            const response = await fetch(`/api/configs/${configId}/export`);
            const data = await response.json();
            
            if (data.success) {
                // 创建下载
                const blob = new Blob([data.data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `config-${configId}.json`;
                link.click();
                URL.revokeObjectURL(url);

                this.showToast('导出成功', 'success');
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('导出失败: ' + error.message, 'error');
        }
    }

    // 删除配置
    async deleteConfig(configId) {
        if (!confirm('确定要删除这个配置吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/configs/${configId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('删除成功', 'success');
                this.loadConfigs();
            } else {
                this.showToast(data.error, 'error');
            }
        } catch (error) {
            this.showToast('删除失败: ' + error.message, 'error');
        }
    }

    // 加载统计信息
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                this.renderStats(data.data);
            }
        } catch (error) {
            console.error('加载统计失败:', error);
        }
    }

    // 渲染统计信息
    renderStats(stats) {
        const container = document.getElementById('stats-content');
        
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.total_files || 0}</div>
                    <div class="stat-label">总处理文件</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.success || 0}</div>
                    <div class="stat-label">成功处理</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.failed || 0}</div>
                    <div class="stat-label">处理失败</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${((stats.success_rate || 0) * 100).toFixed(1)}%</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
            
            ${stats.queue_stats ? `
                <div class="card">
                    <div class="card-header">
                        <h3>队列统计</h3>
                    </div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${stats.queue_stats.queue_size}</div>
                                <div class="stat-label">队列中任务</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.queue_stats.active_workers}</div>
                                <div class="stat-label">活跃工作线程</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${(stats.queue_stats.avg_processing_time || 0).toFixed(3)}s</div>
                                <div class="stat-label">平均处理时间</div>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            ${stats.rate_limit_stats ? `
                <div class="card">
                    <div class="card-header">
                        <h3>速率限制</h3>
                    </div>
                    <div class="card-body">
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${stats.rate_limit_stats.max_requests}</div>
                                <div class="stat-label">最大请求数</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.rate_limit_stats.time_window}s</div>
                                <div class="stat-label">时间窗口</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${(stats.rate_limit_stats.available_tokens || 0).toFixed(1)}</div>
                                <div class="stat-label">可用令牌</div>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
    }

    // 导入文件列表
    async importFileList(file) {
        if (!file) return;

        try {
            const text = await file.text();
            const fileList = document.getElementById('file-list');
            
            // 解析文件内容
            let lines = [];
            if (file.name.endsWith('.csv')) {
                // CSV 格式：可能有多列，取第一列
                lines = text.split('\n').map(line => {
                    const cols = line.split(',');
                    return cols[0].trim();
                }).filter(line => line);
            } else {
                // TXT 格式：每行一个文件名
                lines = text.split('\n').map(line => line.trim()).filter(line => line);
            }

            // 添加到文本框
            const currentValue = fileList.value.trim();
            if (currentValue) {
                fileList.value = currentValue + '\n' + lines.join('\n');
            } else {
                fileList.value = lines.join('\n');
            }

            this.showToast(`已导入 ${lines.length} 个文件`, 'success');
        } catch (error) {
            this.showToast('导入失败: ' + error.message, 'error');
        }
    }

    // 导出结果
    exportResults() {
        const resultsSection = document.getElementById('results-section');
        
        if (resultsSection.style.display === 'none') {
            this.showToast('没有可导出的结果', 'warning');
            return;
        }

        try {
            // 获取结果数据
            const results = this.lastResults || [];
            
            if (results.length === 0) {
                this.showToast('没有可导出的结果', 'warning');
                return;
            }

            // 生成 CSV 内容
            const csvLines = ['原文件名,新文件名,状态,质量分数,类型,年份'];
            
            results.forEach(result => {
                if (result.success) {
                    const line = [
                        result.original_name || '',
                        result.new_name || '',
                        '成功',
                        result.quality_score || '',
                        result.info.is_tv ? '电视剧' : '电影',
                        result.info.year || ''
                    ].join(',');
                    csvLines.push(line);
                } else {
                    const line = [
                        result.file_path || '',
                        '',
                        '失败',
                        '',
                        '',
                        ''
                    ].join(',');
                    csvLines.push(line);
                }
            });

            // 创建下载
            const csvContent = csvLines.join('\n');
            const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `media-renamer-results-${Date.now()}.csv`;
            link.click();
            URL.revokeObjectURL(url);

            this.showToast('导出成功', 'success');
        } catch (error) {
            this.showToast('导出失败: ' + error.message, 'error');
        }
    }

    // 显示 Toast 通知
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        }[type] || 'ℹ️';
        
        toast.innerHTML = `
            <span>${icon}</span>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
}

// 初始化应用
const app = new MediaRenamerApp();
