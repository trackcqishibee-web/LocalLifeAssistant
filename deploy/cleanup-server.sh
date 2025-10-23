#!/bin/bash

# 🧹 Server Cleanup Script for Local Life Assistant
# 用于在重复部署前清理服务器状态
# 使用方法: ./cleanup-server.sh [options]
# 选项:
#   --all        完全清理（包括用户和应用目录）
#   --app        只清理应用文件和配置
#   --services   只停止和禁用服务
#   --help       显示帮助信息

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    echo "🧹 Local Life Assistant - 服务器清理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./cleanup-server.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --all        完全清理（包括用户和应用目录）"
    echo "  --app        只清理应用文件和配置（推荐）"
    echo "  --services   只停止和禁用服务"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./cleanup-server.sh --app     # 清理应用，保留用户"
    echo "  ./cleanup-server.sh --all     # 完全清理服务器"
    echo "  ./cleanup-server.sh --services # 只停止服务"
}

# Stop and disable services
cleanup_services() {
    print_step "停止和禁用服务..."

    # Stop backend service if running
    if sudo systemctl is-active --quiet locallifeassistant-backend 2>/dev/null; then
        print_step "停止后端服务..."
        sudo systemctl stop locallifeassistant-backend
        print_success "后端服务已停止"
    else
        echo "ℹ️  后端服务未运行"
    fi

    # Stop nginx if running
    if sudo systemctl is-active --quiet nginx 2>/dev/null; then
        print_step "停止 Nginx 服务..."
        sudo systemctl stop nginx
        print_success "Nginx 服务已停止"
    else
        echo "ℹ️  Nginx 服务未运行"
    fi

    # Disable services
    if sudo systemctl is-enabled locallifeassistant-backend 2>/dev/null; then
        sudo systemctl disable locallifeassistant-backend
        print_success "后端服务已禁用开机自启"
    fi

    if sudo systemctl is-enabled nginx 2>/dev/null; then
        sudo systemctl disable nginx
        print_success "Nginx 服务已禁用开机自启"
    fi
}

# Remove systemd service files
remove_service_files() {
    print_step "删除服务文件..."

    if [ -f "/etc/systemd/system/locallifeassistant-backend.service" ]; then
        sudo rm -f /etc/systemd/system/locallifeassistant-backend.service
        print_success "后端服务文件已删除"
    fi

    # Reload systemd daemon
    sudo systemctl daemon-reload
    print_success "systemd 配置已重新加载"
}

# Remove Nginx configuration
cleanup_nginx() {
    print_step "清理 Nginx 配置..."

    # Remove site configuration
    if [ -L "/etc/nginx/sites-enabled/locallifeassistant" ]; then
        sudo rm -f /etc/nginx/sites-enabled/locallifeassistant
        print_success "Nginx 站点配置已删除"
    fi

    if [ -f "/etc/nginx/sites-available/locallifeassistant" ]; then
        sudo rm -f /etc/nginx/sites-available/locallifeassistant
        print_success "Nginx 可用站点配置已删除"
    fi

    # Remove SSL certificates if they exist
    if [ -d "/etc/letsencrypt/live/$DOMAIN_NAME" ]; then
        print_warning "发现 SSL 证书，保留以避免重新申请"
        echo "   如需删除，请手动运行: sudo certbot delete --cert-name $DOMAIN_NAME"
    fi
}

# Remove application files
cleanup_application() {
    print_step "清理应用文件..."

    if [ -d "/opt/locallifeassistant" ]; then
        sudo rm -rf /opt/locallifeassistant
        print_success "应用目录已删除"
    fi
}

# Remove application user
cleanup_user() {
    print_step "清理应用用户..."

    if id -u appuser > /dev/null 2>&1; then
        # Check if user owns any processes
        if pgrep -u appuser > /dev/null 2>&1; then
            print_warning "appuser 还有运行中的进程，正在终止..."
            sudo pkill -u appuser
            sleep 2
        fi

        sudo userdel -r appuser 2>/dev/null || true
        print_success "应用用户已删除"
    else
        echo "ℹ️  应用用户不存在"
    fi
}

# Main cleanup functions
cleanup_app_only() {
    print_warning "开始应用级清理（保留用户和系统配置）..."
    cleanup_services
    remove_service_files
    cleanup_nginx
    cleanup_application
    print_success "应用级清理完成！"
}

cleanup_all() {
    print_warning "开始完全清理（包括用户和所有配置）..."
    print_error "⚠️  这将删除所有应用数据和用户！"
    read -p "确定要继续吗？输入 'yes' 确认: " confirm
    if [ "$confirm" != "yes" ]; then
        print_error "操作已取消"
        exit 1
    fi

    cleanup_services
    remove_service_files
    cleanup_nginx
    cleanup_application
    cleanup_user
    print_success "完全清理完成！"
}

cleanup_services_only() {
    print_warning "开始服务级清理（只停止服务）..."
    cleanup_services
    print_success "服务级清理完成！"
}

# Get domain name for SSL cleanup
DOMAIN_NAME=${DOMAIN_NAME:-"your-domain.com"}

# Main logic
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --all)
        cleanup_all
        ;;
    --app)
        cleanup_app_only
        ;;
    --services)
        cleanup_services_only
        ;;
    *)
        echo "❌ 无效选项。请使用 --help 查看可用选项。"
        echo ""
        echo "常用选项:"
        echo "  --app      清理应用文件和配置（推荐用于重复部署）"
        echo "  --services  只停止服务（用于临时维护）"
        echo "  --all      完全清理（谨慎使用）"
        exit 1
        ;;
esac

print_success "清理操作完成！"
echo ""
echo "💡 下一步:"
if [ "$1" = "--services" ]; then
    echo "   重新部署应用: ./auto-deploy.sh"
else
    echo "   重新部署应用: ./auto-deploy.sh"
    echo "   或重新运行完整的部署流程"
fi
