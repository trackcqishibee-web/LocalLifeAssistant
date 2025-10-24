#!/bin/bash

# Nginx Configuration Script for Local Life Assistant
# Run this script after deploy-app.sh

set -e

echo "🌐 Configuring Nginx..."

# Get domain name from command line argument or environment variable
DOMAIN_NAME=${1:-$DOMAIN_NAME}

if [ -z "$DOMAIN_NAME" ]; then
    # Fallback to interactive input for manual usage
    read -p "Enter your domain name (e.g., myapp.com): " DOMAIN_NAME

    if [ -z "$DOMAIN_NAME" ]; then
        echo "❌ Domain name is required!"
        exit 1
    fi
fi

echo "📝 Checking Nginx configuration..."

# Check if Nginx configuration already exists in /etc/nginx/sites-available/
if [ -f /etc/nginx/sites-available/locallifeassistant ]; then
    echo "✅ Nginx configuration already exists!"
    echo "ℹ️  Detected existing configuration at /etc/nginx/sites-available/locallifeassistant"
    echo "🛑 Skipping configuration setup to avoid overwriting existing settings"
    echo "📝 If you need to update the configuration:"
    echo "   1. Manually edit /etc/nginx/sites-available/locallifeassistant"
    echo "   2. Test with: sudo nginx -t"
    echo "   3. Reload with: sudo systemctl reload nginx"
    exit 0
fi

echo "ℹ️  No existing Nginx configuration found, proceeding with setup..."

echo "📝 Creating Nginx configuration for $DOMAIN_NAME..."

# Remove existing configuration if it exists
sudo rm -f /etc/nginx/sites-available/locallifeassistant
sudo rm -f /etc/nginx/sites-enabled/locallifeassistant

# Copy new configuration
sudo cp /opt/locallifeassistant/deploy/nginx.conf /etc/nginx/sites-available/locallifeassistant

# Replace placeholder domain in configuration
sudo sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/locallifeassistant

# Enable the site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/locallifeassistant /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Nginx configured successfully!"
    echo "📝 Next steps:"
    echo "   1. Update your DNS records to point to this server's IP"
    echo "   2. Run setup-ssl.sh to configure SSL certificates"
    echo "   3. Start the backend service: sudo systemctl start locallifeassistant-backend"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi
