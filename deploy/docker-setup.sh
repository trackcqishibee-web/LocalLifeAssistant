#!/bin/bash

# Docker Deployment Script for Local Life Assistant
# This script sets up Docker deployment on DigitalOcean

set -e

echo "🐳 Setting up Docker deployment for Local Life Assistant..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully!"
    echo "⚠️  Please log out and log back in for Docker group changes to take effect"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully!"
fi

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/locallifeassistant
sudo chown $USER:$USER /opt/locallifeassistant
cd /opt/locallifeassistant

# Clone repository
echo "📥 Cloning repository..."
git clone -b feature/llm-city-extraction https://github.com/LijieTu/LocalLifeAssistant.git .

# Create production environment file
echo "🔐 Setting up environment variables..."
cp deploy/env.docker.example .env

echo "📝 Please edit /opt/locallifeassistant/.env with your production API keys:"
echo "   - OPENAI_API_KEY=your_production_openai_key"
echo "   - ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com"

# Create logs directory
mkdir -p logs

echo "✅ Docker setup complete!"
echo "📝 Next steps:"
echo "   1. Edit /opt/locallifeassistant/.env with your API keys"
echo "   2. Run: cd /opt/locallifeassistant && docker-compose up -d"
echo "   3. Check logs: docker-compose logs -f"
