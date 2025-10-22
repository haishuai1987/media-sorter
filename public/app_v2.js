// Media Renamer v2.5.0 - 前端 JavaScript

class MediaRenamerApp {
    constructor() {
        this.isProcessing = false;
        this.statusInterval = null;
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
        document.getElementById('process-btn').addEventListener('click', () => {
            this.startProcessing();
        });

        document.getElementById('clear-btn').addEventListener('click', () => {
            document.getElementById('file-list').value = '';
            this.hideResults();
        });

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
