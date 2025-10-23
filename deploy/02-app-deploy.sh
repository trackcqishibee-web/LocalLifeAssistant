#!/bin/bash

# Application Deployment Script for Local Life Assistant
# Run this script after setup.sh

set -e

echo "🚀 Deploying Local Life Assistant application..."

# Navigate to application directory
cd /opt/locallifeassistant

# Clone or update repository (handle repo changes and preserve venv)
echo "📥 Cloning/updating repository..."
if [ -d ".git" ]; then
    # Check if remote URL matches
    CURRENT_REPO=$(sudo -u appuser git remote get-url origin)
    EXPECTED_REPO="https://github.com/${GITHUB_REPO}.git"
    
    if [ "$CURRENT_REPO" = "$EXPECTED_REPO" ]; then
        # Same repo, update it
        echo "ℹ️  Repository exists, updating..."
        sudo -u appuser git fetch origin
        sudo -u appuser git reset --hard origin/main
        echo "✅ Repository updated"
    else
        # Different repo, clean code but preserve venv
        echo "ℹ️  Repository URL changed, cleaning and re-cloning..."
        sudo -u appuser find . -maxdepth 1 -type f -delete
        sudo -u appuser find . -maxdepth 1 -type d ! -name "." ! -name "venv" ! -name "__pycache__" -exec rm -rf {} +
        sudo -u appuser git clone https://github.com/${GITHUB_REPO}.git .
        echo "✅ Repository cloned"
    fi
else
    # No repository, clone it
    echo "ℹ️  No repository found, cloning..."
    sudo -u appuser git clone https://github.com/${GITHUB_REPO}.git .
    echo "✅ Repository cloned"
fi

# Ensure we're on main branch
sudo -u appuser git checkout main

# Set up backend
echo "🐍 Setting up backend..."
cd backend
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    sudo -u appuser python3.11 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
sudo -u appuser ./venv/bin/pip install --upgrade pip
sudo -u appuser ./venv/bin/pip install -r requirements.txt

# Set up frontend
echo "📦 Setting up frontend..."
cd ../frontend
sudo -u appuser npm install
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
