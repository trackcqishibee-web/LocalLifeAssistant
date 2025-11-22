#!/bin/bash

# 🚀 Automated Deployment Script for Local Life Assistant
# Last updated: 2025-10-27 - EOF heredoc syntax fixed
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
DEPLOY_MODE=${DEPLOY_MODE:-"traditional"}

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

# Setup server
setup_server() {
    print_step "Setting up server..."
    chmod +x 01-server-setup.sh
    ./01-server-setup.sh
    print_success "Server setup completed"
}

# Configure environment variables
configure_environment() {
    print_step "Configuring environment variables..."

        # Since environment variables are already set globally by GitHub Actions,
        # we just need to create a .env file with the correct values for systemd
        ENV_FILE="/opt/locallifeassistant/.env"

        print_step "Creating .env file with global environment variables..."

        # Create .env file with actual values (no template needed since vars are global)
        # Remove old .env if exists to avoid permission issues
        sudo rm -f "$ENV_FILE"
        
        # Determine protocol based on whether domain is an IP address
        if [[ "$DOMAIN_NAME" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            API_PROTOCOL="http"
        else
            API_PROTOCOL="https"
        fi
        
        # Use tee to write as appuser (redirect happens inside sudo context)
        cat << EOF | sudo -u appuser tee "$ENV_FILE" > /dev/null
# OpenAI API Configuration
OPENAI_API_KEY=$OPENAI_API_KEY

# Event API Keys (optional - providers will handle missing keys gracefully)
TICKETMASTER_KEY=${TICKETMASTER_KEY:-}
EVENTBRITE_TOKEN=${EVENTBRITE_TOKEN:-}
MEETUP_TOKEN=${MEETUP_TOKEN:-}
ALLEVENTS_KEY=${ALLEVENTS_KEY:-}
SERPAPI_KEY=${SERPAPI_KEY:-}
PREDICTHQ_TOKEN=${PREDICTHQ_TOKEN:-}

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Frontend Configuration
VITE_API_BASE_URL=${API_PROTOCOL}://$DOMAIN_NAME

# Domain Configuration (for CORS auto-generation)
DOMAIN_NAME=$DOMAIN_NAME

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=/opt/locallifeassistant/backend/chroma_db

# Logging Configuration
LOG_LEVEL=INFO

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=$FIREBASE_CREDENTIALS_PATH
EOF

        print_success "Environment variables saved to .env file"

        # Setup Firebase credentials
        print_step "Setting up Firebase credentials..."

        # Check if source file exists
        if [ ! -f "/home/ubuntu/firebase-service-account.json" ]; then
            print_error "Firebase credentials not found at /home/ubuntu/firebase-service-account.json"
            exit 1
        fi

        # Ensure destination directory exists
        sudo mkdir -p "$(dirname "$FIREBASE_CREDENTIALS_PATH")"

        # Copy credentials
        sudo cp "/home/ubuntu/firebase-service-account.json" "$FIREBASE_CREDENTIALS_PATH"

        # Set correct permissions
        sudo chown appuser:appuser "$FIREBASE_CREDENTIALS_PATH"
        sudo chmod 600 "$FIREBASE_CREDENTIALS_PATH"

        # Verify appuser can read the file
        if sudo -u appuser test -r "$FIREBASE_CREDENTIALS_PATH"; then
            print_success "Firebase credentials copied and accessible by appuser"
        else
            print_error "appuser cannot read Firebase credentials"
            exit 1
        fi
        
        # Verify configuration
        if sudo -u appuser grep -q "OPENAI_API_KEY=sk-" "$ENV_FILE" 2>/dev/null; then
            print_success "OpenAI API key configured"
        else
            print_warning "OpenAI API key configuration may have issues"
        fi

        # Verify Firebase credentials path
        if sudo -u appuser grep -q "FIREBASE_CREDENTIALS_PATH=" "$ENV_FILE" 2>/dev/null; then
            print_success "Firebase credentials path configured"
        else
            print_warning "Firebase credentials path configuration may have issues"
        fi
}

# Deploy application
deploy_application() {
    print_step "Deploying application..."
    chmod +x 02-app-deploy.sh
    ./02-app-deploy.sh
    print_success "Application deployment completed"
}

# Configure web server
configure_web_server() {
    print_step "Configuring Nginx..."
    chmod +x 03-nginx-setup.sh
    ./03-nginx-setup.sh "$DOMAIN_NAME"
    print_success "Nginx configuration completed"
}

# Setup SSL certificates
setup_ssl_certificates() {
    print_step "Setting up SSL certificates..."
    chmod +x 04-ssl-setup.sh
    ./04-ssl-setup.sh
    print_success "SSL certificates configured"
}

# Start services
start_services() {
    print_step "Starting/restarting services..."
    sudo systemctl restart locallifeassistant-backend  # ✅ Works always
    sudo systemctl enable locallifeassistant-backend
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    print_success "Services started/restarted"
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
    echo "   Backend: http://localhost:8000"
    echo ""
    echo "🔧 Management Commands:"
    echo "   Backend status: sudo systemctl status locallifeassistant-backend"
    echo "   Backend logs: sudo journalctl -u locallifeassistant-backend -f"
    echo "   Nginx status: sudo systemctl status nginx"
    echo "   Restart backend: sudo systemctl restart locallifeassistant-backend"
    
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
    configure_environment   
    deploy_application  
    configure_web_server
    setup_ssl_certificates
    start_services
    health_check
    show_summary
}

# Run main function
main "$@"