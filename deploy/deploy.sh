#!/bin/bash

# Complete Deployment Script for Local Life Assistant
# This script runs all deployment steps in sequence

set -e

echo "🚀 Starting complete deployment of Local Life Assistant..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. Run as a regular user with sudo access."
    exit 1
fi

# Step 1: Basic system setup
echo "📋 Step 1: Basic system setup..."
chmod +x deploy/setup.sh
./deploy/setup.sh

# Step 2: Deploy application
echo "📋 Step 2: Deploying application..."
chmod +x deploy/deploy-app.sh
./deploy/deploy-app.sh

# Step 3: Configure Nginx
echo "📋 Step 3: Configuring Nginx..."
chmod +x deploy/configure-nginx.sh
./deploy/configure-nginx.sh

# Step 4: Set up SSL
echo "📋 Step 4: Setting up SSL certificates..."
chmod +x deploy/setup-ssl.sh
./deploy/setup-ssl.sh

# Step 5: Start services
echo "📋 Step 5: Starting services..."
sudo systemctl start locallifeassistant-backend
sudo systemctl status locallifeassistant-backend --no-pager

echo "✅ Deployment complete!"
echo "🎉 Your Local Life Assistant is now running!"
echo ""
echo "📝 Important notes:"
echo "   - Backend service: sudo systemctl status locallifeassistant-backend"
echo "   - Nginx service: sudo systemctl status nginx"
echo "   - SSL certificates: sudo certbot certificates"
echo "   - Logs: sudo journalctl -u locallifeassistant-backend -f"
echo ""
echo "🔧 Management commands:"
echo "   - Restart backend: sudo systemctl restart locallifeassistant-backend"
echo "   - Restart Nginx: sudo systemctl restart nginx"
echo "   - View logs: sudo journalctl -u locallifeassistant-backend -f"
echo "   - Update app: cd /opt/locallifeassistant && sudo -u appuser git pull"
