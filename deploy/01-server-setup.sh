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

# Create application user (robust, idempotent version)
echo "👤 Creating application user..."
# Temporarily disable exit on error for user creation
set +e
# Try to create user, capture exit code
sudo useradd -m -s /bin/bash appuser 2>/dev/null
USERADD_EXIT=$?
set -e

if [ $USERADD_EXIT -eq 0 ]; then
    # User was created successfully
    sudo usermod -aG sudo appuser
    echo "✅ Application user created and added to sudo group"
elif [ $USERADD_EXIT -eq 9 ]; then
    # User already exists (exit code 9)
    if ! getent group sudo | grep -q ":appuser\|,appuser"; then
        sudo usermod -aG sudo appuser
        echo "✅ Added existing user to sudo group"
    else
        echo "ℹ️  Application user already exists and is in sudo group"
    fi
else
    # Unexpected error
    echo "❌ Unexpected error creating user (exit code: $USERADD_EXIT)"
    echo "   Attempting to continue with existing user if available..."
    if getent passwd appuser > /dev/null 2>&1; then
        echo "ℹ️  Found existing appuser, continuing..."
    else
        echo "⚠️  No appuser found, some operations may fail"
    fi
fi

# Create application directory (force clean)
echo "📁 Creating application directory..."
# Remove existing directory if it exists
if [ -d "/opt/locallifeassistant" ]; then
    sudo rm -rf /opt/locallifeassistant
    echo "ℹ️  Removed existing application directory"
fi
# Create fresh directory
sudo mkdir -p /opt/locallifeassistant
sudo chown appuser:appuser /opt/locallifeassistant
echo "✅ Application directory created with correct ownership"

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
