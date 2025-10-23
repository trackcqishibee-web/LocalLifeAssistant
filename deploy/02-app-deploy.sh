#!/bin/bash

# Application Deployment Script for Local Life Assistant
# Run this script after setup.sh

set -e

echo "🚀 Deploying Local Life Assistant application..."

# Navigate to application directory
cd /opt/locallifeassistant

# Clone or update repository
echo "📥 Cloning/updating repository..."
if [ -d ".git" ]; then
    echo "📦 Repository already exists, pulling latest changes..."
    sudo -u appuser git fetch origin
    sudo -u appuser git reset --hard origin/main
    sudo -u appuser git clean -fd
else
    echo "📥 Cloning repository..."
    sudo -u appuser git clone https://github.com/wjshku/LocalLifeAssistant.git .
fi

# Set up backend
echo "🐍 Setting up backend..."
cd backend

# Create or recreate virtual environment if needed
if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then
    echo "🐍 Creating Python virtual environment..."
    sudo -u appuser python3.11 -m venv venv
else
    echo "🐍 Virtual environment already exists, skipping creation..."
fi

echo "📦 Installing/updating Python dependencies..."
sudo -u appuser ./venv/bin/pip install --upgrade pip
sudo -u appuser ./venv/bin/pip install -r requirements.txt

# Set up frontend
echo "📦 Setting up frontend..."
cd ../frontend

# Clean previous build if exists
if [ -d "node_modules" ]; then
    echo "🧹 Cleaning previous node_modules..."
    sudo -u appuser rm -rf node_modules
fi

if [ -d "dist" ] || [ -d "build" ]; then
    echo "🧹 Cleaning previous build..."
    sudo -u appuser rm -rf dist build
fi

echo "📦 Installing Node.js dependencies..."
sudo -u appuser npm install
echo "🔨 Building frontend..."
sudo -u appuser npm run build

# Environment file will be created by configure_environment() function
echo "📝 Environment file will be created automatically in the next step"

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
EnvironmentFile=/opt/locallifeassistant/.env
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
echo "📝 Next steps (automated in auto-deploy.sh):"
echo "   1. Environment variables will be configured automatically"
echo "   2. Nginx will be configured"
echo "   3. SSL certificates will be set up"
echo "   4. Services will be started automatically"
