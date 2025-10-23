#!/bin/bash

# DigitalOcean Droplet Setup Script for Local Life Assistant
# Run this script on a fresh Ubuntu 22.04 droplet

set -e

echo "🚀 Setting up Local Life Assistant on DigitalOcean..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18
echo "📦 Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install -y nginx

# Install Certbot for SSL
echo "🔒 Installing Certbot..."
sudo apt install -y certbot python3-certbot-nginx

# Install PM2 for process management
echo "⚙️ Installing PM2..."
sudo npm install -g pm2

# Check application user (skip creation)
echo "👤 Checking application user..."
if getent passwd appuser > /dev/null 2>&1; then
    # User exists, ensure they're in sudo group
    if ! getent group sudo | grep -q ":appuser\|,appuser"; then
        sudo usermod -aG sudo appuser
        echo "✅ Added existing user to sudo group"
    else
        echo "ℹ️  Application user exists and is in sudo group"
    fi
else
    echo "⚠️  Application user 'appuser' not found!"
    echo "   This may cause issues with subsequent deployment scripts."
    echo "   Please ensure appuser exists before running deployment scripts."
fi

# Create application directory
echo "📁 Creating application directory..."
if [ ! -d "/opt/locallifeassistant" ]; then
    sudo mkdir -p /opt/locallifeassistant
    echo "✅ Application directory created"
else
    echo "ℹ️  Application directory already exists"
fi
# Ensure correct ownership regardless
sudo chown appuser:appuser /opt/locallifeassistant
echo "✅ Application directory ownership set to appuser:appuser"

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
if sudo ufw status | grep -q "Status: inactive"; then
    sudo ufw --force enable
    echo "✅ Firewall enabled"
else
    echo "ℹ️  Firewall already enabled"
fi

echo "✅ Basic setup complete!"
echo "📝 Next steps:"
echo "   1. Clone your repository to /opt/locallifeassistant"
echo "   2. Set up environment variables"
echo "   3. Install application dependencies"
echo "   4. Configure Nginx"
echo "   5. Set up SSL certificates"
