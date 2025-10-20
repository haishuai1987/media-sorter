#!/bin/bash

# 媒体库文件管理器 - 云服务器一键部署脚本
# 适用于 Ubuntu 22.04 LTS / 20.04 LTS

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印标题
print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  媒体库文件管理器 - 云服务器部署${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "检测到 root 用户，建议使用普通用户 + sudo"
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统
check_system() {
    print_info "检查系统环境..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        print_success "系统: $OS $VER"
    else
        print_error "无法识别系统版本"
        exit 1
    fi
    
    # 检查是否为 Ubuntu
    if [[ ! "$OS" =~ "Ubuntu" ]]; then
        print_warning "此脚本针对 Ubuntu 优化，其他系统可能需要手动调整"
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 获取用户输入
get_user_input() {
    print_info "请输入配置信息..."
    echo ""
    
    # 域名
    read -p "请输入域名（如 media.example.com）: " DOMAIN
    if [ -z "$DOMAIN" ]; then
        print_error "域名不能为空"
        exit 1
    fi
    
    # 是否配置 SSL
    read -p "是否配置 SSL 证书？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ENABLE_SSL=true
        read -p "请输入邮箱（用于 Let's Encrypt）: " EMAIL
        if [ -z "$EMAIL" ]; then
            print_error "邮箱不能为空"
            exit 1
        fi
    else
        ENABLE_SSL=false
    fi
    
    # 安装目录
    read -p "安装目录（默认 /opt/media-renamer）: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-/opt/media-renamer}
    
    echo ""
    print_info "配置信息："
    echo "  域名: $DOMAIN"
    echo "  SSL: $ENABLE_SSL"
    [ "$ENABLE_SSL" = true ] && echo "  邮箱: $EMAIL"
    echo "  安装目录: $INSTALL_DIR"
    echo ""
    
    read -p "确认开始部署？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 0
    fi
}

# 更新系统
update_system() {
    print_info "更新系统软件包..."
    sudo apt update
    sudo apt upgrade -y
    print_success "系统更新完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装必要软件..."
    sudo apt install -y \
        python3 \
        python3-pip \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        curl \
        wget
    print_success "依赖安装完成"
}

# 克隆项目
clone_project() {
    print_info "克隆项目到 $INSTALL_DIR..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "目录已存在，是否删除并重新克隆？"
        read -p "(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -rf "$INSTALL_DIR"
        else
            print_info "跳过克隆步骤"
            return
        fi
    fi
    
    sudo mkdir -p "$(dirname "$INSTALL_DIR")"
    sudo git clone https://github.com/haishuai1987/media-sorter.git "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    
    print_success "项目克隆完成"
}

# 配置环境变量
configure_env() {
    print_info "配置环境变量..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# 部署环境
DEPLOY_ENV=cloud

# 监听配置
HOST=127.0.0.1
PORT=8000

# 调试模式
DEBUG=false
EOF
    
    print_success "环境变量配置完成"
}

# 配置 Nginx
configure_nginx() {
    print_info "配置 Nginx..."
    
    sudo tee /etc/nginx/sites-available/media-renamer > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 限制请求大小
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
EOF
    
    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/media-renamer /etc/nginx/sites-enabled/
    
    # 测试配置
    sudo nginx -t
    
    # 重启 Nginx
    sudo systemctl restart nginx
    
    print_success "Nginx 配置完成"
}

# 配置 SSL
configure_ssl() {
    if [ "$ENABLE_SSL" = true ]; then
        print_info "配置 SSL 证书..."
        
        sudo certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive --redirect
        
        # 设置自动续期
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        
        print_success "SSL 证书配置完成"
    else
        print_info "跳过 SSL 配置"
    fi
}

# 创建 Systemd 服务
create_systemd_service() {
    print_info "创建 Systemd 服务..."
    
    sudo tee /etc/systemd/system/media-renamer.service > /dev/null << EOF
[Unit]
Description=Media Renamer Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="DEPLOY_ENV=cloud"
Environment="HOST=127.0.0.1"
Environment="PORT=8000"
ExecStart=/usr/bin/python3 $INSTALL_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载 systemd
    sudo systemctl daemon-reload
    
    # 启用并启动服务
    sudo systemctl enable media-renamer
    sudo systemctl start media-renamer
    
    print_success "Systemd 服务创建完成"
}

# 配置防火墙
configure_firewall() {
    print_info "配置防火墙..."
    
    # 检查 UFW 是否安装
    if command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 22/tcp
        
        # 如果 UFW 未启用，询问是否启用
        if ! sudo ufw status | grep -q "Status: active"; then
            read -p "是否启用防火墙？(y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo ufw --force enable
            fi
        fi
        
        print_success "防火墙配置完成"
    else
        print_warning "UFW 未安装，跳过防火墙配置"
    fi
}

# 检查服务状态
check_service_status() {
    print_info "检查服务状态..."
    
    sleep 3
    
    if sudo systemctl is-active --quiet media-renamer; then
        print_success "服务运行正常"
        
        # 测试 HTTP 访问
        if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000 | grep -q "200"; then
            print_success "应用响应正常"
        else
            print_warning "应用可能未完全启动，请稍后检查"
        fi
    else
        print_error "服务启动失败"
        print_info "查看日志: sudo journalctl -u media-renamer -n 50"
        exit 1
    fi
}

# 打印完成信息
print_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [ "$ENABLE_SSL" = true ]; then
        echo -e "访问地址: ${BLUE}https://$DOMAIN${NC}"
    else
        echo -e "访问地址: ${BLUE}http://$DOMAIN${NC}"
    fi
    
    echo ""
    echo "常用命令:"
    echo "  查看服务状态: sudo systemctl status media-renamer"
    echo "  查看日志: sudo journalctl -u media-renamer -f"
    echo "  重启服务: sudo systemctl restart media-renamer"
    echo "  停止服务: sudo systemctl stop media-renamer"
    echo ""
    echo "配置文件位置:"
    echo "  应用目录: $INSTALL_DIR"
    echo "  Nginx 配置: /etc/nginx/sites-available/media-renamer"
    echo "  Systemd 服务: /etc/systemd/system/media-renamer.service"
    echo ""
    
    if [ "$ENABLE_SSL" = true ]; then
        echo "SSL 证书:"
        echo "  证书位置: /etc/letsencrypt/live/$DOMAIN/"
        echo "  自动续期: 已启用（certbot.timer）"
        echo ""
    fi
    
    echo -e "${YELLOW}下一步:${NC}"
    echo "  1. 访问应用并完成初始配置"
    echo "  2. 在设置中配置 TMDB API Key 和豆瓣 Cookie"
    echo "  3. 配置媒体库路径"
    echo ""
    echo -e "${GREEN}部署成功！享受自动化的媒体库管理体验！${NC}"
    echo ""
}

# 主函数
main() {
    print_header
    check_root
    check_system
    get_user_input
    
    echo ""
    print_info "开始部署..."
    echo ""
    
    update_system
    install_dependencies
    clone_project
    configure_env
    configure_nginx
    configure_ssl
    create_systemd_service
    configure_firewall
    check_service_status
    
    print_completion
}

# 运行主函数
main

