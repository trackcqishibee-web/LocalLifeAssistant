# 🚀 AWS EC2 Deployment Guide

## ✅ What You Have

- **EC2 Instance**: `3.89.127.102`
- **SSH Access**: `ssh -i "locomock_key.pem" ubuntu@3.89.127.102`
- **Region**: `us-east-1`
- **GitHub Actions Workflow**: Ready to deploy automatically!

---

## 📋 Setup Steps

### Step 1: Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Required |
|------------|-------|----------|
| `AWS_EC2_SSH_KEY` | Contents of your `locomock_key.pem` file | ✅ Yes |
| `OPENAI_API_KEY` | Your OpenAI API key (starts with sk-...) | ✅ Yes |
| `DOMAIN_NAME` | Your custom domain (if any) | ⚠️ Optional |
| `ADMIN_EMAIL` | Your email for SSL certificates | ⚠️ Optional |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase credentials | ⚠️ Optional |

#### How to add the SSH Key:

1. Open your `locomock_key.pem` file in a text editor
2. Copy the **entire contents** (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
3. Paste into the `AWS_EC2_SSH_KEY` secret

```bash
# On your local machine:
cat locomock_key.pem
# Copy the output and paste as AWS_EC2_SSH_KEY secret
```

---

### Step 2: One-Time EC2 Instance Setup

SSH into your EC2 instance and run the initial setup:

```bash
# Connect to your EC2 instance
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# Once connected, run:
curl -o setup-ec2.sh https://raw.githubusercontent.com/YOUR_USERNAME/LocalLifeAssistant/main/deploy/setup-ec2.sh
chmod +x setup-ec2.sh
sudo ./setup-ec2.sh
```

Or manually install dependencies:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker

# Install Python and Node.js
sudo apt install -y python3 python3-pip nodejs npm nginx

# Install PM2 for process management
sudo npm install -g pm2

# Create application directory
sudo mkdir -p /opt/locallifeassistant
sudo chown ubuntu:ubuntu /opt/locallifeassistant

# Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # Backend API
sudo ufw --force enable
```

---

### Step 3: Configure AWS Security Group

In AWS Console → **EC2** → **Security Groups**, ensure your instance's security group allows:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | Your IP | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom TCP | 8000 | 0.0.0.0/0 | Backend API (optional, can restrict) |

---

### Step 4: Push to Deploy! 🚀

Once secrets are configured, simply push to your `main` branch:

```bash
git add .
git commit -m "Deploy to AWS EC2"
git push origin main
```

The GitHub Actions workflow will automatically:
1. ✅ Connect to your EC2 instance via SSH
2. ✅ Download the latest code
3. ✅ Install dependencies
4. ✅ Start backend and frontend services
5. ✅ Run health checks

---

## 🔄 Manual Deployment (Alternative)

If you want to deploy manually without GitHub Actions:

```bash
# 1. SSH into your EC2
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# 2. Clone or update repository
cd /opt/locallifeassistant
git clone https://github.com/YOUR_USERNAME/LocalLifeAssistant.git .
# Or if already cloned:
git pull origin main

# 3. Set up environment variables
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
FIREBASE_CREDENTIALS_PATH=/home/ubuntu/firebase-service-account.json
PORT=8000
HOST=0.0.0.0
VITE_API_BASE_URL=http://3.89.127.102:8000
DOMAIN_NAME=3.89.127.102
EOF

# 4. Install backend dependencies
cd backend
python3 -m pip install -r requirements.txt

# 5. Install frontend dependencies
cd ../frontend
npm install

# 6. Build frontend
npm run build

# 7. Start backend with PM2
cd ../backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name backend

# 8. Serve frontend with Nginx
sudo cp ../deploy/nginx.conf /etc/nginx/sites-available/locallifeassistant
sudo ln -sf /etc/nginx/sites-available/locallifeassistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 9. Save PM2 configuration
pm2 save
pm2 startup
```

---

## 🐳 Docker Deployment (Recommended)

For a cleaner deployment using Docker:

```bash
# 1. SSH into EC2
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# 2. Navigate to project
cd /opt/locallifeassistant

# 3. Create .env file
nano .env
# Add your environment variables

# 4. Deploy with Docker Compose
cd deploy/docker
docker-compose up -d --build

# 5. Check status
docker-compose ps
docker-compose logs -f
```

---

## 🌐 Custom Domain Setup (Optional)

If you want to use a custom domain instead of the EC2 public DNS:

### 1. Get Elastic IP (Recommended)
```bash
# In AWS Console:
# EC2 → Elastic IPs → Allocate Elastic IP address
# Then associate it with your EC2 instance
```

### 2. Configure DNS
Point your domain's A record to your Elastic IP or EC2 public IP:
```
A    @    3.89.127.102
A    www  3.89.127.102
```

### 3. Install SSL Certificate
```bash
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 4. Update GitHub Secrets
Add `DOMAIN_NAME` secret with your domain in GitHub repository settings.

---

## 📊 Monitoring Your Deployment

### Check Service Status
```bash
# Check backend
curl http://3.89.127.102:8000/health

# Check if services are running
pm2 status
# or for Docker:
docker-compose ps
```

### View Logs
```bash
# PM2 logs
pm2 logs backend

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# PM2
pm2 restart backend

# Docker
docker-compose restart

# Nginx
sudo systemctl restart nginx
```

---

## 🆘 Troubleshooting

### Issue: Can't connect to EC2
- Check security group allows your IP on port 22
- Verify key file permissions: `chmod 400 locomock_key.pem`
- Try: `ssh -v -i "locomock_key.pem" ubuntu@3.89.127.102`

### Issue: Port already in use
```bash
# Find process using port 8000
sudo lsof -i :8000
# Kill it
sudo kill -9 <PID>
```

### Issue: GitHub Actions deployment fails
- Verify all secrets are set correctly
- Check workflow logs in GitHub Actions tab
- Ensure EC2 security group allows SSH from GitHub Actions IPs

### Issue: Application not accessible
```bash
# Check if backend is running
curl localhost:8000/health

# Check Nginx status
sudo systemctl status nginx

# Check security group allows ports 80 and 443
```

---

## 💡 Best Practices

1. **Use Elastic IP**: Prevents IP changes when instance restarts
2. **Enable Backups**: Use EBS snapshots or AMI backups
3. **Monitor Costs**: Set up AWS billing alerts
4. **Use CloudWatch**: Monitor instance metrics
5. **Keep Updated**: Regularly update system packages
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
6. **Use Docker**: Easier to manage and deploy

---

## 🔐 Security Checklist

- [ ] EC2 security group properly configured
- [ ] SSH key file has correct permissions (400)
- [ ] Firewall (UFW) enabled and configured
- [ ] SSL certificate installed (if using custom domain)
- [ ] Environment variables stored securely (not in code)
- [ ] Regular security updates applied
- [ ] Backup strategy in place

---

## 📞 Quick Commands Reference

```bash
# Connect to EC2
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# View backend logs
pm2 logs backend

# Restart services
pm2 restart backend
sudo systemctl restart nginx

# Check health
curl http://localhost:8000/health

# Pull latest code
cd /opt/locallifeassistant && git pull origin main

# Redeploy with Docker
cd /opt/locallifeassistant/deploy/docker
docker-compose down
docker-compose up -d --build
```

---

## 🎉 Success!

Once deployed, your application will be available at:
- **Frontend**: http://3.89.127.102
- **Backend API**: http://3.89.127.102:8000
- **API Docs**: http://3.89.127.102:8000/docs

---

**Need Help?** Check the main README.md or create an issue on GitHub!

