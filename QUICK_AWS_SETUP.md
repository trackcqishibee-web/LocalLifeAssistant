# ⚡ Quick AWS EC2 Setup Guide

## 🎯 Your EC2 Instance
- **IP Address**: `3.89.127.102`
- **SSH Command**: `ssh -i "locomock_key.pem" ubuntu@3.89.127.102`
- **Region**: us-east-1

---

## 🚀 3-Step Setup

### Step 1: Add GitHub Secrets (5 minutes)

Go to your GitHub repository:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these secrets:

| Secret Name | What to put | Where to find it |
|------------|-------------|------------------|
| `SSH_PRIVATE_KEY` | Contents of `locomock_key.pem` file | Located at `~/.ssh/locomock_key.pem` |
| `OPENAI_API_KEY` | Already have it! | Use the one we just added to .env |

**How to get SSH key contents:**
```bash
cat locomock_key.pem
# Copy everything including -----BEGIN RSA PRIVATE KEY----- and -----END RSA PRIVATE KEY-----
```

---

### Step 2: One-Time EC2 Setup (10 minutes)

Connect to your EC2 instance:
```bash
ssh -i "locomock_key.pem" ubuntu@3.89.127.102
```

Run these commands once:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose
sudo apt install -y docker-compose

# Install other tools
sudo apt install -y python3 python3-pip nodejs npm nginx git

# Create app directory
sudo mkdir -p /opt/locallifeassistant
sudo chown ubuntu:ubuntu /opt/locallifeassistant

# Configure firewall
sudo ufw allow 22     # SSH
sudo ufw allow 80     # HTTP
sudo ufw allow 443    # HTTPS
sudo ufw allow 8000   # Backend
sudo ufw --force enable

echo "✅ EC2 setup complete!"
```

---

### Step 3: Deploy! (Automatic)

Just push your code to GitHub:
```bash
git add .
git commit -m "Deploy to AWS"
git push origin main
```

GitHub Actions will automatically:
- ✅ Connect to your EC2
- ✅ Pull latest code
- ✅ Install dependencies
- ✅ Start services
- ✅ Run health checks

Check deployment status:
- Go to your GitHub repo → **Actions** tab
- Watch the deployment progress

---

## 🌐 Access Your App

Once deployed:
- **Frontend**: http://3.89.127.102
- **Backend API**: http://3.89.127.102:8000
- **API Docs**: http://3.89.127.102:8000/docs

---

## 🔍 Quick Health Check

```bash
# Check if backend is running
curl http://3.89.127.102:8000/health

# Should return:
# {"status":"healthy","version":"2.1.0","features":["smart_caching","real_time_events","city_based_cache"]}
```

---

## ⚠️ Important: AWS Security Group

Make sure your EC2 security group allows these ports:

| Type | Port | Source | Why |
|------|------|--------|-----|
| SSH | 22 | Your IP | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Frontend |
| HTTPS | 443 | 0.0.0.0/0 | SSL (if configured) |
| Custom TCP | 8000 | 0.0.0.0/0 | Backend API |

**How to check:**
1. AWS Console → EC2 → Instances
2. Click your instance
3. Security tab → Click security group link
4. Inbound rules → Edit if needed

---

## 🐛 Troubleshooting

### Can't SSH to EC2?
```bash
# Check key permissions
chmod 400 locomock_key.pem

# Try verbose mode
ssh -v -i "locomock_key.pem" ubuntu@3.89.127.102
```

### GitHub Actions fails?
- Check that `AWS_EC2_SSH_KEY` secret is set correctly
- Make sure EC2 security group allows SSH from anywhere (or GitHub's IPs)
- Check Actions logs for specific error

### App not loading?
```bash
# SSH to EC2 and check
ssh -i "locomock_key.pem" ubuntu@3.89.127.102

# Check if services are running
sudo systemctl status locallifeassistant-backend
sudo systemctl status nginx

# Check logs
journalctl -u locallifeassistant-backend -f
```

---

## 📚 Full Documentation

- **Complete Guide**: See `AWS_DEPLOYMENT_GUIDE.md`
- **Workflow File**: `.github/workflows/deploy-aws-ec2.yml`
- **Local Setup**: See `SETUP_COMPLETE.md`

---

## 🎉 That's It!

Your deployment is set up! Every time you push to `main`, it will automatically deploy to AWS.

**Next Steps:**
1. Set up a custom domain (optional)
2. Install SSL certificate
3. Configure monitoring

Need help? Check the full `AWS_DEPLOYMENT_GUIDE.md` or reach out!

