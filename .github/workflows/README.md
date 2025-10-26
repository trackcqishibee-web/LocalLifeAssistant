# 🚀 Deployment Workflow Configuration

## Required GitHub Secrets

Configure these secrets in: **Settings** → **Secrets and variables** → **Actions** → **Secrets**

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SSH_PRIVATE_KEY` | Your EC2 SSH private key | Contents of `locomock_key.pem` |
| `SERVER_IP` | EC2 instance IP address | `3.89.127.102` |
| `SSH_USER` | SSH username | `ubuntu` |
| `DOMAIN_NAME` | Your domain name | `jeff.locomoco.top` |
| `DEPLOY_GITHUB_BRANCH` | Branch to deploy from | `main` or `feature/aws-ec2-deployment` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase credentials | `{ "type": "service_account", ... }` |
| `ADMIN_EMAIL` | Email for SSL certificates | `admin@example.com` |

## Workflow Triggers

- **Automatic**: Pushes to `main` branch
- **Manual**: Click "Run workflow" in Actions tab

## What It Does

1. 🔧 Configures SSH connection to EC2
2. 📥 Downloads latest deployment scripts
3. 🔐 Sets up Firebase credentials
4. 🚀 Deploys application
5. 🔍 Runs health checks
6. 📊 Shows deployment summary

## Deployment Steps

```bash
# Just push to main branch
git push origin main

# Or trigger manually from GitHub Actions UI
```

## Health Checks

The workflow automatically verifies:
- ✅ Backend service is running
- ✅ Nginx service is running  
- ✅ Backend health endpoint responds

If any check fails, the deployment will be rolled back.

