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

# Check if certificate already exists
echo "🔍 Checking for existing certificate..."
if sudo certbot certificates 2>/dev/null | grep -q "$DOMAIN_NAME"; then
    echo "✅ Certificate already exists for $DOMAIN_NAME"
    echo "📜 Certificate details:"
    sudo certbot certificates | grep -A 5 "$DOMAIN_NAME"
    echo "⏭️  Skipping certificate request"
else
    # Obtain SSL certificate
    echo "📜 Obtaining SSL certificate from Let's Encrypt..."
    EMAIL=${EMAIL:-"admin@$DOMAIN_NAME"}
    sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $EMAIL
    echo "✅ New SSL certificate obtained successfully!"
fi

echo "✅ SSL certificates configured successfully!"
echo "🔗 Your application is now available at: https://$DOMAIN_NAME"
echo "📝 Next steps:"
echo "   1. Start the backend service: sudo systemctl start locallifeassistant-backend"
echo "   2. Test your application at https://$DOMAIN_NAME"
echo "   3. Configure Cloudflare DNS if needed"
