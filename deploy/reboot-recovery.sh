#!/bin/bash

# 🚀 Local Life Assistant - 重启恢复脚本
# 用于服务器重启后恢复所有服务
# 使用方法: wget https://raw.githubusercontent.com/wjshku/LocalLifeAssistant/main/deploy/reboot-recovery.sh && chmod +x reboot-recovery.sh && ./reboot-recovery.sh

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

print_step "🔄 开始重启恢复流程..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_warning "建议不要以 root 用户运行此脚本"
    print_warning "请使用普通用户运行，或确认你知道自己在做什么"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to check service status
check_service() {
    local service_name=$1
    local display_name=$2

    if sudo systemctl is-active --quiet "$service_name"; then
        print_success "$display_name 服务正在运行"
        return 0
    else
        print_error "$display_name 服务未运行"
        return 1
    fi
}

# Function to start service
start_service() {
    local service_name=$1
    local display_name=$2

    print_step "启动 $display_name 服务..."
    if sudo systemctl start "$service_name"; then
        print_success "$display_name 服务启动成功"
        return 0
    else
        print_error "$display_name 服务启动失败"
        return 1
    fi
}

# Function to enable service
enable_service() {
    local service_name=$1
    local display_name=$2

    if sudo systemctl enable "$service_name" >/dev/null 2>&1; then
        print_success "$display_name 服务已设置为开机自启"
    else
        print_warning "$display_name 服务开机自启设置失败"
    fi
}

# Main recovery process
print_step "检查并启动后端服务..."
if ! check_service "locallifeassistant-backend" "Local Life Assistant 后端"; then
    if start_service "locallifeassistant-backend" "Local Life Assistant 后端"; then
        enable_service "locallifeassistant-backend" "Local Life Assistant 后端"
    fi
fi

echo ""

print_step "检查并启动 Nginx 服务..."
if ! check_service "nginx" "Nginx"; then
    if start_service "nginx" "Nginx"; then
        enable_service "nginx" "Nginx"
    fi
fi

echo ""

# Wait for services to fully start
print_step "等待服务完全启动..."
sleep 5

# Final status check
print_step "最终状态检查..."
echo ""

FAILED_SERVICES=()

if ! check_service "locallifeassistant-backend" "Local Life Assistant 后端"; then
    FAILED_SERVICES+=("locallifeassistant-backend")
fi

if ! check_service "nginx" "Nginx"; then
    FAILED_SERVICES+=("nginx")
fi

echo ""

# Health check
print_step "执行应用健康检查..."

# Get domain name from environment or default
DOMAIN_NAME=${DOMAIN_NAME:-"your-domain.com"}

BACKEND_HEALTHY=false
if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
    print_success "后端健康检查通过"
    BACKEND_HEALTHY=true
else
    print_error "后端健康检查失败"
fi

NGINX_ACCESSIBLE=false
if curl -f -s -I https://$DOMAIN_NAME >/dev/null 2>&1; then
    print_success "Nginx HTTPS 访问正常"
    NGINX_ACCESSIBLE=true
elif curl -f -s -I http://$DOMAIN_NAME >/dev/null 2>&1; then
    print_success "Nginx HTTP 访问正常"
    NGINX_ACCESSIBLE=true
else
    print_error "Nginx 访问检查失败"
fi

echo ""

# Summary
if [ ${#FAILED_SERVICES[@]} -eq 0 ] && [ "$BACKEND_HEALTHY" = true ] && [ "$NGINX_ACCESSIBLE" = true ]; then
    print_success "🎉 所有服务恢复成功！"
    echo ""
    echo "📊 服务状态摘要:"
    echo "   🌐 应用访问地址: https://$DOMAIN_NAME"
    echo "   🔗 后端 API: http://localhost:8000"
    echo "   💚 健康检查: curl http://localhost:8000/health"
    echo ""
    echo "🔧 管理命令:"
    echo "   后端状态: sudo systemctl status locallifeassistant-backend"
    echo "   后端日志: sudo journalctl -u locallifeassistant-backend -f"
    echo "   Nginx 状态: sudo systemctl status nginx"
    echo "   重启后端: sudo systemctl restart locallifeassistant-backend"
else
    print_error "⚠️  某些服务恢复失败"
    echo ""
    echo "❌ 失败的服务:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "   - $service"
    done
    if [ "$BACKEND_HEALTHY" = false ]; then
        echo "   - 后端健康检查失败"
    fi
    if [ "$NGINX_ACCESSIBLE" = false ]; then
        echo "   - Nginx 访问检查失败"
    fi
    echo ""
    echo "🔧 故障排除:"
    echo "   查看详细日志: sudo journalctl -u locallifeassistant-backend -f"
    echo "   检查 Nginx 配置: sudo nginx -t"
    echo "   重启服务: sudo systemctl restart locallifeassistant-backend"
    exit 1
fi

print_success "重启恢复流程完成！"
