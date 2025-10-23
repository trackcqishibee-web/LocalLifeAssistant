#!/bin/bash

# Application Deployment Script for Local Life Assistant
# Run this script after setup.sh

set -e

echo "🚀 Deploying Local Life Assistant application..."

# Navigate to application directory
cd /opt/locallifeassistant

# Clone repository (replace with your actual repository URL)
echo "📥 Cloning repository..."
sudo -u appuser git clone https://github.com/LijieTu/LocalLifeAssistant.git .

# Switch to main branch
sudo -u appuser git checkout main

# Set up backend
echo "🐍 Setting up backend..."
cd backend
sudo -u appuser python3.11 -m venv venv
sudo -u appuser ./venv/bin/pip install --upgrade pip
sudo -u appuser ./venv/bin/pip install -r requirements.txt

# Set up frontend
echo "📦 Setting up frontend..."
cd ../frontend
sudo -u appuser npm install
sudo -u appuser npm run build

# Create production environment file
echo "🔐 Creating production environment file..."
cd ..
sudo -u appuser cp .env.example .env.production

# Auto-configure environment variables if available
if [ -n "$OPENAI_API_KEY" ]; then
    echo "🔑 Setting OpenAI API key..."
    sudo -u appuser sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|" .env.production
fi

if [ -n "$DOMAIN_NAME" ]; then
    echo "🌐 Setting domain name..."
    sudo -u appuser sed -i "s|DOMAIN_NAME=.*|DOMAIN_NAME=$DOMAIN_NAME|" .env.production
fi

echo "📝 Production environment configured!"
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Please edit /opt/locallifeassistant/.env.production manually."
fi

# Create systemd service for backend
echo "⚙️ Creating systemd service for backend..."
sudo tee /etc/systemd/system/locallifeassistant-backend.service > /dev/null <<EOF
[Unit]
Description=Local Life Assistant Backend
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/locallifeassistant/backend
Environment=PATH=/opt/locallifeassistant/backend/venv/bin
EnvironmentFile=/opt/locallifeassistant/.env.production
ExecStart=/opt/locallifeassistant/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start backend service
sudo systemctl daemon-reload
sudo systemctl enable locallifeassistant-backend

echo "✅ Application deployment complete!"
echo "📝 Next steps:"
echo "   1. Configure Nginx (run configure-nginx.sh)"
echo "   2. Set up SSL certificates (run setup-ssl.sh)"
echo "   3. Start the backend service: sudo systemctl start locallifeassistant-backend"
echo ""
echo "🔧 Environment configuration:"
echo "   - .env.production created with auto-configured values"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   - ✅ OPENAI_API_KEY: Configured"
else
    echo "   - ❌ OPENAI_API_KEY: Not set (needs manual configuration)"
fi
if [ -n "$DOMAIN_NAME" ]; then
    echo "   - ✅ DOMAIN_NAME: $DOMAIN_NAME"
else
    echo "   - ❌ DOMAIN_NAME: Not set"
fi
