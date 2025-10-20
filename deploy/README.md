# DigitalOcean + Cloudflare Deployment Guide

## 🚀 Complete Deployment Guide for Local Life Assistant

This guide will help you deploy your Local Life Assistant to DigitalOcean and configure it with a custom domain through Cloudflare.

## 📋 Prerequisites

- DigitalOcean account
- Cloudflare account
- Domain name (you can register one through Cloudflare or any domain registrar)
- Your OpenAI API key

## 🌊 Step 1: Create DigitalOcean Droplet

1. **Log into DigitalOcean** and create a new droplet
2. **Choose configuration:**
   - **Image:** Ubuntu 22.04 (LTS) x64
   - **Size:** Basic plan, $6/month (1GB RAM, 1 CPU, 25GB SSD) - minimum recommended
   - **Datacenter:** Choose closest to your users
   - **Authentication:** SSH key (recommended) or password
3. **Create droplet** and note the IP address

## 🔧 Step 2: Initial Server Setup

1. **Connect to your droplet:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. **Run the setup script:**
   ```bash
   # Download and run the setup script
   wget https://raw.githubusercontent.com/LijieTu/LocalLifeAssistant/main/deploy/setup.sh
   chmod +x setup.sh
   ./setup.sh
   ```

## 📦 Step 3: Deploy Application

1. **Clone your repository:**
   ```bash
   cd /opt/locallifeassistant
   git clone https://github.com/LijieTu/LocalLifeAssistant.git .
   ```

2. **Run the deployment script:**
   ```bash
   chmod +x deploy/deploy-app.sh
   ./deploy/deploy-app.sh
   ```

3. **Configure environment variables:**
   ```bash
   sudo nano /opt/locallifeassistant/.env.production
   ```
   
   Add your production API keys:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key
   CHROMA_PERSIST_DIRECTORY=/opt/locallifeassistant/backend/chroma_db
   ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
   ```

## 🌐 Step 4: Configure Domain with Cloudflare

1. **Add your domain to Cloudflare:**
   - Log into Cloudflare dashboard
   - Click "Add a Site"
   - Enter your domain name
   - Choose the free plan

2. **Update nameservers:**
   - Cloudflare will provide nameservers
   - Update your domain registrar with these nameservers
   - Wait for DNS propagation (can take up to 24 hours)

3. **Add DNS records:**
   - In Cloudflare dashboard, go to DNS
   - Add an A record:
     - **Type:** A
     - **Name:** @ (or your domain)
     - **IPv4 address:** Your DigitalOcean droplet IP
     - **Proxy status:** Proxied (orange cloud)

4. **Add www subdomain:**
   - Add another A record:
     - **Type:** A
     - **Name:** www
     - **IPv4 address:** Your DigitalOcean droplet IP
     - **Proxy status:** Proxied (orange cloud)

## ⚙️ Step 5: Configure Nginx

1. **Run the Nginx configuration script:**
   ```bash
   chmod +x deploy/configure-nginx.sh
   ./deploy/configure-nginx.sh
   ```
   
   Enter your domain name when prompted.

## 🔒 Step 6: Set Up SSL Certificates

1. **Run the SSL setup script:**
   ```bash
   chmod +x deploy/setup-ssl.sh
   ./deploy/setup-ssl.sh
   ```

2. **Verify SSL is working:**
   - Visit `https://your-domain.com`
   - Check that the lock icon appears in your browser

## 🚀 Step 7: Start Services

1. **Start the backend service:**
   ```bash
   sudo systemctl start locallifeassistant-backend
   sudo systemctl enable locallifeassistant-backend
   ```

2. **Check service status:**
   ```bash
   sudo systemctl status locallifeassistant-backend
   ```

## 🧪 Step 8: Test Your Deployment

1. **Visit your website:** `https://your-domain.com`
2. **Test the API:** `https://your-domain.com/api/health`
3. **Try the chat interface** and verify everything works

## 🔧 Management Commands

### Service Management
```bash
# Restart backend
sudo systemctl restart locallifeassistant-backend

# View logs
sudo journalctl -u locallifeassistant-backend -f

# Check status
sudo systemctl status locallifeassistant-backend
```

### Application Updates
```bash
# Update application
cd /opt/locallifeassistant
sudo -u appuser git pull
sudo systemctl restart locallifeassistant-backend
```

### SSL Certificate Management
```bash
# Check certificates
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

## 🛡️ Security Considerations

1. **Firewall:** UFW is configured to only allow SSH, HTTP, and HTTPS
2. **SSL:** Let's Encrypt certificates with automatic renewal
3. **Updates:** Regular system updates are recommended
4. **API Keys:** Store production API keys securely in `.env.production`

## 🆘 Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u locallifeassistant-backend -f
   ```

2. **Nginx errors:**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

3. **SSL certificate issues:**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

4. **DNS not resolving:**
   - Check Cloudflare DNS settings
   - Verify nameservers are correct
   - Wait for DNS propagation

### Logs Location
- **Application logs:** `sudo journalctl -u locallifeassistant-backend -f`
- **Nginx logs:** `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
- **System logs:** `/var/log/syslog`

## 📞 Support

If you encounter issues:
1. Check the logs using the commands above
2. Verify all services are running
3. Test individual components
4. Check Cloudflare and DigitalOcean dashboards for any issues

---

**🎉 Congratulations!** Your Local Life Assistant is now live and accessible via your custom domain!
