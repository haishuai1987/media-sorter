/**
 * 错误统计面板 (v1.8.0)
 * 显示实时错误统计和操作历史
 */

class ErrorStatsPanel {
    constructor() {
        this.modal = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        // 创建模态框
        this.modal = document.createElement('div');
        this.modal.id = 'error-stats-modal';
        this.modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        `;

        this.modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 800px;
                max-height: 80vh;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: modalSlideIn 0.3s ease-out;
            ">
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px 25px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h2 style="margin: 0; font-size: 20px;">📊 错误统计与操作历史</h2>
                    <button onclick="errorStatsPanel.close()" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 24px;
                        cursor: pointer;
                        padding: 5px 10px;
                        border-radius: 50%;
                        transition: background 0.2s;
                    ">×</button>
                </div>

                <div style="padding: 25px; overflow-y: auto; max-height: calc(80vh - 80px);">
                    <!-- 错误统计 -->
                    <div style="margin-bottom: 30px;">
                        <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px;">
                            🛡️ 错误统计
                        </h3>
                        <div id="error-stats-content" style="
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 15px;
                        ">
                            <!-- 动态内容 -->
                        </div>
                    </div>

                    <!-- 操作历史 -->
                    <div>
                        <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px;">
                            📜 操作历史
                        </h3>
                        <div id="operation-history-content">
                            <!-- 动态内容 -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-50px) scale(0.9);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
        `;
        document.head.appendChild(style);

        // 点击背景关闭
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        document.body.appendChild(this.modal);
    }

    async open() {
        this.modal.style.display = 'flex';
        await this.refresh();
        
        // 每5秒刷新一次
        this.refreshInterval = setInterval(() => {
            this.refresh();
        }, 5000);
    }

    close() {
        this.modal.style.display = 'none';
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async refresh() {
        await Promise.all([
            this.loadErrorStats(),
            this.loadOperationHistory()
        ]);
    }

    async loadErrorStats() {
        try {
            const response = await fetch('/api/error-stats');
            const data = await response.json();

            const container = document.getElementById('error-stats-content');
            if (!container) return;

            container.innerHTML = `
                <div style="
                    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #4caf50;
                ">
                    <div style="font-size: 32px; font-weight: 700; color: #2e7d32; margin-bottom: 5px;">
                        ${data.success_count || 0}
                    </div>
                    <div style="font-size: 14px; color: #558b2f;">
                        成功操作
                    </div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #f44336;
                ">
                    <div style="font-size: 32px; font-weight: 700; color: #c62828; margin-bottom: 5px;">
                        ${data.error_count || 0}
                    </div>
                    <div style="font-size: 14px; color: #d32f2f;">
                        错误次数
                    </div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #2196f3;
                ">
                    <div style="font-size: 32px; font-weight: 700; color: #1565c0; margin-bottom: 5px;">
                        ${((data.error_rate || 0) * 100).toFixed(1)}%
                    </div>
                    <div style="font-size: 14px; color: #1976d2;">
                        错误率
                    </div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #ff9800;
                ">
                    <div style="font-size: 32px; font-weight: 700; color: #e65100; margin-bottom: 5px;">
                        ${data.request_count || 0}
                    </div>
                    <div style="font-size: 14px; color: #f57c00;">
                        总请求数
                    </div>
                </div>
            `;

            // 显示最后错误
            if (data.last_error) {
                container.innerHTML += `
                    <div style="
                        grid-column: 1 / -1;
                        background: #fff3cd;
                        padding: 15px;
                        border-radius: 8px;
                        border-left: 4px solid #ffc107;
                        margin-top: 15px;
                    ">
                        <div style="font-weight: 600; color: #856404; margin-bottom: 5px;">
                            最后错误:
                        </div>
                        <div style="font-size: 13px; color: #856404;">
                            ${data.last_error}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载错误统计失败:', error);
        }
    }

    async loadOperationHistory() {
        try {
            const response = await fetch('/api/operation-history');
            const data = await response.json();

            const container = document.getElementById('operation-history-content');
            if (!container) return;

            if (!data.operations || data.operations.length === 0) {
                container.innerHTML = `
                    <div style="
                        text-align: center;
                        padding: 40px;
                        color: #999;
                    ">
                        暂无操作历史
                    </div>
                `;
                return;
            }

            container.innerHTML = data.operations.map(op => {
                const isSuccess = op.status === 'success';
                const icon = isSuccess ? '✅' : '❌';
                const bgColor = isSuccess ? '#e8f5e9' : '#ffebee';
                const borderColor = isSuccess ? '#4caf50' : '#f44336';
                const textColor = isSuccess ? '#2e7d32' : '#c62828';

                return `
                    <div style="
                        background: ${bgColor};
                        padding: 15px;
                        border-radius: 8px;
                        border-left: 4px solid ${borderColor};
                        margin-bottom: 10px;
                    ">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 20px;">${icon}</span>
                                <span style="font-weight: 600; color: ${textColor};">
                                    ${op.operation || '未知操作'}
                                </span>
                            </div>
                            <span style="font-size: 12px; color: #666;">
                                ${op.timestamp || ''}
                            </span>
                        </div>
                        ${op.message ? `
                            <div style="font-size: 13px; color: #666; margin-left: 30px;">
                                ${op.message}
                            </div>
                        ` : ''}
                        ${!isSuccess && op.error ? `
                            <div style="font-size: 12px; color: ${textColor}; margin-left: 30px; margin-top: 5px;">
                                错误: ${op.error}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('加载操作历史失败:', error);
        }
    }
}

// 全局实例
window.errorStatsPanel = new ErrorStatsPanel();

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorStatsPanel;
}
