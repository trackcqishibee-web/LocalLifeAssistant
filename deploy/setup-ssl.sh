#!/bin/bash

# SSL Certificate Setup Script for Local Life Assistant
# Run this script after configure-nginx.sh

set -e

echo "🔒 Setting up SSL certificates..."

# Get domain name from Nginx configuration
DOMAIN_NAME=$(grep -o 'server_name [^;]*' /etc/nginx/sites-available/locallifeassistant | awk '{print $2}' | head -1)

if [ -z "$DOMAIN_NAME" ]; then
    echo "❌ Could not find domain name in Nginx configuration!"
    exit 1
fi

echo "🌐 Setting up SSL for domain: $DOMAIN_NAME"

# Obtain SSL certificate
echo "📜 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME

# Test certificate renewal
echo "🔄 Testing certificate renewal..."
sudo certbot renew --dry-run

# Set up automatic renewal
echo "⏰ Setting up automatic certificate renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "✅ SSL certificates configured successfully!"
echo "🔗 Your application is now available at: https://$DOMAIN_NAME"
echo "📝 Next steps:"
echo "   1. Start the backend service: sudo systemctl start locallifeassistant-backend"
echo "   2. Test your application at https://$DOMAIN_NAME"
echo "   3. Configure Cloudflare DNS if needed"
