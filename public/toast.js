/**
 * Toast通知系统 (v1.8.0)
 * 轻量级、无依赖的通知组件
 */

class ToastNotification {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // 创建容器
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // 图标映射
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        // 颜色映射
        const colors = {
            success: { bg: '#e8f5e9', border: '#4caf50', text: '#2e7d32' },
            error: { bg: '#ffebee', border: '#f44336', text: '#c62828' },
            warning: { bg: '#fff3e0', border: '#ff9800', text: '#e65100' },
            info: { bg: '#e3f2fd', border: '#2196f3', text: '#1565c0' }
        };

        const color = colors[type] || colors.info;

        toast.style.cssText = `
            background: ${color.bg};
            border-left: 4px solid ${color.border};
            color: ${color.text};
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        `;

        toast.innerHTML = `
            <span style="font-size: 20px;">${icons[type]}</span>
            <span style="flex: 1; font-size: 14px; font-weight: 500;">${message}</span>
            <span style="font-size: 18px; opacity: 0.5;">×</span>
        `;

        // 添加动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
            .toast:hover {
                transform: translateX(-5px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
            }
        `;
        if (!document.getElementById('toast-styles')) {
            style.id = 'toast-styles';
            document.head.appendChild(style);
        }

        // 点击关闭
        toast.addEventListener('click', () => {
            this.remove(toast);
        });

        // 添加到容器
        this.container.appendChild(toast);

        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }

        return toast;
    }

    remove(toast) {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    // 从错误对象创建友好提示
    showError(error, operation = '操作') {
        let message = `${operation}失败`;
        
        if (error && error.message) {
            const errorMsg = error.message.toLowerCase();
            
            // 网络错误
            if (errorMsg.includes('timeout') || errorMsg.includes('connection')) {
                message = '网络连接超时，请检查网络后重试';
            }
            // Cookie错误
            else if (errorMsg.includes('401') || errorMsg.includes('unauthorized')) {
                message = 'Cookie已过期，请重新登录';
            }
            // 权限错误
            else if (errorMsg.includes('403') || errorMsg.includes('permission')) {
                message = '没有权限执行此操作';
            }
            // 限流错误
            else if (errorMsg.includes('429') || errorMsg.includes('too many')) {
                message = '请求过于频繁，请稍后再试';
            }
            // 服务器错误
            else if (errorMsg.includes('500') || errorMsg.includes('502') || errorMsg.includes('503')) {
                message = '服务器暂时不可用，请稍后重试';
            }
            // 其他错误
            else {
                message = `${operation}失败: ${error.message}`;
            }
        }
        
        return this.error(message);
    }
}

// 全局实例
window.toast = new ToastNotification();

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastNotification;
}
