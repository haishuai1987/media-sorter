#!/bin/bash
# 媒体库文件管理器 - Linux/NAS 安装脚本
# 支持: Ubuntu, Debian, CentOS, Synology, QNAP, TrueNAS等

set -e

echo "=========================================="
echo "  媒体库文件管理器 安装向导"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif [ -f /etc/synoinfo.conf ]; then
        OS="synology"
        VER=$(cat /etc/synoinfo.conf | grep buildnumber | cut -d'"' -f2)
    elif [ -f /etc/config/uLinux.conf ]; then
        OS="qnap"
        VER="unknown"
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    echo -e "${GREEN}检测到系统: $OS $VER${NC}"
}

# 检查Python版本
check_python() {
    echo ""
    echo "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 6 ]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION 已安装${NC}"
            PYTHON_CMD="python3"
            return 0
        else
            echo -e "${RED}✗ Python版本过低: $PYTHON_VERSION (需要 >= 3.6)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ 未找到Python 3${NC}"
        return 1
    fi
}

# 安装Python（如果需要）
install_python() {
    echo ""
    echo "尝试安装Python 3..."
    
    case $OS in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
            ;;
        centos|rhel|fedora)
            sudo yum install -y python3 python3-pip
            ;;
        synology)
            echo -e "${YELLOW}Synology系统请通过套件中心安装Python 3${NC}"
            echo "1. 打开套件中心"
            echo "2. 搜索 'Python 3'"
            echo "3. 安装 Python 3.x"
            return 1
            ;;
        qnap)
            echo -e "${YELLOW}QNAP系统请通过App Center安装Python 3${NC}"
            echo "1. 打开App Center"
            echo "2. 搜索 'Python'"
            echo "3. 安装 Python 3.x"
            return 1
            ;;
        *)
            echo -e "${RED}不支持的系统，请手动安装Python 3.6+${NC}"
            return 1
            ;;
    esac
}

# 检查端口占用
check_port() {
    PORT=8090
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$PORT "; then
            echo -e "${YELLOW}⚠ 端口 $PORT 已被占用${NC}"
            echo "请修改 app.py 中的 PORT 变量"
            return 1
        fi
    fi
    echo -e "${GREEN}✓ 端口 $PORT 可用${NC}"
    return 0
}

# 创建配置目录
create_config() {
    echo ""
    echo "创建配置目录..."
    
    CONFIG_DIR="$HOME/.media-renamer"
    mkdir -p "$CONFIG_DIR"
    
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        cat > "$CONFIG_DIR/config.json" << EOF
{
  "port": 8090,
  "scan_path": "",
  "movie_output": "",
  "tv_output": "",
  "network_delay": 1.0,
  "max_retries": 3
}
EOF
        echo -e "${GREEN}✓ 配置文件已创建: $CONFIG_DIR/config.json${NC}"
    else
        echo -e "${YELLOW}配置文件已存在，跳过${NC}"
    fi
}

# 设置权限
set_permissions() {
    echo ""
    echo "设置文件权限..."
    
    chmod +x app.py
    chmod 644 index.html
    
    echo -e "${GREEN}✓ 权限设置完成${NC}"
}

# 创建systemd服务（可选）
create_service() {
    echo ""
    read -p "是否创建systemd服务（开机自启）？[y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_DIR=$(pwd)
        SERVICE_FILE="/etc/systemd/system/media-renamer.service"
        
        echo "创建服务文件..."
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Media Renamer Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_CMD $INSTALL_DIR/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable media-renamer
        
        echo -e "${GREEN}✓ systemd服务已创建${NC}"
        echo "使用以下命令管理服务:"
        echo "  启动: sudo systemctl start media-renamer"
        echo "  停止: sudo systemctl stop media-renamer"
        echo "  状态: sudo systemctl status media-renamer"
        echo "  日志: sudo journalctl -u media-renamer -f"
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo "=========================================="
    echo "  安装完成！"
    echo "=========================================="
    echo ""
    echo "启动服务:"
    echo "  $PYTHON_CMD app.py"
    echo ""
    echo "访问地址:"
    echo "  本地: http://localhost:8090"
    echo "  局域网: http://$(hostname -I | awk '{print $1}'):8090"
    echo ""
    echo "配置文件:"
    echo "  $HOME/.media-renamer/config.json"
    echo ""
    echo "文档:"
    echo "  README.md - 使用说明"
    echo "  Linux_NAS优化方案.md - 优化说明"
    echo ""
}

# 主安装流程
main() {
    detect_os
    
    if ! check_python; then
        read -p "是否尝试安装Python 3？[y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! install_python; then
                echo -e "${RED}安装失败，请手动安装Python 3.6+${NC}"
                exit 1
            fi
            check_python
        else
            echo -e "${RED}需要Python 3.6+才能运行${NC}"
            exit 1
        fi
    fi
    
    check_port
    create_config
    set_permissions
    
    # 仅在支持systemd的系统上提供服务选项
    if command -v systemctl &> /dev/null && [ "$OS" != "synology" ] && [ "$OS" != "qnap" ]; then
        create_service
    fi
    
    show_usage
}

# 运行安装
main
