#!/bin/bash

# 🚀 Automated Deployment Script for Local Life Assistant
# GitHub Actions 友好的自动化部署脚本
# Usage: ./auto-deploy.sh

set -e  # Exit on any error

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

# Configuration from environment variables
DOMAIN_NAME=${DOMAIN_NAME:-"your-domain.com"}
GITHUB_REPO=${GITHUB_REPO:-"wjshku/LocalLifeAssistant"}
GITHUB_BRANCH=${GITHUB_BRANCH:-"main"}
OPENAI_API_KEY=${OPENAI_API_KEY}
EMAIL=${EMAIL:-"admin@$DOMAIN_NAME"}
DEPLOY_MODE=${DEPLOY_MODE:-"traditional"}  # traditional or docker

print_step "🚀 Starting automated deployment..."
echo "📝 Configuration:"
echo "   Domain: $DOMAIN_NAME"
echo "   Repo: $GITHUB_REPO"
echo "   Branch: $GITHUB_BRANCH"
echo "   Mode: $DEPLOY_MODE"
echo "   Email: $EMAIL"

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please don't run this script as root. Run as a regular user with sudo access."
        exit 1
    fi
    
    # Check required environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY environment variable is required!"
        exit 1
    fi
    
    # Check if domain is configured
    if [ "$DOMAIN_NAME" = "your-domain.com" ]; then
        print_warning "Please set DOMAIN_NAME environment variable to your actual domain"
        print_warning "Example: export DOMAIN_NAME=myapp.com"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup server (traditional deployment)
setup_server() {
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        print_step "Setting up server (traditional mode)..."
        chmod +x 01-server-setup.sh
        ./01-server-setup.sh
        print_success "Server setup completed"
    fi
}

# Deploy application
deploy_application() {
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        print_step "Deploying application (traditional mode)..."
        chmod +x 02-app-deploy.sh
        ./02-app-deploy.sh
        print_success "Application deployment completed"
    elif [ "$DEPLOY_MODE" = "docker" ]; then
        print_step "Deploying application (Docker mode)..."
        chmod +x docker/docker-deploy.sh
        ./docker/docker-deploy.sh
        print_success "Docker deployment completed"
    fi
}

# Configure web server
configure_web_server() {
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        print_step "Configuring Nginx..."
        chmod +x 03-nginx-setup.sh
        echo "$DOMAIN_NAME" | ./03-nginx-setup.sh
        print_success "Nginx configuration completed"
    fi
}

# Setup SSL certificates
setup_ssl_certificates() {
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        print_step "Setting up SSL certificates..."
        chmod +x 04-ssl-setup.sh
        echo "$DOMAIN_NAME" | ./04-ssl-setup.sh
        print_success "SSL certificates configured"
    fi
}

# Start services
start_services() {
    print_step "Starting services..."
    
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        sudo systemctl start locallifeassistant-backend
        sudo systemctl enable locallifeassistant-backend
        sudo systemctl start nginx
        sudo systemctl enable nginx
        print_success "Traditional services started"
    elif [ "$DEPLOY_MODE" = "docker" ]; then
        cd /opt/locallifeassistant
        docker-compose up -d
        print_success "Docker services started"
    fi
}

# Health check
health_check() {
    print_step "Performing health check..."
    
    # Wait for services to start
    sleep 10
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed"
    fi
    
    # Check Nginx
    if sudo systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_warning "Nginx is not running"
    fi
}

# Show deployment summary
show_summary() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📝 Deployment Summary:"
    echo "   Domain: https://$DOMAIN_NAME"
    echo "   Mode: $DEPLOY_MODE"
    echo "   Backend: http://localhost:8000"
    echo ""
    echo "🔧 Management Commands:"
    
    if [ "$DEPLOY_MODE" = "traditional" ]; then
        echo "   Backend status: sudo systemctl status locallifeassistant-backend"
        echo "   Backend logs: sudo journalctl -u locallifeassistant-backend -f"
        echo "   Nginx status: sudo systemctl status nginx"
        echo "   Restart backend: sudo systemctl restart locallifeassistant-backend"
    elif [ "$DEPLOY_MODE" = "docker" ]; then
        echo "   Docker status: docker-compose ps"
        echo "   Docker logs: docker-compose logs -f"
        echo "   Restart services: docker-compose restart"
        echo "   Stop services: docker-compose down"
    fi
    
    echo ""
    echo "📊 Monitoring:"
    echo "   Health check: curl http://localhost:8000/health"
    echo "   SSL status: sudo certbot certificates"
    echo ""
    echo "🌐 Your application is now available at: https://$DOMAIN_NAME"
}

# Main deployment flow
main() {
    check_prerequisites
    setup_server
    deploy_application
    configure_web_server
    setup_ssl_certificates
    start_services
    health_check
    show_summary
}

# Run main function
main "$@"