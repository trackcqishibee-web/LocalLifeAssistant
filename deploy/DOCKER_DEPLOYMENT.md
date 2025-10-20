# 🐳 Docker Deployment Guide for Local Life Assistant

This guide will help you deploy your Local Life Assistant using Docker on DigitalOcean with Cloudflare DNS.

## 🚀 Quick Start

### Prerequisites
- DigitalOcean account
- Cloudflare account with a domain
- Your OpenAI API key

### One-Command Deployment
```bash
# On your DigitalOcean droplet
wget https://raw.githubusercontent.com/LijieTu/LocalLifeAssistant/main/deploy/docker-setup.sh
chmod +x docker-setup.sh
./docker-setup.sh
```

## 📋 Step-by-Step Deployment

### 1. Create DigitalOcean Droplet

1. **Create a new droplet:**
   - **Image:** Ubuntu 22.04 (LTS) x64
   - **Size:** Basic plan, $6/month (1GB RAM, 1 CPU, 25GB SSD)
   - **Datacenter:** Choose closest to your users
   - **Authentication:** SSH key (recommended)

2. **Note the IP address** of your droplet

### 2. Connect and Setup

```bash
# Connect to your droplet
ssh root@YOUR_DROPLET_IP

# Run the Docker setup script
wget https://raw.githubusercontent.com/LijieTu/LocalLifeAssistant/main/deploy/docker-setup.sh
chmod +x docker-setup.sh
./docker-setup.sh
```

### 3. Configure Environment Variables

```bash
# Edit the environment file
nano /opt/locallifeassistant/.env
```

Add your production values:
```env
OPENAI_API_KEY=your_actual_openai_api_key
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 4. Start the Application

```bash
cd /opt/locallifeassistant
docker-compose up -d
```

### 5. Verify Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test the API
curl http://localhost:8000/health
```

## 🌐 Configure Cloudflare DNS

### 1. Add Domain to Cloudflare
- Log into Cloudflare dashboard
- Add your domain
- Update nameservers at your domain registrar

### 2. Configure DNS Records
- **A Record:** `@` → `YOUR_DROPLET_IP`
- **A Record:** `www` → `YOUR_DROPLET_IP`
- **Proxy Status:** Proxied (orange cloud)

### 3. Configure SSL (Optional)
```bash
# Install Certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Update docker-compose.yml to use SSL
# (See SSL configuration section below)
```

## 🔧 Management Commands

Use the management script for easy operations:

```bash
cd /opt/locallifeassistant/deploy
chmod +x docker-manage.sh

# Start services
./docker-manage.sh start

# Stop services
./docker-manage.sh stop

# View logs
./docker-manage.sh logs

# Check status
./docker-manage.sh status

# Update application
./docker-manage.sh update

# Backup data
./docker-manage.sh backup
```

## 🔒 SSL Configuration

### Option 1: Cloudflare SSL (Recommended)
- Enable SSL/TLS encryption mode: "Full (strict)"
- Cloudflare handles SSL termination
- No additional configuration needed

### Option 2: Let's Encrypt SSL
```bash
# Install Certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Update docker-compose.yml to mount certificates
# Add volume: - /etc/letsencrypt:/etc/letsencrypt:ro
```

## 📊 Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Monitor Resources
```bash
# Docker stats
docker stats

# System resources
htop
```

### Health Checks
- **Backend:** `http://your-domain.com:8000/health`
- **Frontend:** `http://your-domain.com`

## 🔄 Updates and Maintenance

### Update Application
```bash
cd /opt/locallifeassistant
git pull
docker-compose build
docker-compose up -d
```

### Backup Data
```bash
# Create backup
./docker-manage.sh backup

# Restore from backup
./docker-manage.sh restore chroma_backup_20240101_120000.tar.gz
```

### Scale Services
```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3
```

## 🛡️ Security Best Practices

### 1. Environment Variables
- Never commit `.env` files to git
- Use strong, unique API keys
- Rotate keys regularly

### 2. Firewall Configuration
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 🆘 Troubleshooting

### Common Issues

1. **Services won't start:**
   ```bash
   docker-compose logs
   docker-compose ps
   ```

2. **Out of memory:**
   ```bash
   # Check memory usage
   free -h
   docker stats
   
   # Consider upgrading droplet size
   ```

3. **API not responding:**
   ```bash
   # Check backend logs
   docker-compose logs backend
   
   # Test API directly
   curl http://localhost:8000/health
   ```

4. **Frontend not loading:**
   ```bash
   # Check frontend logs
   docker-compose logs frontend
   
   # Verify nginx configuration
   docker exec locallifeassistant-frontend nginx -t
   ```

### Performance Optimization

1. **Enable Docker BuildKit:**
   ```bash
   export DOCKER_BUILDKIT=1
   ```

2. **Use multi-stage builds** (already configured)

3. **Optimize image layers** (already configured)

## 📈 Scaling and Production

### Production Considerations

1. **Use a reverse proxy** (Nginx/Traefik)
2. **Set up monitoring** (Prometheus/Grafana)
3. **Configure log aggregation** (ELK Stack)
4. **Use container orchestration** (Docker Swarm/Kubernetes)

### Load Balancing
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Use Nginx for load balancing
# (See nginx-proxy.conf configuration)
```

## 🎉 Success!

Your Local Life Assistant is now running on DigitalOcean with Docker!

- **Frontend:** `https://your-domain.com`
- **Backend API:** `https://your-domain.com:8000`
- **Health Check:** `https://your-domain.com:8000/health`

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify service status: `docker-compose ps`
3. Test individual components
4. Check DigitalOcean and Cloudflare dashboards

---

**🐳 Docker makes deployment easy, reliable, and scalable!**
